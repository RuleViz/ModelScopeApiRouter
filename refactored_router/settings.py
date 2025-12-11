import os
import json
from pathlib import Path
from typing import List, Dict

class Settings:
    def __init__(self):
        self.BASE_DIR = Path(__file__).parent
        self.DATA_DIR = self.BASE_DIR / "router_data"
        self.STATS_FILE = self.DATA_DIR / "model_stats.json"
        self.CONFIG_FILE = self.BASE_DIR / "config.json"
        self.ENV_FILE = self.BASE_DIR / ".env"
        
        self.DATA_DIR.mkdir(exist_ok=True)
        
        self._load_env()
        self.API_KEY = os.getenv("MS_API_KEY", "")
        self.BASE_URL = os.getenv("MS_BASE_URL", "https://api-inference.modelscope.cn/v1")
        self.PORT = int(os.getenv("PORT", "2166"))
        self.ROUTER_ALIAS = "modelscope-router"
        
        self.MODELS = self._load_models()

    def _load_env(self):
        """简单的 .env 解析器，避免引入 python-dotenv 依赖"""
        if not self.ENV_FILE.exists():
            return
        with open(self.ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

    def _load_models(self) -> List[Dict]:
        if not self.CONFIG_FILE.exists():
            return []
        with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

# 单例模式
config = Settings()