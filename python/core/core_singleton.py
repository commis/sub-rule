import threading
from typing import Any, Callable, TypeVar

# 定义类型变量，支持所有类
_T = TypeVar("_T")


class SingletonDecorator:
    """线程安全的单例装饰器"""

    def __init__(self, cls: Callable[..., _T]):
        self._cls = cls
        self._instance: _T | None = None
        self._lock: threading.Lock = threading.Lock()

    def __call__(self, *args: Any, **kwargs: Any) -> _T:
        """控制类的实例化过程"""
        # 无锁快速检查（提升性能）
        if self._instance is None:
            # 加锁确保线程安全
            with self._lock:
                if self._instance is None:
                    self._instance = self._cls(*args, **kwargs)
        return self._instance


# 简化别名，方便使用
singleton = SingletonDecorator
