import os
import json
import urllib.request
import urllib.parse
import ssl
from typing import List

from data_sources.base import NewsItem
from utils.logger import setup_logger
from utils.config_loader import LLMConfig
from .base import Processor


class AISummarizer(Processor):
    def __init__(self):
        self.llm_config = LLMConfig()
        self.logger = setup_logger("AISummarizer")
        self.balance_warning_shown = False
    
    @property
    def name(self) -> str:
        return "AISummarizer"
    
    def process(self, news_items: List[NewsItem]) -> List[NewsItem]:
        if not self.llm_config.is_configured:
            self.logger.warning(f"未配置{self.llm_config.provider.upper()} API密钥，跳过AI摘要")
            return news_items
        
        self.logger.info(f"开始使用 {self.llm_config.provider.upper()} 生成AI摘要...")
        success_count = 0
        
        for item in news_items:
            try:
                summary = self._generate_summary(item)
                if summary:
                    item.description = summary
                    success_count += 1
            except urllib.error.HTTPError as e:
                if e.code == 402 and not self.balance_warning_shown:
                    self.logger.error("=" * 60)
                    self.logger.error("⚠️  DEEPSEEK余额不足！")
                    self.logger.error("请访问 https://platform.deepseek.com/ 充值后再使用AI摘要功能")
                    self.logger.error("当前将跳过AI摘要，使用原始内容")
                    self.logger.error("=" * 60)
                    self.balance_warning_shown = True
                else:
                    self.logger.error(f"为新闻 '{item.title[:20]}...' 生成摘要失败: HTTP Error {e.code}")
            except Exception as e:
                self.logger.error(f"为新闻 '{item.title[:20]}...' 生成摘要失败: {str(e)}")
        
        if success_count > 0:
            self.logger.info(f"成功为 {success_count} 条新闻生成摘要")
        elif self.balance_warning_shown:
            self.logger.info("因余额不足，未生成任何AI摘要")
        else:
            self.logger.info(f"成功为 {success_count} 条新闻生成摘要")
        
        return news_items
    
    def _generate_summary(self, item: NewsItem) -> str:
        prompt = f"""请用中文为以下AI相关新闻生成简洁精炼的摘要（50-80字），突出核心技术突破和亮点：

标题：{item.title}
原文：{item.description}

要求：
1. 保留关键技术术语
2. 突出创新性和影响力
3. 语言简洁流畅
4. 不要包含无关信息"""
        
        headers = self.llm_config.get_headers()
        
        payload = {
            "model": self.llm_config.model,
            "messages": [
                {"role": "system", "content": "你是一个专业的AI技术新闻编辑，擅长提炼技术要点"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 100
        }
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(
            self.llm_config.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"].strip()
        elif "output" in data:
            return data["output"]["text"].strip()
        return ""