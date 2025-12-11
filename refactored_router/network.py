import time
import uuid
import httpx
import json
from typing import AsyncGenerator, Tuple, Any
from fastapi.responses import StreamingResponse, JSONResponse
from .settings import config
from .schema import CallRecord
from .stats import stats_service
from .ui import dashboard

class APIClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {config.API_KEY}",
            "Content-Type": "application/json"
        }

    async def call_model(self, model_info: dict, payload: dict, is_stream: bool) -> Tuple[bool, Any, str]:
        """
        统一调用接口
        Returns: (success, response_object, error_message)
        """
        model_name = model_info['name']
        model_id = model_info['model_id']
        
        # 准备请求负载
        current_payload = payload.copy()
        current_payload['model'] = model_id
        
        start_time = time.time()
        client = httpx.AsyncClient(timeout=60.0)
        
        try:
            request_obj = client.build_request(
                "POST", 
                f"{config.BASE_URL}/chat/completions", 
                json=current_payload, 
                headers=self.headers
            )
            
            response = await client.send(request_obj, stream=True)
            
            if response.status_code != 200:
                error_text = await response.aread()
                await client.aclose()
                return False, None, f"HTTP {response.status_code}: {error_text.decode('utf-8', errors='ignore')[:100]}"

            if is_stream:
                # 记录开始调用的信息（虽然不知道什么时候结束，但先占个位，或者在流结束时记录）
                # 这里我们创建一个生成器 wrapper 来在流结束时记录 stats
                record_template = CallRecord(
                    id=str(uuid.uuid4()), timestamp=start_time, model_name=model_name,
                    success=False, response_time=0
                )
                
                return True, StreamingResponse(
                    self._stream_wrapper(client, response, record_template),
                    media_type="text/event-stream"
                ), ""
            else:
                data = await response.aread()
                await client.aclose()
                
                # 记录成功
                duration = time.time() - start_time
                record = CallRecord(
                    id=str(uuid.uuid4()), timestamp=start_time, model_name=model_name,
                    success=True, response_time=duration
                )
                stats_service.record_call(record)
                dashboard.log_result(record)
                
                return True, JSONResponse(json.loads(data)), ""

        except Exception as e:
            await client.aclose()
            return False, None, str(e)

    async def _stream_wrapper(self, client: httpx.AsyncClient, response: httpx.Response, record: CallRecord):
        """包装流式响应以监控完成状态"""
        try:
            async for chunk in response.aiter_bytes():
                yield chunk
            
            # 流正常结束
            record.response_time = time.time() - record.timestamp
            record.success = True
            stats_service.record_call(record)
            dashboard.log_result(record)
            
        except Exception as e:
            # 流异常中断
            record.error_message = f"Stream broken: {str(e)}"
            record.response_time = time.time() - record.timestamp
            stats_service.record_call(record)
            dashboard.log_result(record)
            raise e
        finally:
            await client.aclose()

api_client = APIClient()