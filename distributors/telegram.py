import os
import urllib.request
import urllib.parse
import json

from .base import Distributor, Report
from utils.logger import setup_logger


class TelegramDistributor(Distributor):
    def __init__(self):
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        self.logger = setup_logger("TelegramDistributor")
    
    @property
    def name(self) -> str:
        return "Telegram"
    
    def distribute(self, report: Report) -> bool:
        if not self.bot_token or not self.chat_id:
            self.logger.warning("未配置Telegram环境变量，跳过Telegram推送")
            return True
        
        self.logger.info("开始发送Telegram消息...")
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            max_length = 4096
            if len(report.content) > max_length:
                chunks = [report.content[i:i+max_length] for i in range(0, len(report.content), max_length)]
                for i, chunk in enumerate(chunks):
                    params = urllib.parse.urlencode({
                        "chat_id": self.chat_id,
                        "text": f"📄 AI日报 [{i+1}/{len(chunks)}]\n\n{chunk}",
                        "parse_mode": "Markdown"
                    })
                    full_url = f"{url}?{params}"
                    with urllib.request.urlopen(full_url) as response:
                        json.loads(response.read().decode("utf-8"))
            else:
                params = urllib.parse.urlencode({
                    "chat_id": self.chat_id,
                    "text": f"📄 AI日报 {report.date}\n\n{report.content}",
                    "parse_mode": "Markdown"
                })
                full_url = f"{url}?{params}"
                with urllib.request.urlopen(full_url) as response:
                    json.loads(response.read().decode("utf-8"))
            
            self.logger.info("Telegram消息发送成功")
            return True
        except Exception as e:
            self.logger.error(f"Telegram消息发送失败: {str(e)}")
            return False