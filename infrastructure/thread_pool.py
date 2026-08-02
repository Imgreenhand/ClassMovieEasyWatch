"""
【Infrastructure Layer】线程池

基于 concurrent.futures 的简单线程池封装。
"""

import logging
from concurrent.futures import ThreadPoolExecutor, Future
from collections.abc import Callable
from typing import Any


class ThreadPool:
    """全局线程池单例，用于将阻塞操作放到后台线程执行"""

    _instance: "ThreadPool | None" = None

    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="cmew-worker")

    @classmethod
    def get_instance(cls, max_workers: int = 4) -> "ThreadPool":
        if cls._instance is None:
            cls._instance = cls(max_workers=max_workers)
        return cls._instance

    def submit(self, fn: Callable[..., Any], *args, **kwargs) -> Future:
        """提交任务到线程池，返回 Future"""
        return self._executor.submit(fn, *args, **kwargs)

    def shutdown(self, wait: bool = True) -> None:
        """关闭线程池"""
        try:
            self._executor.shutdown(wait=wait)
        except Exception:
            logging.warning("线程池关闭时出现异常", exc_info=True)
