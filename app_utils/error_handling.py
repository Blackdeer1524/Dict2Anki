import sys
import traceback


def create_exception_message():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    return ''.join(lines)


def error_handler(error_processing=None):
    def error_decorator(func):
        def method_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if error_processing is None:
                    error_log = create_exception_message()
                    print(error_log)
                else:
                    error_processing(*args, exception=e, **kwargs)
        return method_wrapper
    return error_decorator


