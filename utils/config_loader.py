import os
import json


def load_env_file(env_path: str = ".env"):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


class LLMConfig:
    PROVIDERS = {
        "openai": {
            "base_url": "https://api.openai.com/v1/chat/completions",
            "api_key_env": "OPENAI_API_KEY",
            "model_env": "OPENAI_MODEL",
            "default_model": "gpt-3.5-turbo",
            "auth_prefix": "Bearer"
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1/chat/completions",
            "api_key_env": "DEEPSEEK_API_KEY",
            "model_env": "DEEPSEEK_MODEL",
            "default_model": "deepseek-chat",
            "auth_prefix": "Bearer"
        },
        "zhipu": {
            "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            "api_key_env": "ZHIPU_API_KEY",
            "model_env": "ZHIPU_MODEL",
            "default_model": "glm-4",
            "auth_prefix": "Bearer"
        },
        "qianwen": {
            "base_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            "api_key_env": "QIANWEN_API_KEY",
            "model_env": "QIANWEN_MODEL",
            "default_model": "qwen-turbo",
            "auth_prefix": "Bearer"
        }
    }

    def __init__(self):
        load_env_file()
        self.provider = os.environ.get("LLM_PROVIDER", "deepseek").lower()
        self._validate_provider()

    def _validate_provider(self):
        if self.provider not in self.PROVIDERS:
            self.provider = "deepseek"

    @property
    def api_key(self) -> str:
        config = self.PROVIDERS[self.provider]
        return os.environ.get(config["api_key_env"], "")

    @property
    def model(self) -> str:
        config = self.PROVIDERS[self.provider]
        return os.environ.get(config["model_env"], config["default_model"])

    @property
    def base_url(self) -> str:
        return self.PROVIDERS[self.provider]["base_url"]

    @property
    def auth_prefix(self) -> str:
        return self.PROVIDERS[self.provider]["auth_prefix"]

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def get_headers(self) -> dict:
        return {
            "Authorization": f"{self.auth_prefix} {self.api_key}",
            "Content-Type": "application/json"
        }