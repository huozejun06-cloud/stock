# ==============================================================================
# 工具库/策略线程基类.py — 策略执行线程基类（统一异常处理 + 信号规范）
# 2026-06-05 新增：所有策略线程继承此类，消除重复的 try-except 代码
# ==============================================================================

from PySide6.QtCore import QThread, Signal
import traceback


class BaseStrategyThread(QThread):
    """策略执行线程基类 - 统一异常处理和信号定义
    
    所有策略子类只需实现 _执行() 方法返回结果，
    线程的启动/异常/日志/进度全部由基类统一管理。
    
    信号规范：
    - 完成信号(object): 返回执行结果
    - 错误信号(str): 错误消息
    - 日志信号(str): 日志消息（② 日志面板使用）
    - 进度信号(int): 0-100 进度值（③ 进度条使用）
    """
    完成信号 = Signal(object)
    错误信号 = Signal(str)
    日志信号 = Signal(str)      # ② 日志
    进度信号 = Signal(int)      # ③ 进度

    def 安全执行(self, func):
        """统一异常处理外壳"""
        try:
            self.日志信号.emit("开始执行...")
            result = func()
            self.完成信号.emit(result)
            self.日志信号.emit("✅ 执行完成")
            self.进度信号.emit(100)
        except Exception as e:
            err = f"{str(e)}\n{traceback.format_exc()}"
            self.错误信号.emit(err)
            self.日志信号.emit(f"❌ 执行失败: {str(e)}")

    def run(self):
        raise NotImplementedError("子类必须实现 run()")
