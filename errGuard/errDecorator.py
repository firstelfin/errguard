#!/usr/bin/env python3
# encoding: utf-8
# @author: firstelfin
# @time: 2026/05/23 11:43:15

import os
import sys
import inspect
import warnings
import traceback
import functools
from loguru import logger
from typing import Callable, List, Optional, Union
from .tools import is_async_function, ErrorInfo, traceback_info, error_handler


class ErrorCatcher(object):
    r"""错误管理类, 执行算子的错误管理, 遇到错误会给`res_obj`注入错误的顺序调用栈到`error_msg`, 注入错误编码到`error_code`.

    Example::

        ```
        class MatchError(Exception): ...

        class ResItem(BaseModel):
            resCode: int = 0
            resMsg:  str = ""


        @ErrorCheck(res_obj="res_item")
        class Elfin:

            class_name = "Elfin"

            def __call__(self, num, **kwargs):
                if num < 10:
                    raise MatchError(f"Num: {num} should be greater than 10.")
                else:
                    raise KeyError(f"Num: {num} should be less than 10.")
        
        if __name__ == "__main__":
            elfin = Elfin()
            res = ResItem()
            elfin(20, res_item=res)
            print(res)
        
        ```

    """

    class_name = "ErrorCheck"
    type2code = dict()  # ERROR_NAME2CODE

    def __init__(self, res_obj="res_item", error_code="resCode", error_msg="resMsg") -> None:
        self.error_code = error_code
        self.error_msg  = error_msg
        self.res_obj    = res_obj
    
    def __call__(self, cls):

        # 定义__call__
        is_class = isinstance(cls, type)
        cls_call = cls.__call__ if is_class else cls

        async_status = is_async_function(cls_call)
        res_item_error_msg = f"ResItemAttrError: {cls.__name__} does not have parameter {self.res_obj}; "\
            f"Please use the format {self.res_obj}={self.res_obj}_param to pass parameters within the __call__ method."

        def call_hook(_self, *args, **kwargs):
            res_item = kwargs.get(self.res_obj, None)
            assert res_item is not None, res_item_error_msg

            try:
                res = cls_call(_self, *args, **kwargs)
                return res
            except Exception as e:
                res_item = self.inject(res_item, e)
                return res_item
        
        async def async_call_hook(_self, *args, **kwargs):
            res_item = kwargs.get(self.res_obj, None)
            assert res_item is not None, res_item_error_msg

            try:
                res = await cls_call(_self, *args, **kwargs)
                return res
            except Exception as e:
                res_item = self.inject(res_item, e)
                return res_item
        
        if is_class:
            cls.__call__ = call_hook if not async_status else async_call_hook
        else:
            cls = call_hook if not async_status else async_call_hook
        return cls

    def inject(self, res_item, e):
        error_code, error_msg = self.get_error_code_msg(e)
        if isinstance(res_item, dict):
            res_item.update({f"{self.error_code}": error_code, f"{self.error_msg}": error_msg})
            return res_item
        setattr(res_item, self.error_code, error_code)
        setattr(res_item, self.error_msg, error_msg)
        return res_item
    
    def inject_type_to_code(self, trans: dict):
        self.type2code = self.type2code.update(trans)
    
    def get_error_code_msg(self, e):
        error_str = str(e)
        traceback_list = traceback.extract_tb(e.__traceback__)[1:]
        traceback_list.reverse()
        traceback_str = f" --> ".join([str(tl) for tl in traceback_list])
        try:
            suffix_desc = f" --> errorColNum:[{traceback_list[-1].colno+1}->{traceback_list[-1].end_colno+1}]"
        except:
            suffix_desc = ""
        error_str += " tracebackStr:" + traceback_str + suffix_desc
        error_class = error_str.split(":")[0]
        error_code = self.type2code.get(error_class, 99)
        logger.info(f"errorCode:{error_code} -> errorMsg:{error_str}")
        return error_code, error_str


def intercept(
    error_debug: bool,
    error_response: Optional[list] = None,
    error_key: Optional[str] = None,
    *,
    methods: Optional[List[str]] = None,
):
    """装饰器工厂

    Args:
        error_debug (bool): 是否是debug模式, 用于调试时打印详细错误信息。
        error_response (list, optional): 错误响应列表. Defaults to None.
        error_key (str, optional): 返回体存放错误的关键字. Defaults to None.
        methods (List[str], optional): 需要封装的类方法. Defaults to None.

    Returns:
        Callable: 装饰器对象
    """

    def decorator(target):
        # 判断是类还是函数, target是装饰对象本身
        if inspect.isclass(target):
            return _decorate_class(target, methods, error_debug, error_response, error_key)
        else:
            # 普通函数或方法（实际上如果直接装饰方法, target 已经是函数）
            return _wrap_function(target, error_debug, error_response, error_key)

    # 如果直接 @intercept 不带参数, handler 可能是被装饰对象, 此时需要特殊处理
    # 但我们要求必须显式调用 intercept(handler) 或 intercept(handler=...)
    # 为了使用简单, 这里省略了无参数情况, 你可以通过 intercept() 带默认 handler 来支持。
    # 更健壮的写法：检测第一个参数是否可调用, 如果是则当作 handler。
    # 但为了清晰, 这里要求必须带 handler。
    return decorator


def _decorate_class(cls, methods, error_debug, error_response, error_key):
    """装饰类的所有符合条件的方法"""
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        # 如果指定了 methods 列表, 只处理列表中的方法
        if methods is not None and name not in methods:
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
