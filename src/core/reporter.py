import smtplib
import os
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
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f7f9; color: #333; }}
        .header {{ background: linear-gradient(135deg, #1e4eb8 0%, #3b82f6 100%); color: white; padding: 40px 20px; text-align: left; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 10px 0 5px 0; font-size: 28px; font-weight: bold; }}
        .header p {{ margin: 0; font-size: 14px; opacity: 0.9; }}
        .header .sub {{ font-size: 12px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8; }}
        .content {{ padding: 30px; max-width: 900px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-top: -20px; }}
        .intro-text {{ color: #666; font-size: 14px; line-height: 1.6; margin-bottom: 25px; }}
        
        .cards {{ display: flex; justify-content: space-between; gap: 15px; margin-bottom: 30px; }}
        .card {{ flex: 1; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.03); }}
        .card .val {{ font-size: 24px; font-weight: bold; display: block; margin-bottom: 5px; }}
        .card .lab {{ font-size: 10px; font-weight: bold; text-transform: uppercase; color: #888; letter-spacing: 0.5px; }}
        
        .card-blue {{ background-color: #eff6ff; border: 1px solid #dbeafe; color: #1e40af; }}
        .card-green {{ background-color: #f0fdf4; border: 1px solid #dcfce7; color: #166534; }}
        .card-red {{ background-color: #fef2f2; border: 1px solid #fee2e2; color: #991b1b; }}
        .card-teal {{ background-color: #f0fdfa; border: 1px solid #ccfbf1; color: #115e59; }}
        .card-orange {{ background-color: #fffbeb; border: 1px solid #fef3c7; color: #92400e; }}
        
        .section-title {{ font-size: 18px; font-weight: bold; margin: 30px 0 15px 0; display: flex; align-items: center; color: #111; }}
        .section-title span {{ margin-right: 10px; }}
        
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th {{ background-color: #f8fafc; color: #64748b; font-size: 11px; text-transform: uppercase; text-align: left; padding: 12px 15px; border-bottom: 1px solid #e2e8f0; }}
        td {{ padding: 12px 15px; font-size: 14px; border-bottom: 1px solid #f1f5f9; }}
        .metric-row:hover {{ background-color: #f8fafc; }}
        .metric-name {{ color: #475569; }}
        .metric-val {{ text-align: right; font-weight: 600; color: #1e293b; }}
        
        .failed-header {{ color: #dc2626; font-size: 16px; font-weight: bold; margin-bottom: 15px; }}
        .failed-table th {{ background-color: #fef2f2; color: #991b1b; }}
        .failed-table td {{ vertical-align: top; }}
        .error-text {{ color: #dc2626; font-size: 12px; line-height: 1.4; }}
        
        .footer {{ text-align: center; padding: 30px; font-size: 12px; color: #94a3b8; line-height: 1.8; }}
        .footer .run-it {{ font-family: monospace; color: #cbd5e1; margin-top: 10px; display: block; }}
    </style>
</head>
<body>
    <div style="max-width: 900px; margin: 20px auto;">
        <div class="header">
            <div class="sub">WHITEBOX LEARNING</div>
            <h1>Raw Positions Auto Apply Report</h1>
            <p>Run completed on {date_str} at {time_str}</p>
        </div>
        
        <div class="content">
            <p class="intro-text">
                This report summarises the email application run that processed all active candidates. 
                The run completed in the expected window with the following overall metrics.
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
                    <span class="lab">INSERTED (NEW)</span>
                </div>
            </div>
            
            <div class="section-title">
                <span>📊</span> Run Overview
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th style="width: 70%;">METRIC</th>
                        <th style="text-align: right;">VALUE</th>
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
                        <td class="metric-name">Success Rate</td>
                        <td class="metric-val" style="color: #2563eb;">{success_rate:.0f}%</td>
                    </tr>
                </tbody>
            </table>
"""

            # Add Candidate Breakdown Section
            html += f"""
            <div class="section-title">
                <span>👤</span> Candidate Profile Breakdown
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th style="width: 20%;">CANDIDATE</th>
                        <th style="width: 25%;">EMAIL</th>
                        <th style="text-align: center;">JOBS APPLIED (SENT)</th>
                        <th style="text-align: center;">FAILED</th>
                        <th style="text-align: center;">SKIPPED</th>
                        <th style="text-align: right;">TOTAL PROCESSED</th>
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
                        <td class="metric-name">{name}</td>
                        <td style="font-size: 13px; color: #64748b;"><a href="mailto:{user_email}" style="color: #3b82f6; text-decoration: none;">{user_email}</a></td>
                        <td style="text-align: center; color: #16a34a; font-weight: 600;">{sent}</td>
                        <td style="text-align: center; color: #dc2626;">{failed}</td>
                        <td style="text-align: center; color: #f59e0b;">{skipped}</td>
                        <td class="metric-val">{processed}</td>
                    </tr>
"""
            
            # Add Total Row
            html += f"""
                    <tr style="background-color: #f8fafc; font-weight: bold; border-top: 2px solid #e2e8f0;">
                        <td class="metric-name" style="color: #111;">TOTAL</td>
                        <td style="color: #64748b; font-size: 11px;">-</td>
                        <td style="text-align: center; color: #16a34a;">{grand_total_sent}</td>
                        <td style="text-align: center; color: #dc2626;">{grand_total_failed}</td>
                        <td style="text-align: center; color: #f59e0b;">{grand_total_skipped}</td>
                        <td class="metric-val" style="color: #111;">{grand_total_processed}</td>
                    </tr>
                </tbody>
            </table>
"""

            # Add Detailed Results Section (Success Details)
            success_details = []
            for run in self.consolidated_data:
                user_name = run.get('user_name', 'Unknown')
                results = run.get('results', [])
                
                # Collect details for successful sends: Company (Email)
                successful_entries = []
                for r in results:
                    if r.get('sent_status') == 'success':
                        company = r.get('Company') or r.get('Title') or 'Unknown Position'
                        email = r.get('email') or 'Unknown Email'
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
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 30px;">
"""
                for detail in success_details:
                    html += f"""
                <div style="margin-bottom: 20px;">
                    <div style="color: #1e40af; font-size: 14px; font-weight: bold; border-bottom: 1px solid #dbeafe; padding-bottom: 5px; margin-bottom: 10px;">
                        {detail['name']}
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr; gap: 8px;">
"""
                    for entry in detail['entries']:
                        html += f"""
                        <div style="font-size: 12px; color: #475569; display: flex; align-items: center;">
                            <span style="color: #16a34a; margin-right: 8px;">•</span>
                            <strong style="color: #334155;">{entry['display']}</strong>
                            <span style="margin: 0 8px; color: #cbd5e1;">|</span>
                            <a href="mailto:{entry['email']}" style="color: #3b82f6; text-decoration: none;">{entry['email']}</a>
                        </div>
"""
                    html += "                    </div>\n                </div>"
                html += "            </div>"

            # Add Failed Candidates Section if any
            if failed_candidates_list:
                html += f"""
            <div class="failed-header">
                ❌ Failed Candidates ({len(failed_candidates_list)})
            </div>
            
            <table class="failed-table">
                <thead>
                    <tr>
                        <th style="width: 25%;">NAME</th>
                        <th style="width: 30%;">EMAIL</th>
                        <th>ERROR / CAUSE</th>
                    </tr>
                </thead>
                <tbody>
"""
                for fc in failed_candidates_list:
                    html += f"""
                    <tr>
                        <td>{fc['name']}</td>
                        <td><a href="mailto:{fc['email']}" style="color: #3b82f6; text-decoration: none;">{fc['email']}</a></td>
                        <td class="error-text">{fc['error']}</td>
                    </tr>
"""
                html += """
                </tbody>
            </table>
"""

            html += f"""
        </div>
        
        <div class="footer">
            This is an automated report generated by the WBL Email Extraction System.<br>
            <span class="run-it">Run ID: {self.run_id}</span>
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
        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
            return None, None
