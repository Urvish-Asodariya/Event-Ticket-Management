import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from .config import get_settings
import asyncio
from datetime import datetime

settings = get_settings()

class NotificationService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send email using SMTP
        """
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.from_email
            message['To'] = to_email

            # Add text content if provided
            if text_content:
                message.attach(MIMEText(text_content, 'plain'))
            
            # Add HTML content
            message.attach(MIMEText(html_content, 'html'))

            # Use asyncio to run SMTP operations in a thread pool
            return await asyncio.get_event_loop().run_in_executor(
                None, self._send_smtp_email, message
            )
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False

    def _send_smtp_email(self, message: MIMEMultipart) -> bool:
        """
        Helper method to send email via SMTP
        """
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
            return True
        except Exception as e:
            print(f"SMTP Error: {str(e)}")
            return False

    async def send_booking_confirmation(
        self,
        email: str,
        booking_details: dict
    ) -> bool:
        """
        Send booking confirmation email
        """
        subject = "Navratri Pass Booking Confirmation"
        html_content = f"""
        <html>
            <body>
                <h2>Booking Confirmation</h2>
                <p>Thank you for booking your Navratri Pass!</p>
                <h3>Booking Details:</h3>
                <ul>
                    <li>Booking ID: {booking_details.get('id')}</li>
                    <li>Pass Type: {booking_details.get('pass_type')}</li>
                    <li>Amount Paid: ₹{booking_details.get('amount_paid')}</li>
                    <li>Valid for: {booking_details.get('validity_period')}</li>
                </ul>
                <p>Please keep your QR code handy for entry.</p>
            </body>
        </html>
        """
        return await self.send_email(email, subject, html_content)

    async def send_pass_reminder(
        self,
        email: str,
        pass_details: dict
    ) -> bool:
        """
        Send reminder email before pass expiry
        """
        subject = "Your Navratri Pass - Reminder"
        html_content = f"""
        <html>
            <body>
                <h2>Navratri Pass Reminder</h2>
                <p>This is a reminder about your Navratri Pass:</p>
                <ul>
                    <li>Pass ID: {pass_details.get('id')}</li>
                    <li>Valid until: {pass_details.get('validity_end')}</li>
                </ul>
                <p>Don't forget to use your pass before it expires!</p>
            </body>
        </html>
        """
        return await self.send_email(email, subject, html_content)

    async def send_bulk_notification(
        self,
        emails: List[str],
        subject: str,
        message: str
    ) -> dict:
        """
        Send bulk notifications (e.g., for offers)
        """
        results = {
            "success": 0,
            "failed": 0,
            "failed_emails": []
        }

        for email in emails:
            success = await self.send_email(email, subject, message)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["failed_emails"].append(email)

        return results
