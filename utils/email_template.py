def otp_email_template(otp: str):
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>ACCESSLearn OTP Verification</h2>
            <p>Your verification code is:</p>
            <div style="font-size: 28px; font-weight: bold; letter-spacing: 6px;">
                {otp}
            </div>
            <p>This code will expire in 5 minutes.</p>
        </body>
    </html>
    """