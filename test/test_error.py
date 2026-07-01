import sys
sys.path.append('..') # Add the parent directory to the system path
from pyadorn.errDecorator import error_factory
from pyadorn.tools import traceback_info, ErrorInfo, get_last_traceback_info
import sys
import traceback
from loguru import logger

error_status = []
error_decorator0 = error_factory(error_debug=True, error_response=None, error_key="elfinError")
error_decorator1 = error_factory(error_debug=False, error_response=None, error_key="elfinError")
error_decorator2 = error_factory(error_debug=False, error_response=error_status, error_key="error3")

class MatchError(Exception):
    def __init__(self, msg, code=599):
        self.msg = msg
        self.code = code


@error_decorator2
class Elfin:

    class_name = "Elfin"

    def __call__(self, num, **kwargs):
        if num < 10:
            raise MatchError(f"Num: {num} should be greater than 10.", code=500)
        else:
            raise KeyError(f"Num: {num} should be less than 10.")


@error_decorator1
def test_error():
    if sys.version_info < (3, 8):
        raise Exception("Python version must be 3.8 or later.")
    else:
        raise MatchError("Python version must be 3.8 or later.", code=500)


@error_decorator2
def test_error2():
    if sys.version_info < (3, 8):
        raise Exception("Python version must be 3.8 or later.")
    else:
        raise MatchError("Python version must be 3.8 or later.", code=500)


# elfin = Elfin()
# res1 = elfin(9)
# print("-*-"*12, "\n",res1)

# res2 = test_error()
# print("-*-"*12, "\n","res2\n", res2)
res3 = test_error2()
print("-*-"*12, "\n","res3\n", res3)
print("error_status\n", error_status)
