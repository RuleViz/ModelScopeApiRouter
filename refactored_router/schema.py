from typing import Optional
from pydantic import BaseModel

class CallRecord(BaseModel):
    id: str
    timestamp: float
    model_name: str
    success: bool
    response_time: float
    error_message: Optional[str] = None

class ModelConfig(BaseModel):
    name: str
    model_id: str
    estimated_limit: int = 50
    # 运行时状态字段，不存入 config.json
    calls: int = 0
