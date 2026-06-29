from errGuard.errDecorator import intercept
from errGuard.tools import traceback_info, ErrorInfo, get_last_traceback_info
import sys
import traceback
from loguru import logger

error_decorator = intercept(error_debug=False, error_response=None, error_key="elfinError")


class MatchError(Exception): ...


@error_decorator
class Elfin:

    class_name = "Elfin"

    def __call__(self, num, **kwargs):
        if num < 10:
            raise MatchError(f"Num: {num} should be greater than 10.")
        else:
            raise KeyError(f"Num: {num} should be less than 10.")


elfin = Elfin()
try:
    res = elfin(25)
except Exception as e:
    infos = traceback_info(e)
    # traceback.print_list(infos, file=sys.stdout)
    # traceback.print_exception(type(e), e, e.__traceback__, file=sys.stdout)
    print(get_last_traceback_info(e))
    logger.exception("Error occurred in Elfin class.")
    print("logger exception 测试")


print(res)
