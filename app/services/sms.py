import logging

logger = logging.getLogger(__name__)


async def send_otp(phone: str, otp: str) -> None:

    print("phone", phone)
    print("otp", otp)
    logger.info(
        "DEV OTP for %s: %s",
        phone,
        otp,
    )
