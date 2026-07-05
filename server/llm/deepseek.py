# ==============================================================================
# server/llm/deepseek.py — DeepSeek API 适配器
# Phase B-3: 继承 LLMAdapter，封装 DeepSeek API
# ==============================================================================

import json
import httpx
from typing import Optional, Dict, Any

from server.llm.base import LLMAdapter, DecisionResult


class DeepSeekAdapter(LLMAdapter):
    """DeepSeek API 适配器"""
    
    BASE_URL = "https://api.deepseek.com/v1"
    
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        super().__init__(api_key, model)
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    
    def generate_decision(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> DecisionResult:
        """调用 DeepSeek API 生成决策"""
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的股票量化分析师。请根据提供的技术指标和市场数据，"
                               "输出交易决策。格式: 信号(BUY/WATCH/SELL), 置信度(0~1), "
                               "理由, 风险等级(LOW/MEDIUM/HIGH)。"
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 500,
        }
        
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=self._headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
            
            content = data["choices"][0]["message"]["content"]
            
            # 从回复中解析决策（简单关键词匹配）
            signal = self._parse_signal(content)
            confidence = self._parse_confidence(content)
            risk = self._parse_risk(content)
            
            return DecisionResult(
                signal=signal,
                confidence=confidence,
                reasoning=content[:500],
                risk_level=risk,
                key_metrics={"model": self.model, "provider": "deepseek"},
            )
            
        except httpx.TimeoutException:
            return DecisionResult(
                signal="INSUFFICIENT_DATA",
                confidence=0.0,
                reasoning="DeepSeek API 请求超时",
                risk_level="HIGH",
                key_metrics={"error": "timeout"},
            )
        except Exception as e:
            return DecisionResult(
                signal="INSUFFICIENT_DATA",
                confidence=0.0,
                reasoning=f"DeepSeek API 调用失败: {str(e)[:200]}",
                risk_level="HIGH",
                key_metrics={"error": str(e)[:100]},
            )
    
    def health_check(self) -> bool:
        """检查 DeepSeek API 是否可用"""
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=self._headers,
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "OK"}],
                        "max_tokens": 5,
                    },
                )
                return resp.status_code == 200
        except:
            return False
    
    def _parse_signal(self, content: str) -> str:
        """从回复中提取交易信号"""
        upper = content.upper()
        if "BUY" in upper or "买入" in content:
            return "BUY"
        elif "SELL" in upper or "卖出" in content:
            return "SELL"
        elif "WATCH" in upper or "观望" in content:
            return "WATCH"
        return "INSUFFICIENT_DATA"
    
    def _parse_confidence(self, content: str) -> float:
        """从回复中提取置信度"""
        import re
        matches = re.findall(r'(?:置信度|confidence)[：: ]*([0-9.]+)', content)
        if matches:
            try:
                val = float(matches[0])
                return min(1.0, max(0.0, val))
            except:
                pass
        return 0.5
    
    def _parse_risk(self, content: str) -> str:
        """从回复中提取风险等级"""
        if "HIGH" in content or "高" in content[:200]:
            return "HIGH"
        elif "MEDIUM" in content or "中" in content[:200]:
            return "MEDIUM"
        return "LOW"
