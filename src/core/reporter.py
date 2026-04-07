import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SmartApplyReporter:
    """Handles email reporting for SmartApply-dev runs."""
    def __init__(self, consolidated_data):
        self.consolidated_data = consolidated_data
        
        # Pull SMTP from .env using Gmail account used to send applications
        self.email_from = os.getenv("GMAIL_ADDRESS")
        self.password = os.getenv("GMAIL_APP_PASSWORD")
        self.server = "smtp.gmail.com"
        self.port = 587
        
        # Recipients for the report
        email_to_raw = os.getenv("REPORT_EMAIL_TO")
        if email_to_raw:
            self.email_to = [email.strip() for email in email_to_raw.split(',') if email.strip()]
        else:
            self.email_to = []

    def _is_configured(self):
        config_values = {
            "GMAIL_ADDRESS": self.email_from,
            "GMAIL_APP_PASSWORD": "set" if self.password else None,
            "REPORT_EMAIL_TO": self.email_to
        }
        missing = [k for k, v in config_values.items() if not v]
        if missing:
            logger.info(f"Reporting configuration missing: {', '.join(missing)} - Email Reporting will be skipped.")
            return False
        return True

    def send_report(self):
        try:
            if not self.consolidated_data:
                logger.warning("No runs data to report.")
                return False

            subject, html_body = self._generate_html_report()
            
            if not subject or not html_body:
                return False
            
            return self._send_email(subject, html_body)
        except Exception as e:
            logger.error(f"Failed to send run report: {e}", exc_info=True)
            return False

    def _send_email(self, subject, html_body):
        if not self._is_configured():
            logger.info("SMTP not properly configured. Skipping report.")
            return True
            
        msg = MIMEMultipart()
        # Set explicitly the display name so that emails don't visually group under a single account sender name in Gmail UI
        msg['From'] = f"SmartApply System <{self.email_from}>"
        msg['To'] = ', '.join(self.email_to)
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))
        
        try:
            with smtplib.SMTP(self.server, self.port) as server:
                server.starttls()
                server.login(self.email_from, self.password)
                server.sendmail(self.email_from, self.email_to, msg.as_string())
            logger.info(f"Consolidated run report sent successfully to {len(self.email_to)} recipient(s).")
            return True
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return False

    def _generate_html_report(self):
        try:
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #f9fafb; color: #111827; padding: 20px;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #3b82f6; padding-bottom: 10px;">SmartApply Consolidated Report</h2>
                <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            """
            
            total_processed = 0
            total_sent = 0
            total_skipped = 0
            total_failed = 0
            
            for run in self.consolidated_data:
                results = run.get('results', [])
                stats = run.get('stats', {})
                total_processed += len(results)
                total_sent += stats.get('sent', 0)
                total_skipped += stats.get('skipped', 0)
                total_failed += stats.get('failed', 0)
                
            success_rate = (total_sent / total_processed * 100) if total_processed else 0
            
            html_body += f"""
                <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 30px;">
                    <h3 style="color: #1e3a8a; margin-top: 0;">Overall Run Summary</h3>
                    <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
                        <tr>
                            <th style="padding: 10px; border: 1px solid #e5e7eb; text-align: left;">Total Processed</th>
                            <td style="padding: 10px; border: 1px solid #e5e7eb;">{total_processed}</td>
                        </tr>
                        <tr style="background-color: #f8f9fa;">
                            <th style="padding: 10px; border: 1px solid #e5e7eb; text-align: left; color: #10b981;">Successfully Sent</th>
                            <td style="padding: 10px; border: 1px solid #e5e7eb; font-weight: bold;">{total_sent}</td>
                        </tr>
                        <tr>
                            <th style="padding: 10px; border: 1px solid #e5e7eb; text-align: left; color: #f59e0b;">Skipped / Validation Failed</th>
                            <td style="padding: 10px; border: 1px solid #e5e7eb;">{total_skipped}</td>
                        </tr>
                        <tr style="background-color: #f8f9fa;">
                            <th style="padding: 10px; border: 1px solid #e5e7eb; text-align: left; color: #ef4444;">Errors / Failed</th>
                            <td style="padding: 10px; border: 1px solid #e5e7eb;">{total_failed}</td>
                        </tr>
                        <tr>
                            <th style="padding: 10px; border: 1px solid #e5e7eb; text-align: left;">Success Rate</th>
                            <td style="padding: 10px; border: 1px solid #e5e7eb;">{success_rate:.1f}%</td>
                        </tr>
                    </table>
                </div>
            """
            
            for run in self.consolidated_data:
                user_name = run.get('user_name', 'Unknown User')
                stats = run.get('stats', {})
                results = run.get('results', [])
                
                run_success_rate = (stats.get('sent', 0) / len(results) * 100) if results else 0
                
                html_body += f"""
                <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px;">
                    <h3 style="color: #2c3e50; margin-top: 0;">Profile: {user_name}</h3>
                    
                    <div style="display: flex; gap: 20px; font-size: 0.95em; color: #4b5563; margin-bottom: 15px;">
                        <span><strong>Processed:</strong> {len(results)}</span>
                        <span><strong style="color: #10b981;">Sent:</strong> {stats.get('sent', 0)}</span>
                        <span><strong style="color: #f59e0b;">Skipped:</strong> {stats.get('skipped', 0)}</span>
                    </div>
                """
                
                if results:
                    summary_rows = ""
                    for r in results:
                        status = r.get("sent_status", "unknown")
                        color = "#10b981" if status == "success" else "#f59e0b" if status in ["skipped", "user_skipped"] else "#ef4444"
                        email = r.get("Contact Info", "") or r.get("contact_email", "") or "Unknown"
                        
                        summary_rows += f"""
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style='padding: 8px; border: 1px solid #e5e7eb;'>{r.get('Company', 'N/A')}</td>
                            <td style='padding: 8px; border: 1px solid #e5e7eb;'>{email}</td>
                            <td style='padding: 8px; border: 1px solid #e5e7eb;'><span style="color: {color}; font-weight: bold;">{status.upper()}</span></td>
                            <td style='padding: 8px; border: 1px solid #e5e7eb; font-size: 0.9em; color: #6b7280;'>{r.get('error', '')}</td>
                        </tr>
                        """
                        
                    html_body += f"""
                    <table style="border-collapse: collapse; width: 100%; font-size: 0.95em;">
                        <tr style="background-color: #f3f4f6; color: #374151;">
                            <th style="padding: 10px; border: 1px solid #e5e7eb; text-align: left;">Company</th>
                            <th style="padding: 10px; border: 1px solid #e5e7eb; text-align: left;">Email</th>
                            <th style="padding: 10px; border: 1px solid #e5e7eb; text-align: left;">Status</th>
                            <th style="padding: 10px; border: 1px solid #e5e7eb; text-align: left;">Details</th>
                        </tr>
                        {summary_rows}
                    </table>
                    """
                else:
                    html_body += "<p style='color: #6b7280; font-style: italic;'>No jobs processed for this profile.</p>"
                    
                html_body += "</div>"

            html_body += """
                <p style="margin-top: 40px; font-size: 0.85em; color: #9ca3af; text-align: center;">
                    <em>This is an automated consolidated report from SmartApply.</em>
                </p>
            </body>
            </html>
            """
            
            subject = f"SmartApply Consolidated Report - {datetime.now().strftime('%Y-%m-%d')}"
            return subject, html_body
        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
            return None, None
