EMAIL_CONFIG = {
    "smtp_server": "smtp.qq.com",
    "smtp_port": 587,
    "sender_email": "2835234675@qq.com",
    "sender_password": "hgzqwxueepqcdhej",
    "receiver_email": "2835234675@qq.com",
    "email_subject": "每日AI前沿技术日报"
}

AI_OBSERVER_CONFIG = {
    "description": "每日AI前沿日报",
    "query": "过去24小时AI领域最重要的技术突破，包括arXiv预印本、OpenAI、Google DeepMind、Anthropic等机构的最新进展",
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
        "categories": ["cs.AI", "cs.LG", "stat.ML"],
        "max_results": 10
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
        "feeds": ["量子位", "机器之心"],
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