import json
from datetime import date
from typing import Dict, List
from .settings import config
from .schema import CallRecord

class StatsService:
    def __init__(self):
        self.stats = {}
        self.model_limits = {}
        # 初始化限制信息
        for model in config.MODELS:
            self.model_limits[model['name']] = model.get('estimated_limit', 50)
        self.load_all()

    def load_all(self):
        """加载统计数据，如果是新的一天则重置"""
        try:
            if config.STATS_FILE.exists():
                with open(config.STATS_FILE, 'r') as f:
                    data = json.load(f)
                    if data.get('date') == str(date.today()):
                        self.stats = data.get('stats', {})
                    else:
                        self.reset_daily_stats()
            else:
                self.reset_daily_stats()
        except:
            self.reset_daily_stats()
        
        # 确保所有配置中的模型都在 stats 中有记录
        for model in config.MODELS:
            if model['name'] not in self.stats:
                self._init_model_stat(model['name'])

    def _init_model_stat(self, name: str):
        self.stats[name] = {
            'calls': 0, 
            'success_calls': 0, 
            'error_calls': 0,
            'total_response_time': 0, 
            'last_error': None, 
            'is_limited': False
        }

    def save_stats(self):
        try:
            data = {'date': str(date.today()), 'stats': self.stats}
            with open(config.STATS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass

    def reset_daily_stats(self):
        self.stats = {}
        for model in config.MODELS:
            self._init_model_stat(model['name'])
        self.save_stats()

    def record_call(self, record: CallRecord):
        if record.model_name not in self.stats:
            self.reset_daily_stats()
            
        st = self.stats[record.model_name]
        st['calls'] += 1
        st['total_response_time'] += record.response_time
        
        if record.success:
            st['success_calls'] += 1
        else:
            st['error_calls'] += 1
            st['last_error'] = record.error_message
            # 简单的限流检测策略
            if record.error_message and any(x in str(record.error_message).lower() for x in ["limit", "quota", "429"]):
                st['is_limited'] = True
                
        self.stats[record.model_name] = st
        self.save_stats()

    def get_available_models(self) -> List[Dict]:
        """获取当前可用（未被限流）的模型列表"""
        available = []
        for model in config.MODELS:
            st = self.stats.get(model['name'], {})
            if st.get('is_limited', False):
                continue
            
            # 返回模型配置的副本，附带当前调用次数供路由参考
            model_with_stats = model.copy()
            model_with_stats['_calls'] = st.get('calls', 0)
            available.append(model_with_stats)
        return available

    def get_snapshot(self) -> Dict:
        """返回当前统计数据的快照，供 UI 使用"""
        return {
            "stats": self.stats,
            "limits": self.model_limits
        }

# 全局单例
stats_service = StatsService()