# errguard

python错误管理工具, 保护接口异常中断, 实现错误的监管与分类


## 错误装饰器

错误管理使用工厂进行了装饰器的封装。工厂(`error_factory`)对以下功能进行了构建：

| 功能                       | 参数名             | 类型                    |
| -------------------------- | ------------------ | ----------------------- |
| 是否打印错误堆栈信息       | `error_debug`    | `bool`                |
| 全局错误记录               | `error_response` | `Optional[list]`      |
| 通过函数返回体注入错误信息 | `error_key`      | `Optional[str]`       |
| 待装饰的类方法             | `methods`        | `Optional[List[str]]` |
| 不装饰的类方法             | `filters`        | `Optional[List[str]]` |

其中，error_debug参数是控制是否想终端打印错误信息，这里是使用exception函数将错误堆栈完整打印，一般情况下会自动提示/填充变量的值；error_response参数不是None时，出现错误会将错误放到error_response列表内，被装饰函数返回None；error_key是函数返回体接受错误信息的关键字，返回的值是list[ErrorInfo]对象, error_response非None时会优先使用。methods和filters都是对装饰类方法的配置参数，一个指定要装饰哪些方法，另一个是排除哪些方法。

注：

1. 错误装饰器需要指定上面的参数得到实例化对象
2. 错误装饰器可以装饰类和函数
3. 错误装饰器可以装饰同步、异步函数

先定义装饰器

```Python
from errGuard.errDecorator import error_factory
error_status = []
error_decorator0 = error_factory(error_debug=True, error_response=None, error_key="elfinError")
error_decorator1 = error_factory(error_debug=False, error_response=None, error_key="elfinError")
error_decorator2 = error_factory(error_debug=False, error_response=error_status, error_key="error3")
```

### 打印错误信息

```Python
@error_decorator0
class Elfin:

    class_name = "Elfin"

    def __call__(self, num, **kwargs):
        if num < 10:
            raise MatchError(f"Num: {num} should be greater than 10.", code=500)
        else:
            raise KeyError(f"Num: {num} should be less than 10.")

elfin = Elfin()
res1 = elfin(9)
print("-*-"*12, "\n",res1)
```

输出内容:

```python
2026-06-30 23:11:52.169 | ERROR    | errGuard.errDecorator:sync_wrapper:90 - 捕获异常:
Traceback (most recent call last):

  File "/Users/elfindan/project/errguard/test.py", line 50, in <module>
    res1 = elfin(9)
           └ <__main__.Elfin object at 0x108260410>

> File "/Users/elfindan/project/errguard/errGuard/errDecorator.py", line 87, in sync_wrapper
    res = func(*args, **kwargs)
          │     │       └ {}
          │     └ (<__main__.Elfin object at 0x108260410>, 9)
          └ <function Elfin.__call__ at 0x108265760>

  File "/Users/elfindan/project/errguard/test.py", line 25, in __call__
    raise MatchError(f"Num: {num} should be greater than 10.", code=500)
          │                  └ 9
          └ <class '__main__.MatchError'>

MatchError: Num: 9 should be greater than 10.
-*--*--*--*--*--*--*--*--*--*--*--*- 
 {'elfinError': [ErrorInfo(code=500, msg='Num: 9 should be greater than 10.', traceback=['  File "/Users/elfindan/project/errguard/test.py", line 25, in __call__\n    raise MatchError(f"Num: {num} should begreater than 10.", code=500)'], timestamp='2026-06-30 23:15:34')]}
```

### 不打印错误信息

```Python
@error_decorator1
class Elfin:

    class_name = "Elfin"

    def __call__(self, num, **kwargs):
        if num < 10:
            raise MatchError(f"Num: {num} should be greater than 10.", code=500)
        else:
            raise KeyError(f"Num: {num} should be less than 10.")

elfin = Elfin()
res2 = elfin(9)
print("-*-"*12, "\n",res2)
```

输出结果:

```python
-*--*--*--*--*--*--*--*--*--*--*--*- 
 {'elfinError': [ErrorInfo(code=500, msg='Num: 9 should be greater than 10.', traceback=['  File "/Users/elfindan/project/errguard/test.py", line 25, in __call__\n    raise MatchError(f"Num: {num} should begreater than 10.", code=500)'], timestamp='2026-06-30 23:18:22')]}
```

所以`error_response=None, error_key="elfinError"`会返回带有指定的error_key的字典。

### 装饰函数

```Python
@error_decorator2
def test_error2():
    if sys.version_info < (3, 8):
        raise Exception("Python version must be 3.8 or later.")
    else:
        raise MatchError("Python version must be 3.8 or later.", code=500)

res3 = test_error2()
print("-*-"*12, "\n","res3\n", res3)
print("error_status\n", error_status)
```

输出结果:

```python
-*--*--*--*--*--*--*--*--*--*--*--*- 
 res3
 {'error3': []}
error_status
 [ErrorInfo(code=500, msg='Python version must be 3.8 or later.', traceback=['  File "/Users/elfindan/project/errguard/test.py", line 43, in test_error2\n    raise MatchError("Python version must be 3.8 or later.", code=500)'], timestamp='2026-06-30 23:25:30')]
```

---

