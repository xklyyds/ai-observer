from typing import List
from data_sources.base import NewsItem
from utils.logger import setup_logger
from .base import Processor


class NewsCategorizer(Processor):
    AI_CATEGORIES = {
        "LLM": ["GPT", "LLM", "大语言模型", "语言模型", "Transformer", "BERT", "ChatGPT", "Claude", "Gemini"],
        "图像生成": ["Stable Diffusion", "DALL-E", "图像生成", "扩散模型", "GAN", "文生图"],
        "语音": ["语音识别", "语音合成", "TTS", "ASR", "Whisper"],
        "AI代理": ["Agent", "智能代理", "自主智能", "LLM Agent"],
        "AI硬件": ["芯片", "GPU", "NPU", "AI芯片", "NVIDIA", "AMD", "Intel"],
        "生物AI": ["AlphaFold", "蛋白质", "药物发现", "生物信息"],
        "多模态": ["多模态", "视觉语言", "Vision-Language", "图文"],
        "开源项目": ["GitHub", "开源", "代码", "框架"],
        "研究论文": ["arXiv", "论文", "研究", "发表"],
        "技术新闻": ["发布", "新闻", "更新", "公告"]
    }
    
    def __init__(self):
        self.logger = setup_logger("NewsCategorizer")
    
    @property
    def name(self) -> str:
        return "NewsCategorizer"
    
    def process(self, news_items: List[NewsItem]) -> List[NewsItem]:
        self.logger.info("开始分类新闻...")
        for item in news_items:
            if not item.category:
                item.category = self._classify(item)
            if not item.tags:
                item.tags = self._extract_tags(item)
        
        self.logger.info(f"成功分类 {len(news_items)} 条新闻")
        return news_items
    
    def _classify(self, item: NewsItem) -> str:
        text = f"{item.title} {item.description}".lower()
        for category, keywords in self.AI_CATEGORIES.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return category
        return "其他"
    
    def _extract_tags(self, item: NewsItem) -> List[str]:
        tags = []
        text = f"{item.title} {item.description}"
        
        tag_keywords = {
            "LLM": ["GPT", "LLM", "语言模型"],
            "推理": ["推理", "Reasoning", "逻辑"],
            "RAG": ["RAG", "检索增强"],
            "图像": ["图像", "Image", "图片"],
            "开源": ["开源", "GitHub", "Open Source"],
            "效率": ["效率", "提速", "优化"],
            "训练": ["训练", "Train", "预训练"],
            "模型": ["模型", "Model"]
        }
        
        for tag, keywords in tag_keywords.items():
            for keyword in keywords:
                if keyword in text and tag not in tags:
                    tags.append(tag)
        
        return tags