import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from datetime import datetime

from .base import Distributor, Report
from utils.logger import setup_logger


class EmailDistributor(Distributor):
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger("EmailDistributor")
    
    @property
    def name(self) -> str:
        return "Email"
    
    def distribute(self, report: Report) -> bool:
        self.logger.info("开始发送邮件...")
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config["sender_email"]
            msg['To'] = self.config["receiver_email"]
            msg['Subject'] = f"{self.config['email_subject']} - {datetime.now().strftime('%Y%m%d')}"
            msg['Date'] = formatdate(localtime=True)
            
            body = MIMEText(report.content, 'plain', 'utf-8')
            msg.attach(body)
            
            with smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"]) as server:
                server.starttls()
                server.login(self.config["sender_email"], self.config["sender_password"])
                server.sendmail(
                    self.config["sender_email"],
                    self.config["receiver_email"],
                    msg.as_string()
                )
            
            self.logger.info("邮件发送成功")
            return True
        except Exception as e:
            self.logger.error(f"邮件发送失败: {str(e)}")
            return False