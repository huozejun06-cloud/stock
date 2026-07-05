"""
V8引擎全局单例 + 双重检查锁
整个进程生命周期有且仅有一个 V8 引擎实例。
永生不灭——任何地方都不允许关闭或销毁它。
"""
import threading
from functools import wraps

# 全局锁（兼容旧引用：from 工具库.V8线程锁 import V8_LOCK）
V8_LOCK = threading.Lock()

# 单例状态
_V8_INITIALIZED = False
_V8_ENGINE = None  # 全局唯一实例


def get_v8_engine():
    """
    获取全局唯一的 V8 引擎实例。
    
    双重检查锁（Double-Checked Locking）：
    1. 第一次检查：无锁，快速通过
    2. 加锁 + 第二次检查：确保只有一个线程初始化
    3. 后续调用直接返回已有实例，零开销
    
    ⚠️ 永远不要 close 或删除返回的引擎！
    """
    global _V8_ENGINE, _V8_INITIALIZED
    if not _V8_INITIALIZED:                      # 第一次检查（无锁）
        with V8_LOCK:                             # 加锁
            if not _V8_INITIALIZED:               # 第二次检查（防重入）
                from py_mini_racer import MiniRacer
                _V8_ENGINE = MiniRacer()
                _V8_INITIALIZED = True
    return _V8_ENGINE


def v8_thread_safe(func):
    """装饰器：V8 调用线程安全（备用的，主要靠单例）"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        with V8_LOCK:
            return func(*args, **kwargs)
    return wrapper


def preheat_v8():
    """
    预热 V8 引擎。
    
    在程序启动时、单线程环境下先初始化一次 V8 引擎。
    后续多线程再调用 akshare 时，V8 引擎已就绪，不会触发 MiniRacer()，
    也就不会多线程撞车。
    """
    if not _V8_INITIALIZED:
        print("  🔥 预热 V8 引擎...")
        get_v8_engine()
        print("  ✅ V8 引擎预热完成")
