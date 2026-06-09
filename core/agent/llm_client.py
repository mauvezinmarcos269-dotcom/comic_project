import json
import re
import urllib.request
import urllib.error
from typing import Any

API_URL = "https://api.siliconflow.cn/v1/chat/completions"

class SiliconFlowClient:
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("API Key 不能为空，请在 .env 文件中配置 SILICONFLOW_API_KEY")
        
        # 主动防御，拦截包含中文字符的错误配置
        try:
            api_key.encode('ascii')
        except UnicodeEncodeError:
            raise ValueError(
                "【配置错误】检测到您的 `SILICONFLOW_API_KEY` 中包含中文字符或非法空格！\n"
                "请务必打开项目根目录下的 `.env` 文件，将类似 '请替换为你的密钥' 的中文提示文字完全删除，"
                "并替换为以 'sk-' 开头的真实官方 API Key。"
            )
            
        self.api_key = api_key.strip()
        self.model = model

    def chat_json(self, messages: list[dict[str, str]], temperature: float = 0.1) -> dict[str, Any]:
        """请求大模型并强制返回/解析为 JSON 字典"""
        payload = {
            "model": self.model,
            "temperature": temperature,
            "enable_thinking": False,
            "messages": messages,
        }

        req = urllib.request.Request(
            API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                if "choices" not in data or not data["choices"]:
                    raise ValueError(f"API 返回异常节点: {data}")
                
                content = data["choices"][0].get("message", {}).get("content", "")
                return self._extract_json(content)
                
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise RuntimeError("SiliconFlow 鉴权失败(401)，请检查账户额度是否充足或密钥是否已被官方停用。")
            raise RuntimeError(f"HTTP 远程错误 {e.code}: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"大模型网络连接或网关故障: {str(e)}")

    def _extract_json(self, content: str) -> dict[str, Any]:
        """稳健的 JSON 剥离器"""
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", content, flags=re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
                
        # 若模型返回了纯文本而非标准JSON，将其转换为通用QA格式，防止彻底引发崩溃
        return {"module": "generic_qa", "params": {}, "reason": "未按标准格式输出JSON，强行兜底降级", "raw_content": content}