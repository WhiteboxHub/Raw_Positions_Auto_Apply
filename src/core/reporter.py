import smtplib
import os
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.policy import SMTP
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RawPositionsAutoApplyReporter:
    """Handles email reporting for Raw_Positions_Auto_Apply runs."""
    def __init__(self, consolidated_data, run_id=None):
        self.consolidated_data = consolidated_data
        self.run_id = run_id or "N/A"
        
        # Pull SMTP from .env using Gmail account used to send applications
        self.email_from = os.getenv("GMAIL_ADDRESS")
        self.password = os.getenv("GMAIL_APP_PASSWORD")
        self.server = "smtp.gmail.com"
        self.port = 587
        
        # Recipients for the report
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
            logger.debug("Reloaded environment variables for reporting.")
        except ImportError:
            pass

        email_to_raw = os.getenv("REPORT_EMAIL_TO")
        if email_to_raw:
            # Handle comma separated list and trailing comments
            clean_emails = email_to_raw.split('#')[0].strip()
            self.email_to = [email.strip() for email in clean_emails.split(',') if email.strip()]
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
        # Set explicitly the display name
        msg['From'] = f"Raw_Positions_Auto_Apply System <{self.email_from}>"
        msg['To'] = ', '.join(self.email_to)
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))
        
        try:
            with smtplib.SMTP(self.server, self.port) as server:
                server.starttls()
                server.login(self.email_from, self.password)
                server.sendmail(self.email_from, self.email_to, msg.as_string(policy=SMTP))
            logger.info(f"Consolidated run report sent successfully to {len(self.email_to)} recipient(s).")
            return True
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return False

    def _generate_html_report(self):
        try:
            now = datetime.now()
            date_str = now.strftime('%B %d, %Y')
            time_str = now.strftime('%I:%M %p')
            
            # Aggregate stats
            total_candidates = len(self.consolidated_data)
            total_extracted = 0
            total_inserted = 0
            successful_candidates_count = 0
            failed_candidates_count = 0
            failed_candidates_list = []
            
            for run in self.consolidated_data:
                stats = run.get('stats', {})
                results = run.get('results', [])
                user_name = run.get('user_name', 'Unknown')
                user_email = run.get('user_email', 'Unknown')
                
                sends = stats.get('sent', 0)
                fails = stats.get('failed', 0)
                
                total_extracted += len(results)
                total_inserted += sends
                
                # A candidate is "failed" if they have 0 successful sends and at least one fail, 
                # or if the errors indicate a fatal setup issue.
                if sends == 0 and (fails > 0 or not results):
                    failed_candidates_count += 1
                    error_msg = stats.get('errors', [{}])[0].get('reason', 'Unknown initialization error') if stats.get('errors') else "No jobs matched or authentication failed"
                    failed_candidates_list.append({
                        "name": user_name,
                        "email": user_email,
                        "error": error_msg
                    })
                else:
                    successful_candidates_count += 1

            success_rate = (successful_candidates_count / total_candidates * 100) if total_candidates else 0
            
            # Start building HTML
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 40px 20px; }}
        .container {{ max-width: 950px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); overflow: hidden; }}
        
        .header {{ background-color: #1f2937; color: #ffffff; padding: 40px 30px; text-align: center; border-bottom: 1px solid #374151; }}
        .header .sub {{ font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; color: #9ca3af; margin-bottom: 8px; }}
        .header h1 {{ margin: 0; font-size: 28px; font-weight: 600; letter-spacing: -0.5px; }}
        .header p {{ margin: 10px 0 0 0; font-size: 14px; color: #9ca3af; }}
        
        .content {{ padding: 35px; }}
        .intro-text {{ color: #4b5563; font-size: 15px; line-height: 1.6; margin-bottom: 35px; text-align: center; max-width: 700px; margin-left: auto; margin-right: auto; }}
        
        .cards {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 15px; margin-bottom: 40px; }}
        .card {{ flex: 1; min-width: 150px; padding: 25px 15px; border-radius: 12px; text-align: center; background-color: #f9fafb; border: 1px solid #e5e7eb; transition: all 0.2s ease; }}
        .card .val {{ font-size: 32px; font-weight: 800; display: block; margin-bottom: 6px; letter-spacing: -1px; }}
        .card .lab {{ font-size: 11px; font-weight: 700; text-transform: uppercase; color: #6b7280; letter-spacing: 1px; }}
        
        .card-blue {{ border-top: 4px solid #3b82f6; }}
        .card-blue .val {{ color: #2563eb; }}
        .card-green {{ border-top: 4px solid #10b981; }}
        .card-green .val {{ color: #059669; }}
        .card-red {{ border-top: 4px solid #ef4444; }}
        .card-red .val {{ color: #dc2626; }}
        .card-teal {{ border-top: 4px solid #0d9488; }}
        .card-teal .val {{ color: #0f766e; }}
        .card-orange {{ border-top: 4px solid #f59e0b; }}
        .card-orange .val {{ color: #d97706; }}
        
        .section-title {{ font-size: 18px; font-weight: 700; margin: 40px 0 20px 0; display: flex; align-items: center; color: #111827; border-bottom: 2px solid #f3f4f6; padding-bottom: 10px; }}
        .section-title span {{ margin-right: 12px; font-size: 20px; }}
        
        .table-container {{ border-radius: 12px; border: 1px solid #e5e7eb; overflow: hidden; margin-bottom: 30px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background-color: #f9fafb; color: #374151; font-size: 12px; text-transform: uppercase; font-weight: 700; text-align: left; padding: 15px 20px; border-bottom: 1px solid #e5e7eb; }}
        td {{ padding: 15px 20px; font-size: 14px; border-bottom: 1px solid #f3f4f6; color: #4b5563; }}
        tr:last-child td {{ border-bottom: none; }}
        
        .metric-row:hover {{ background-color: #f9fafb; }}
        .metric-name {{ color: #374151; font-weight: 600; }}
        .metric-val {{ text-align: right; font-weight: 700; color: #111827; }}
        
        .failed-header {{ color: #dc2626; font-size: 18px; font-weight: 700; margin: 40px 0 20px 0; }}
        .failed-table th {{ background-color: #fff1f2; color: #991b1b; }}
        .error-text {{ color: #dc2626; font-size: 13px; line-height: 1.5; font-weight: 500; }}
        
        .contact-group {{ background-color: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 25px; margin-bottom: 30px; }}
        .contact-name {{ color: #1e40af; font-size: 15px; font-weight: 700; border-bottom: 1px solid #dbeafe; padding-bottom: 8px; margin-bottom: 15px; }}
        .contact-grid {{ display: grid; grid-template-columns: 1fr; gap: 10px; }}
        .contact-item {{ font-size: 13px; display: flex; align-items: center; }}
        .contact-item .bullet {{ color: #10b981; margin-right: 10px; font-size: 16px; }}
        
        .footer {{ text-align: center; padding: 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 13px; }}
        .footer .run-it {{ font-family: 'JetBrains Mono', 'Courier New', monospace; font-size: 11px; color: #9ca3af; margin-top: 12px; display: block; }}
        
        a {{ color: #3b82f6; text-decoration: none; font-weight: 500; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="sub">WHITEBOX LEARNING</div>
            <h1>Raw Positions Auto Apply Report</h1>
            <p>Run completed on <strong>{date_str}</strong> at <strong>{time_str}</strong></p>
        </div>
        
        <div class="content">
            <p class="intro-text">
                This report summarizes the email application run that processed all active candidates. 
                The automation completed successfully with the following performance metrics.
            </p>
            
            <div class="cards">
                <div class="card card-blue">
                    <span class="val">{total_candidates}</span>
                    <span class="lab">CANDIDATES</span>
                </div>
                <div class="card card-green">
                    <span class="val">{successful_candidates_count}</span>
                    <span class="lab">SUCCESS</span>
                </div>
                <div class="card card-red">
                    <span class="val">{failed_candidates_count}</span>
                    <span class="lab">FAILED</span>
                </div>
                <div class="card card-teal">
                    <span class="val">{total_extracted}</span>
                    <span class="lab">EXTRACTED</span>
                </div>
                <div class="card card-orange">
                    <span class="val">{total_inserted}</span>
                    <span class="lab">INSERTED</span>
                </div>
            </div>
            
            <div class="section-title">
                <span>📊</span> Performance Overview
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 70%;">Metric</th>
                            <th style="text-align: right;">Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr class="metric-row">
                            <td class="metric-name">Total Candidates Processed</td>
                            <td class="metric-val">{total_candidates}</td>
                        </tr>
                        <tr class="metric-row">
                            <td class="metric-name">Successful Candidates</td>
                            <td class="metric-val" style="color: #16a34a;">{successful_candidates_count}</td>
                        </tr>
                        <tr class="metric-row">
                            <td class="metric-name">Failed Candidates</td>
                            <td class="metric-val" style="color: #dc2626;">{failed_candidates_count}</td>
                        </tr>
                        <tr class="metric-row">
                            <td class="metric-name">Contacts Extracted (Passed Filters)</td>
                            <td class="metric-val" style="color: #0d9488;">{total_extracted}</td>
                        </tr>
                        <tr class="metric-row">
                            <td class="metric-name">Contacts Inserted (New to DB)</td>
                            <td class="metric-val" style="color: #ea580c;">{total_inserted}</td>
                        </tr>
                        <tr class="metric-row">
                            <td class="metric-name">Overall Success Rate</td>
                            <td class="metric-val" style="color: #2563eb;">{success_rate:.0f}%</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="section-title">
                <span>👤</span> Candidate Profile Breakdown
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Candidate</th>
                            <th style="text-align: center;">Sent</th>
                            <th style="text-align: center;">Failed</th>
                            <th style="text-align: center;">Skipped</th>
                            <th style="text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            grand_total_sent = 0
            grand_total_failed = 0
            grand_total_skipped = 0
            grand_total_processed = 0

            for run in self.consolidated_data:
                name = run.get('user_name', 'Unknown')
                user_email = run.get('user_email', 'Unknown')
                stats = run.get('stats', {})
                results = run.get('results', [])
                
                sent = stats.get('sent', 0)
                failed = stats.get('failed', 0)
                skipped = stats.get('skipped', 0)
                processed = len(results)
                
                grand_total_sent += sent
                grand_total_failed += failed
                grand_total_skipped += skipped
                grand_total_processed += processed
                
                html += f"""
                        <tr class="metric-row">
                            <td>
                                <div class="metric-name">{name}</div>
                                <div style="font-size: 11px;"><a href="mailto:{user_email}">{user_email}</a></div>
                            </td>
                            <td style="text-align: center; color: #16a34a; font-weight: 700;">{sent}</td>
                            <td style="text-align: center; color: #dc2626;">{failed}</td>
                            <td style="text-align: center; color: #f59e0b;">{skipped}</td>
                            <td style="text-align: right; font-weight: 700; color: #111827;">{processed}</td>
                        </tr>
"""
            
            # Add Total Row
            html += f"""
                        <tr style="background-color: #f9fafb; font-weight: 800; border-top: 2px solid #e5e7eb;">
                            <td class="metric-name" style="color: #111827;">TOTAL SUM</td>
                            <td style="text-align: center; color: #16a34a;">{grand_total_sent}</td>
                            <td style="text-align: center; color: #dc2626;">{grand_total_failed}</td>
                            <td style="text-align: center; color: #f59e0b;">{grand_total_skipped}</td>
                            <td style="text-align: right; color: #111827;">{grand_total_processed}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
"""

            # Add Detailed Results Section (Success Details)
            success_details = []
            for run in self.consolidated_data:
                user_name = run.get('user_name', 'Unknown')
                results = run.get('results', [])
                
                successful_entries = []
                for r in results:
                    if r.get('sent_status') == 'success':
                        company = r.get('Company') or r.get('Title') or 'Unknown Position'
                        email_raw = (
                            r.get('email') or 
                            r.get('Contact Info') or 
                            r.get('Contact Information') or 
                            r.get('Recipient') or 
                            r.get('email_address') or 
                            'Unknown Email'
                        )
                        
                        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                        match = re.search(email_pattern, str(email_raw))
                        email = match.group(0).strip() if match else str(email_raw).strip()

                        successful_entries.append({
                            "display": company,
                            "email": email
                        })
                
                if successful_entries:
                    success_details.append({
                        "name": user_name,
                        "entries": successful_entries
                    })

            if success_details:
                html += f"""
            <div class="section-title">
                <span>✅</span> Successful Recruiter Contacts
            </div>
"""
                for detail in success_details:
                    html += f"""
            <div class="contact-group">
                <div class="contact-name">{detail['name']}</div>
                <div class="contact-grid">
"""
                    for entry in detail['entries']:
                        html += f"""
                    <div class="contact-item">
                        <span class="bullet">•</span>
                        <strong style="color: #334155; margin-right: 8px;">{entry['display']}</strong>
                        <span style="color: #cbd5e1; margin-right: 8px;">|</span>
                        <a href="mailto:{entry['email']}">{entry['email']}</a>
                    </div>
"""
                    html += "                </div>\n            </div>"

            # Add Failed Candidates Section if any
            if failed_candidates_list:
                html += f"""
            <div class="failed-header">
                ❌ Failed Candidates ({len(failed_candidates_list)})
            </div>
            
            <div class="table-container">
                <table class="failed-table">
                    <thead>
                        <tr>
                            <th>Name / Email</th>
                            <th>Error / Cause</th>
                        </tr>
                    </thead>
                    <tbody>
"""
                for fc in failed_candidates_list:
                    html += f"""
                        <tr>
                            <td>
                                <div class="metric-name">{fc['name']}</div>
                                <div style="font-size: 11px;"><a href="mailto:{fc['email']}">{fc['email']}</a></div>
                            </td>
                            <td class="error-text">{fc['error']}</td>
                        </tr>
"""
                html += """
                    </tbody>
                </table>
            </div>
"""

            html += f"""
        </div>
        
        <div class="footer">
            This is an automated report generated by the WBL Email Extraction System.<br>
            <span class="run-it">RUN ID: {self.run_id}</span>
        </div>
    </div>
</body>
</html>
"""
            subject = f"Raw Positions Auto Apply Report - {date_str}"
            return subject, html
        except Exception as e:
            logger.error(f"Error generating HTML report: {e}", exc_info=True)
            return None, None
