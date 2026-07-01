#!/usr/bin/env python3
# encoding: utf-8
# @author: firstelfin
# @time: 2026/05/23 11:43:15

import inspect
import warnings
import functools
from loguru import logger
from typing import List, Optional
from .tools import error_handler


def error_factory(
    error_debug: bool,
    error_response: Optional[list] = None,
    error_key: Optional[str] = None,
    *,
    methods: Optional[List[str]] = None,
    filters: Optional[List[str]] = None,
):
    """装饰器工厂

    Args:
        error_debug (bool): 是否是debug模式, 用于调试时打印详细错误信息。
        error_response (list, optional): 错误响应列表. Defaults to None.
        error_key (str, optional): 返回体存放错误的关键字. Defaults to None.
        methods (List[str], optional): 需要封装的类方法. Defaults to None.
        filters (List[str], optional): 不需要封装的类方法. Defaults to None.

    Returns:
        Callable: 装饰器对象
    """

    def decorator(target):
        # 判断是类还是函数, target是装饰对象本身
        if inspect.isclass(target):
            return _decorate_class(target, methods, filters, error_debug, error_response, error_key)
        else:
            # 普通函数或方法（实际上如果直接装饰方法, target 已经是函数）
            return _wrap_function(target, error_debug, error_response, error_key)

    # 如果直接 @intercept 不带参数, handler 可能是被装饰对象, 此时需要特殊处理
    # 但我们要求必须显式调用 intercept(handler) 或 intercept(handler=...)
    # 为了使用简单, 这里省略了无参数情况, 你可以通过 intercept() 带默认 handler 来支持。
    # 更健壮的写法：检测第一个参数是否可调用, 如果是则当作 handler。
    # 但为了清晰, 这里要求必须带 handler。
    return decorator


def _decorate_class(cls, methods, filters, error_debug, error_response, error_key):
    """装饰类的所有符合条件的方法"""
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        # 如果指定了 methods 列表, 只处理列表中的方法
        if methods is not None and name not in methods:
            continue
        # 如果指定了 filters 列表, 排除列表中的方法
        if filters is not None and name in filters:
            continue
        # 包装该方法
        wrapped = _wrap_function(method, error_debug, error_response, error_key)
        setattr(cls, name, wrapped)
    return cls


def _wrap_function(func, error_debug=False, error_response: Optional[list] = None, error_key: Optional[str] = None):
    """包装单个函数, 自动适配同步/异步"""

    assert error_response is not None or error_key is not None, "error_response and error_key cannot be both None."
    
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                res = await func(*args, **kwargs)
            except Exception as e:
                if error_debug:
                    logger.exception("捕获异常:")
                res = {error_key: []} if error_key is not None else None
                error_handler(e, error_response, res[error_key] if isinstance(res, dict) else None)  # type: ignore
            return res
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                res = func(*args, **kwargs)
            except Exception as e:
                if error_debug:
                    logger.exception("捕获异常:")
                res = {error_key: []} if error_key is not None else None
                error_handler(e, error_response, res[error_key] if isinstance(res, dict) else None)  # type: ignore
            return res
        return sync_wrapper
