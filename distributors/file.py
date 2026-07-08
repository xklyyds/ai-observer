import os
from datetime import datetime

from .base import Distributor, Report
from utils.logger import setup_logger


class FileDistributor(Distributor):
    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = output_dir
        self.logger = setup_logger("FileDistributor")
    
    @property
    def name(self) -> str:
        return "File"
    
    def distribute(self, report: Report) -> bool:
        self.logger.info("保存日报文件...")
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            filename = f"ai_report_{datetime.now().strftime('%Y%m%d')}.txt"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report.content)
            
            self.logger.info(f"日报已保存到 {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"保存日报失败: {str(e)}")
            return False
    
    def get_output_path(self) -> str:
        filename = f"ai_report_{datetime.now().strftime('%Y%m%d')}.txt"
        return os.path.join(self.output_dir, filename)