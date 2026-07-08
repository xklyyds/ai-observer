import os

import os
from pathlib import Path

EMAIL_CONFIG = {
    "smtp_server": os.environ.get("SMTP_SERVER", "smtp.qq.com"),
    "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
    "sender_email": os.environ.get("SMTP_SENDER_EMAIL", ""),
    "sender_password": os.environ.get("SMTP_SENDER_PASSWORD", ""),
    "receiver_email": os.environ.get("SMTP_RECEIVER_EMAIL", ""),
    "email_subject": "每日AI前沿技术日报"
}

SERVER_CONFIG = {
    "host": os.environ.get("SERVER_HOST", "0.0.0.0"),
    "port": int(os.environ.get("SERVER_PORT", "5000")),
    "domain": os.environ.get("SERVER_DOMAIN", "http://localhost:5000"),
    "db_path": os.environ.get("DB_PATH", ""),
    "secret_key": os.environ.get("SECRET_KEY", "change-this-to-a-random-secret-key"),
}

AI_OBSERVER_CONFIG = {
    "description": "每日AI前沿日报",
    "query": "过去24小时AI及互联网科技领域最重要的技术突破，涵盖大模型、AI应用、云计算、网络安全、开源项目、芯片等方向",
    "response_language": "zh"
}

DATA_SOURCES_CONFIG = {
    "bing": {
        "enabled": True,
        "use_mock": True,
        "query": "AI技术突破",
        "count": 10
    },
    "arxiv": {
        "enabled": True,
        "use_mock": False,
        "categories": ["cs.AI", "cs.LG", "stat.ML", "cs.CV", "cs.CL", "cs.SE", "cs.CR", "cs.NE", "cs.RO", "cs.DC"],
        "max_results": 20
    },
    "github": {
        "enabled": True,
        "use_mock": True,
        "language": "python",
        "since": "daily"
    },
    "hackernews": {
        "enabled": True,
        "use_mock": True,
        "max_items": 10
    },
    "rss": {
        "enabled": True,
        "feeds": ["量子位", "机器之心", "TechCrunch", "The Verge", "Ars Technica", "Wired", "InfoQ", "Hacker News"],
        "max_per_feed": 5
    },
    "zhihu": {
        "enabled": True,
        "use_mock": True,
        "max_items": 10
    },
    "techmedia": {
        "enabled": True,
        "max_items": 10
    },
    "nature": {
        "enabled": True,
        "use_mock": True,
        "max_items": 15
    },
    "mit_tech_review": {
        "enabled": True,
        "use_mock": True,
        "max_items": 10
    },
    "biorxiv": {
        "enabled": True,
        "use_mock": True,
        "max_items": 10
    }
}

PROCESSORS_CONFIG = {
    "categorizer": {
        "enabled": True
    },
    "summarizer": {
        "enabled": True
    },
    "trend_analyzer": {
        "enabled": True
    }
}

DISTRIBUTORS_CONFIG = {
    "email": {
        "enabled": True
    },
    "telegram": {
        "enabled": True
    },
    "file": {
        "enabled": True
    }
}

REPORT_OUTPUT_DIR = "./reports"
LOG_FILE = "./ai_daily_report.log"
