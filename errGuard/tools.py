#!/usr/bin/env python3
# encoding: utf-8
# @author: firstelfin
# @time: 2026/05/31 11:37:15

import functools
import inspect
import traceback
from datetime import datetime
from traceback import FrameSummary
from types import TracebackType
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Union


def is_async_function(func):
    return func.__code__.co_flags & 0x80  # 检查CO_ASYNC标志


def traceback_info(e: Union[Exception, TracebackType]):
    """根据TracebackType或Exception对象获取异常信息

    traceback.print_exception()会直接打印完整异常信息到标准输出

    Args:
        e (Union[Exception, TracebackType]): 报错信息对象或者主动通过sys获取的调用栈对象

    Returns:
        list[FrameSummary]: 异常信息列表,每个元素是一个FrameSummary对象,包含文件名、行号、函数名和代码片段
    
    Example:
        >>> import traceback
        >>> trace_info = traceback_info(e)
        ... [<FrameSummary file /Users/elfindan/project/errguard/test.py, line 21 in <module>>, <FrameSummary file /Users/elfindan/project/errguard/test.py, line 16 in __call__>]
        >>> traceback.print_exception(type(e), e, e.__traceback__, file=sys.stdout)
        ... Traceback (most recent call last):
        ... File "/Users/elfindan/project/errguard/test.py", line 23, in <module>
        ...     elfin(25)
        ... File "/Users/elfindan/project/errguard/test.py", line 18, in __call__
        ...     raise KeyError(f"Num: {num} should be less than 10.")
        ... KeyError: 'Num: 25 should be less than 10.'
    """
    tb_obj = e.__traceback__ if isinstance(e, Exception) else e
    results: list[FrameSummary] = traceback.extract_tb(tb_obj)
    return results


def format_frame_summary(fs) -> str:
    s = f'  File "{fs.filename}", line {fs.lineno}, in {fs.name}'
    if fs.line:
        s += f'\n    {fs.line.strip()}'
    return s


def get_last_traceback_info(e: Union[Exception, TracebackType]) -> str:
    """获取最后一个异常信息的字符串表示"""
    tb_info = traceback_info(e)
    last_tb = tb_info[-1]
    res_str = format_frame_summary(last_tb)
    return res_str


@dataclass
class ErrorInfo:

    code: str            # 错误编码
    msg: str             # 错误信息
    traceback: list      # 调用栈（字符串格式）
    timestamp: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


def error_handler(e: Exception, error_response: Optional[list] = None, error_inject_list: Optional[list] = None):
    """处理异常并返回错误响应"""
    error_item = ErrorInfo(
        code="",
        msg=str(e),
        traceback=[get_last_traceback_info(e)]
    )
    if error_response is not None:
        # 将错误对象传入指定对象error_response中
        error_response.append(error_item)
    else:
        # 将错误分配给指定的对象关键字error_key中
        error_inject_list.append(error_item)  # type: ignore

