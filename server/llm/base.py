# ==============================================================================
# server/llm/base.py — LLM 适配器抽象基类 + 限流/重试/降级
# Phase B-6: 三层保护机制
# ==============================================================================

import time
import random
from abc import ABC, abstractmethod
from collections import deque
from typing import Optional, Dict, Any, Callable
from pydantic import BaseModel


# ==============================================================================
# 决策结果模型
# ==============================================================================

class DecisionResult(BaseModel):
    """所有 LLM Adapter 统一返回的结构化决策结果"""
    signal: str
    confidence: float
    reasoning: str
    risk_level: str
    key_metrics: Dict[str, Any]


# ==============================================================================
# 速率限制器
# ==============================================================================

class RateLimiter:
    """滑动窗口速率限制器"""
    
    def __init__(self, max_calls_per_minute: int = 30):
        self.max_calls = max_calls_per_minute
        self._timestamps: deque = deque()
    
    def wait_if_needed(self):
        """超过限制则自动等待"""
        now = time.time()
        while self._timestamps and self._timestamps[0] < now - 60:
            self._timestamps.popleft()
        
        if len(self._timestamps) >= self.max_calls:
            wait = self._timestamps[0] + 60 - now
            if wait > 0:
                time.sleep(wait)
        
        self._timestamps.append(time.time())
    
    @property
    def used_this_minute(self) -> int:
        now = time.time()
        while self._timestamps and self._timestamps[0] < now - 60:
            self._timestamps.popleft()
        return len(self._timestamps)


# ==============================================================================
# 重试装饰器
# ==============================================================================

_EXPONENTIAL_RETRY_EXCEPTIONS = (TimeoutError, ConnectionError, ConnectionResetError)


def with_retry(max_retries: int = 3, base_delay: float = 1.0):
    """指数退避重试装饰器（带随机抖动）"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except _EXPONENTIAL_RETRY_EXCEPTIONS as e:
                    last_error = e
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                    time.sleep(delay)
            raise last_error  # type: ignore
        return wrapper
    return decorator


# ==============================================================================
# LLM 适配器抽象基类
# ==============================================================================

class LLMAdapter(ABC):
    """LLM 适配器基类 — 子类需实现 generate_decision() 和 health_check()"""
    
    def __init__(self, api_key: str, model: str = "default"):
        self.api_key = api_key
        self.model = model
        self._rate_limiter = RateLimiter(max_calls_per_minute=30)
    
    @abstractmethod
    def generate_decision(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> DecisionResult:
        ...
    
    @abstractmethod
    def health_check(self) -> bool:
        ...
    
    def safe_generate_decision(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> DecisionResult:
        """带限流 + 重试的安全决策方法

        外部调用者应使用此方法而非直接调用 generate_decision()
        """
        try:
            self._rate_limiter.wait_if_needed()
            
            @with_retry(max_retries=3, base_delay=1.0)
            def _call():
                return self.generate_decision(prompt, context)
            
            return _call()
        except Exception as e:
            return DecisionResult(
                signal="INSUFFICIENT_DATA",
                confidence=0.0,
                reasoning=f"所有重试均失败: {str(e)[:200]}",
                risk_level="HIGH",
                key_metrics={"error": str(e)[:100], "retries": 3},
            )
    
    def get_provider_name(self) -> str:
        return self.__class__.__name__
