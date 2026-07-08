from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from core.config import settings
from utils.email_template import otp_email_template

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,

    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,

    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_PORT=settings.MAIL_PORT,

    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,

    USE_CREDENTIALS=True
)

class EmailService:

    @staticmethod
    async def send_teacher_otp_email(email: str, otp: str):

        message = MessageSchema(
            subject="Your ACCESSLearn OTP code",

            recipients=[email],

            body=otp_email_template(otp),

            subtype="html"

        )

        fm = FastMail(conf)
        await fm.send_message(message)