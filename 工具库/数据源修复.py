"""
数据源修复（兼容旧版引用）
现转发到新版数据源管理器
"""
from 工具库.数据源管理器 import get_manager
from 工具库.自动补丁 import auto_patch

# 兼容旧版函数名
EASTMONEY_SERVERS = ["push2.eastmoney.com", "1.push2.eastmoney.com", "2.push2.eastmoney.com"]

def get_available_server():
    """兼容旧版"""
    mgr = get_manager()
    return mgr.current_source

def patch_akshare_url():
    """兼容旧版：检查东财可用性，必要时自动降级"""
    auto_patch()
    return True
