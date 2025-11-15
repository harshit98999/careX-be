import random
import os
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags
from email.mime.image import MIMEImage # Import for attaching images

def generate_otp(length=6):
    """
    Generates a random OTP of a specified length.
    """
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])

def send_otp_email(email, otp, purpose="account verification"):
    """
    Sends a professional HTML email with an embedded logo and OTP.
    This version defines the HTML content directly within the function.
    """
    # 1. Determine the subject and introductory text based on the purpose
    if purpose == "login":
        subject = 'Your CareX Security Code'
        introductory_text = 'To securely access your CareX account, please use the following one-time password (OTP). This code is a safeguard to protect your information.'
    else:  # Default to account verification
        subject = 'Complete Your CareX Registration'
        introductory_text = 'Welcome to CareX. To finalize your account setup and ensure its security, please use the following one-time password (OTP) to verify your email address.'

    # Define a unique Content-ID for the logo. This will link the attachment to the <img> tag.
    logo_cid = 'carex_logo_cid'

    # 2. Define the HTML content for the email as a multi-line f-string
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CareX Verification</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';
                background-color: #f4f7f6; margin: 0; padding: 0;
            }}
            .container {{
                max-width: 600px; margin: 20px auto; background-color: #ffffff;
                border-radius: 8px; overflow: hidden; border: 1px solid #e0e0e0;
            }}
            .header {{
                background-color: #007bff;
                padding: 15px 20px;
                display: flex;
                align-items: center;
            }}
            .header img {{
                max-width: 32px; /* <-- UPDATED: Logo size reduced */
                max-height: 32px;
                margin-right: 15px;
            }}
            .header .brand-name {{
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
            }}
            .content {{
                padding: 30px; color: #333333; line-height: 1.6;
            }}
            .otp-code {{
                font-size: 28px; font-weight: bold; color: #007bff; text-align: center;
                margin: 25px 0; letter-spacing: 5px; padding: 15px;
                background-color: #f2f2f2; border-radius: 5px;
            }}
            .footer {{
                text-align: center; padding: 20px; font-size: 12px;
                color: #888888; background-color: #f9f9f9;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="cid:{logo_cid}" alt="CareX Logo">
                <span class="brand-name">CareX</span>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>{introductory_text}</p>
                <div class="otp-code">{otp}</div>
                <p>This code is valid for <strong>{settings.OTP_EXPIRY_MINUTES} minutes</strong> and is required to proceed.</p>
                <p>If you did not request this code, you can safely ignore this email. No changes have been made to your account.</p>
                <p>Best regards,<br>The CareX Team</p>
            </div>
            <div class="footer">
                <p>&copy; 2025 CareX. All rights reserved.</p>
                <p>This is an automated security notification. Please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # 3. Create a plain-text fallback for email clients that do not support HTML
    text_content = strip_tags(html_content)

    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]

    try:
        # 4. Create an EmailMultiAlternatives object to handle both HTML and plain text
        msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
        msg.attach_alternative(html_content, "text/html")

        # 5. Attach the logo image for embedding
        logo_path = os.path.join(settings.BASE_DIR, 'static/images/logo.png')

        with open(logo_path, 'rb') as f:
            # Create a MIMEImage object, explicitly defining the subtype to prevent errors
            logo_mime = MIMEImage(f.read(), _subtype='png')
            # Add the Content-ID header. The angle brackets are crucial.
            logo_mime.add_header('Content-ID', f'<{logo_cid}>')
            # Attach the MIMEImage object to the email message
            msg.attach(logo_mime)

        # 6. Send the final email
        msg.send()
        return True
    except FileNotFoundError:
        print(f"Error: Logo file not found at {logo_path}")
        return False
    except Exception as e:
        # Log any other errors that occur during email sending
        print(f"Error sending professional OTP email: {e}")
        return False