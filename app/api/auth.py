from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.db.session import get_db
from app.models.otp import OTP
from app.models.user import User, UserRole
from app.schemas.auth import (
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    AuthUserResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from app.services.otp import (
    generate_otp,
    get_otp_expiry,
    hash_otp,
    verify_otp,
)
from app.services.sms import send_otp

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/send-otp",
    response_model=SendOTPResponse,
)
async def send_otp_endpoint(
    request: SendOTPRequest,
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)

    # ---------------------------------------------------------
    # 1. Find the most recent OTP for this phone number
    # ---------------------------------------------------------
    result = await db.execute(
        select(OTP)
        .where(OTP.phone == request.phone)
        .order_by(OTP.created_at.desc())
        .limit(1)
    )

    latest_otp = result.scalar_one_or_none()

    # ---------------------------------------------------------
    # 2. 30-second resend cooldown
    # ---------------------------------------------------------
    if latest_otp is not None:
        cooldown_until = latest_otp.created_at + timedelta(
            seconds=settings.OTP_RESEND_COOLDOWN_SECONDS
        )

        if now < cooldown_until:
            remaining_seconds = int((cooldown_until - now).total_seconds())

            raise HTTPException(
                status_code=429,
                detail=(
                    f"Please wait {remaining_seconds} "
                    "seconds before requesting another OTP."
                ),
            )

    # ---------------------------------------------------------
    # 3. Maximum 5 OTP requests within 30 minutes
    # ---------------------------------------------------------
    window_start = now - timedelta(minutes=settings.OTP_SEND_WINDOW_MINUTES)

    count_result = await db.execute(
        select(func.count(OTP.id)).where(
            OTP.phone == request.phone,
            OTP.created_at >= window_start,
        )
    )

    send_count = count_result.scalar_one()

    if send_count >= settings.OTP_MAX_SENDS:
        raise HTTPException(
            status_code=429,
            detail=("Too many OTP requests. " "Please try again later."),
        )

    # ---------------------------------------------------------
    # 4. Generate OTP
    # ---------------------------------------------------------
    otp = generate_otp()

    otp_record = OTP(
        phone=request.phone,
        otp_hash=hash_otp(otp),
        expires_at=get_otp_expiry(),
        attempts=0,
        verified=False,
    )

    db.add(otp_record)

    await db.commit()

    # ---------------------------------------------------------
    # 5. Send OTP
    # ---------------------------------------------------------
    await send_otp(
        request.phone,
        otp,
    )

    return {
        "message": "OTP sent successfully",
    }


@router.post(
    "/verify-otp",
    response_model=VerifyOTPResponse,
)
async def verify_otp_endpoint(
    request: VerifyOTPRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OTP)
        .where(OTP.phone == request.phone)
        .order_by(OTP.created_at.desc())
        .limit(1)
    )

    otp_record = result.scalar_one_or_none()

    if otp_record is None:
        raise HTTPException(
            status_code=400,
            detail="OTP not found",
        )

    if otp_record.verified:
        raise HTTPException(
            status_code=400,
            detail="OTP already used",
        )

    now = datetime.now(timezone.utc)

    if now > otp_record.expires_at:
        raise HTTPException(
            status_code=400,
            detail="OTP expired",
        )

    if otp_record.attempts >= settings.OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=400,
            detail="Too many attempts. Please request a new OTP.",
        )

    if not verify_otp(
        request.otp,
        otp_record.otp_hash,
    ):
        otp_record.attempts += 1

        await db.commit()

        remaining_attempts = settings.OTP_MAX_ATTEMPTS - otp_record.attempts

        if remaining_attempts <= 0:
            raise HTTPException(
                status_code=400,
                detail="Too many attempts. Please request a new OTP.",
            )

        raise HTTPException(
            status_code=400,
            detail=(f"Invalid OTP. " f"{remaining_attempts} attempts remaining."),
        )

    # OTP is correct
    otp_record.verified = True

    result = await db.execute(select(User).where(User.phone == request.phone))

    user = result.scalar_one_or_none()

    is_new_user = user is None

    if user is None:
        user = User(
            phone=request.phone,
            role=request.role,
        )

        db.add(user)

    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # True in production with HTTPS
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # True in production with HTTPS
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )

    return VerifyOTPResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        is_new_user=is_new_user,
        user=AuthUserResponse(phone=user.phone, id=user.id, role=user.role),
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = decode_refresh_token(request.refresh_token)

    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
        )

    # Make sure the user still exists
    result = await db.execute(select(User).where(User.id == user_id))

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    # Create new tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return RefreshTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )
