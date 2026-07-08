import smtplib
import html
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from datetime import datetime

from .base import Distributor, Report
from utils.logger import setup_logger
from subscription_manager import get_verified_subscribers


class EmailDistributor(Distributor):
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger("EmailDistributor")
    
    @property
    def name(self) -> str:
        return "Email"
    
    def distribute(self, report: Report) -> bool:
        self.logger.info("开始发送邮件...")
        recipients = self._get_recipients()
        if not recipients:
            self.logger.warning("没有收件人，跳过邮件发送")
            return True

        success_count = 0
        for recipient in recipients:
            try:
                self._send_single(report, recipient)
                success_count += 1
                self.logger.info(f"邮件已发送至 {recipient}")
            except Exception as e:
                self.logger.error(f"发送至 {recipient} 失败: {str(e)}")

        self.logger.info(f"邮件发送完成: {success_count}/{len(recipients)} 成功")
        return success_count > 0

    def _get_recipients(self) -> list:
        """Get list of recipients: verified subscribers + configured receiver."""
        recipients = get_verified_subscribers()
        configured = self.config.get("receiver_email", "").strip()
        if configured and configured not in recipients:
            recipients.insert(0, configured)
        return recipients

    def _build_html_body(self, report: Report) -> str:
        """Build an HTML email body from the plain text report."""
        lines = report.content.split("\n")
        html_content = []
        html_content.append("""
        <!DOCTYPE html>
        <html><head><meta charset="UTF-8">
        <style>
            body { font-family: -apple-system, 'Segoe UI', Arial, sans-serif; max-width: 680px; margin: 0 auto; padding: 20px; color: #333; }
            .header { text-align: center; padding: 20px 0; border-bottom: 2px solid #00D4FF; margin-bottom: 24px; }
            .header h1 { color: #0A1628; margin: 0; font-size: 24px; }
            .header p { color: #666; margin: 8px 0 0; font-size: 14px; }
            .section { margin: 20px 0; padding: 16px; background: #f8f9fa; border-radius: 8px; }
            .section h2 { color: #0A1628; font-size: 16px; margin: 0 0 12px; border-left: 3px solid #00D4FF; padding-left: 10px; }
            .item { margin: 12px 0; padding: 12px; background: #fff; border-radius: 6px; border: 1px solid #eee; }
            .item-title { font-size: 15px; font-weight: 600; margin: 0 0 6px; }
            .item-title a { color: #0A1628; text-decoration: none; }
            .item-title a:hover { color: #00D4FF; }
            .item-meta { font-size: 12px; color: #888; margin: 4px 0; }
            .item-summary { font-size: 13px; color: #555; margin: 6px 0 0; line-height: 1.5; }
            .tag { display: inline-block; background: #e8f4ff; color: #0066cc; font-size: 11px; padding: 2px 8px; border-radius: 10px; margin: 2px; }
            .footer { text-align: center; padding: 20px; color: #999; font-size: 12px; border-top: 1px solid #eee; margin-top: 24px; }
            .trend-box { display: flex; gap: 16px; flex-wrap: wrap; }
            .trend-item { flex: 1; min-width: 120px; text-align: center; padding: 12px; background: #fff; border-radius: 8px; border: 1px solid #eee; }
            .trend-num { font-size: 24px; font-weight: 700; color: #00D4FF; }
            .trend-label { font-size: 12px; color: #888; }
        </style>
        </head><body>
        """)

        # Header
        html_content.append(f'<div class="header"><h1>AI前沿技术日报</h1><p>{report.date} · 共收录 {report.news_count} 条新闻</p></div>')

        in_trends = False
        current_category = None

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("【今日趋势分析】"):
                in_trends = True
                html_content.append('<div class="section"><h2>📊 今日趋势分析</h2>')
                continue

            if stripped.startswith("【今日要闻】"):
                if in_trends:
                    html_content.append("</div>")
                    in_trends = False
                html_content.append('<div class="section"><h2>📰 今日要闻</h2>')
                continue

            if stripped.startswith("📁"):
                # Close previous category
                if current_category:
                    html_content.append("</div>")
                current_category = stripped[2:].strip()
                html_content.append(f'<div class="category"><h3 style="color:#7C3AED;margin:16px 0 8px;font-size:14px;">📁 {html.escape(current_category)}</h3>')
                continue

            if in_trends and stripped.startswith("•"):
                html_content.append(f'<div style="padding:2px 0;font-size:13px;">{html.escape(stripped)}</div>')
                continue

            # News items
            if stripped and stripped[0].isdigit() and ". " in stripped[:5]:
                title = stripped.split(". ", 1)[1] if ". " in stripped else stripped
                has_tags = "[" in title and "]" in title
                title_text = title.split("[")[0].strip() if has_tags else title.strip()
                html_content.append(f'<div class="item"><div class="item-title"><a href="#" target="_blank">{html.escape(title_text)}</a></div>')
                continue

            if stripped.startswith("来源:"):
                source = stripped[3:].strip()
                html_content.append(f'<div class="item-meta">📌 {html.escape(source)}</div>')
                continue

            if stripped.startswith("摘要:"):
                summary = stripped[3:].strip()
                html_content.append(f'<div class="item-summary">{html.escape(summary)}</div>')
                continue

            if stripped.startswith("链接:"):
                link = stripped[3:].strip()
                html_content.append(f'<div class="item-meta"><a href="{html.escape(link)}" style="color:#00D4FF;">🔗 阅读原文</a></div>')
                html_content.append("</div>")
                continue

            if stripped.startswith("---") or stripped.startswith("=="):
                html_content.append('<hr style="border:none;border-top:1px solid #eee;margin:16px 0;">')
                continue

        if current_category:
            html_content.append("</div>")

        # Footer with unsubscribe
        domain = ""
        try:
            from config import SERVER_CONFIG
            domain = SERVER_CONFIG.get("domain", "")
        except ImportError:
            pass

        html_content.append(f"""
        <div class="footer">
            <p>AI前沿观察者 · 每日自动发送</p>
            <p>如不想继续接收，请 <a href="{domain}" style="color:#00D4FF;">点击此处取消订阅</a></p>
        </div>
        </body></html>
        """)

        return "\n".join(html_content)

    def _send_single(self, report: Report, recipient: str):
        msg = MIMEMultipart("alternative")
        msg["From"] = self.config["sender_email"]
        msg["To"] = recipient
        msg["Subject"] = f"{self.config['email_subject']} - {report.date}"
        msg["Date"] = formatdate(localtime=True)

        # Plain text version
        text_part = MIMEText(report.content, "plain", "utf-8")
        msg.attach(text_part)

        # HTML version
        html_body = self._build_html_body(report)
        html_part = MIMEText(html_body, "html", "utf-8")
        msg.attach(html_part)

        with smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"]) as server:
            server.starttls()
            server.login(self.config["sender_email"], self.config["sender_password"])
            server.sendmail(self.config["sender_email"], [recipient], msg.as_string())


