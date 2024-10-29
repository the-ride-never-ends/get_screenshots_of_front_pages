"""
A decorator that wraps a function or coroutine in a try-except block with optional retries and exception raising.

This decorator allows you to automatically handle exceptions for a function,
with the ability to specify the number of retry attempts and whether to
ultimately raise the exception or not.

NOTE: 'Exception' is automatically added to the exception argument list if not specified.

Args:
    exception (list): A tuple of exception types to catch. Defaults to [Exception].
    raise_exception (bool): If True, raises the caught exception after all retries
                            have been exhausted. If False, suppresses the exception.
                            Defaults to False.
    retries (int): The number of times to retry the function if an exception occurs.
                    If None, the function will only be attempted once. Defaults to None.
    logger (logging.Logger): A logger instance. Defaults to None.

Returns:
    function: A decorated function or coroutine that implements the try-except logic.

Example:
>>> # Synchronous example
>>> @try_except(exception=[ValueError, TypeError], raise_exception=True, retries=3)
>>> def test_func(x):
>>>     return x / 0 
>>> test_func(-1)
ERROR:__main__:ValueError exception in 'test_func': x cannot be negative
Retrying (0/3)...
>>> # Asynchronous example
>>> @try_except(exception=[ValueError, TypeError], raise_exception=True, retries=3, async_=True)
>>> async def test_func(x):
>>>     return await x / 0
>>> await test_func(-1)
ERROR:__main__:ValueError exception in 'test_func': x cannot be negative
Retrying (0/3)...
"""

from functools import wraps
import inspect
import sys
from typing import Any, Callable, Coroutine


from logger.logger import Logger


def async_try_except(exception: list=[Exception],
                    raise_exception: bool=False,
                    retries: int=0,
                    logger: Logger=None,
                    ) -> Callable:
    """
    A decorator that wraps a coroutine in a try-except block with optional retries and exception raising.

    This decorator allows you to automatically handle exceptions for a function,
    with the ability to specify the number of retry attempts and whether to
    ultimately raise the exception or not.

    NOTE: 'Exception' is automatically added to the exception argument list if not specified.

    Args:
        exception (list): A tuple of exception types to catch. Defaults to [Exception].
        raise_exception (bool): If True, raises the caught exception after all retries
                                have been exhausted. If False, suppresses the exception.
                                Defaults to False.
        retries (int): The number of times to retry the function if an exception occurs.
                       If None, the function will only be attempted once. Defaults to None.
        logger (logging.Logger): A logger instance. Defaults to None.

    Returns:
        function: A decorated coroutine that implements the try-except logic.

    Example:
    >>> @async try_except(exception=[ValueError, TypeError], raise_exception=True, retries=3)
    >>> async def test_func(x):
    >>>     await asyncio.sleep(1)
    >>>     return x / 0 
    >>> await test_func(-1)
    ERROR:__main__:ValueError exception in 'test_func': x cannot be negative
    Retrying (0/3)...
    """
    def decorator(func: Coroutine) -> Coroutine:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:

            # Initialize Logger and other variables.
            # NOTE See: https://stackoverflow.com/questions/1261875/what-does-nonlocal-do-in-python-3
            nonlocal logger
            logger = logger or Logger(logger_name=func.__module__, stacklevel=3)
            attempts = 0
            finally_e = None

            # Since we don't want any uncaught exceptions
            # We add in Exception to the input exception list 
            # if it's not specified in it.
            exception_list = list(exception)
            if Exception not in exception_list:
                exception_list.extend([Exception])
            exception_tuple = tuple(exception_list)

            # Determine if func is a method and prepare to use __exit__ or __aexit__ if it is.
            if inspect.ismethod(func):
                instance = args[0]  # Get the class instance (self)
                exit_context: Coroutine = getattr(instance, '__aexit__', None)
                if not exit_context:
                    logger.warning(f"{func.__name__} is a method, but the class does not have an __exit__ or __aexit__ method.")
            else:
                exit_context = None

            try:
                while attempts <= retries:
                    # Try the function.
                    try:
                        return await func(*args, **kwargs)
                    except exception_tuple as e:
                        # Define error variables
                        error_name: str = e.__class__.__name__
                        func_name = func.__name__
                        error_message = f"{error_name} exception in '{func_name}'\n{e}"
                        retry_message = f"Retrying ({attempts}/{retries})..."

                        # If no retries are specified, log the error and set the finally_e variable to the Exception.
                        if retries <= 0: 
                            logger.exception(error_message)
                            finally_e: Exception = e
                            break
                        else:
                            # On first attempt, print the error and retry message
                            if attempts <= 0: 
                                print(error_message)
                                print(retry_message)

                            # On subsequent attempts, print the retry message.
                            elif attempts > 0 and attempts < retries: 
                                print(retry_message)

                            # On the final attempt, log the error and set the finally_e variable to the Exception.
                            else: 
                                print(f"Function '{func_name}' errored after {attempts + 1} retries.")
                                logger.exception(f"{error_message}\nretries: {attempts + 1}")
                                finally_e: Exception = e
                                break
                            attempts += 1
            finally:
                # Raise the exception if requested.
                if raise_exception:
                    if finally_e: # Should only trigger if no retries were specified or if all of them are exhauseted.
                        if exit_context: # Handle the call to __aexit__ if the method has it
                            exception_info = sys.exc_info()
                            await exit_context(exception_info[0], exception_info[1], exception_info[2])
                        raise finally_e
        return wrapper
    return decorator


def try_except(exception: list=[Exception],
               raise_exception: bool=False,
               retries: int=0,
               logger: Logger=None,
               ) -> Callable:
    """
    A decorator that wraps a function in a try-except block with optional retries and exception raising.

    This decorator allows you to automatically handle exceptions for a function,
    with the ability to specify the number of retry attempts and whether to
    ultimately raise the exception or not.

    NOTE: 'Exception' is automatically added to the exception argument list if not specified.
    TODO: Figure out how to make this take coroutines as well

    Args:
        exception (list): A tuple of exception types to catch. Defaults to [Exception].
        raise_exception (bool): If True, raises the caught exception after all retries
                                have been exhausted. If False, suppresses the exception.
                                Defaults to False.
        retries (int): The number of times to retry the function if an exception occurs.
                       If None, the function will only be attempted once. Defaults to None.
        logger (logging.Logger): A logger instance. Defaults to None.

    Returns:
        function: A decorated function or coroutine that implements the try-except logic.

    Example:
    >>> @try_except(exception=[ValueError, TypeError], raise_exception=True, retries=3)
    >>> def test_func(x):
    >>>     return x / 0 
    >>> test_func(-1)
    ERROR:__main__:ValueError exception in 'test_func': x cannot be negative
    Retrying (0/3)...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:

            # Initialize Logger and other variables.
            # NOTE See: https://stackoverflow.com/questions/1261875/what-does-nonlocal-do-in-python-3
            nonlocal logger
            logger = logger or Logger(logger_name=func.__module__, stacklevel=3)
            attempts = 0
            finally_e = None

            # Since we don't want any uncaught exceptions
            # We add in Exception to the input exception list 
            # if it's not specified in it.
            exception_list = list(exception)
            if Exception not in exception_list:
                exception_list.extend([Exception])
            exception_tuple = tuple(exception_list)


            def get_method_type(cls, method_name):
                method = getattr(cls, method_name)
                
                if inspect.ismethod(method):
                    if method.__self__ is cls:
                        return "class method"
                    else:
                        return "instance method"
                elif inspect.isfunction(method):
                    return "static method"
                else:
                    return "not a method"

            # Determine if func is a method and prepare to use __exit__ or __aexit__ if it is.
            if inspect.ismethod(func):
                instance = args[0]  # Get the class instance (self)
                exit_context: Callable = getattr(instance, '__exit__', None)
                if not exit_context:
                    logger.warning(f"{func.__name__} is a method, but the class does not have an __exit__ method.")
            else:
                exit_context = None

            try:
                while attempts <= retries:
                    # Try the function.
                    try:
                        return func(*args, **kwargs)
                    except exception_tuple as e:
                        # Define error variables
                        error_name: str = e.__class__.__name__
                        func_name = func.__name__
                        error_message = f"{error_name} exception in '{func_name}'\n{e}"
                        retry_message = f"Retrying ({attempts}/{retries})..."

                        # If no retries are specified, log the error and raise it if requested.
                        if retries <= 0: 
                            logger.exception(error_message)
                            finally_e: Exception = e
                            break
                        else:
                            # On first attempt, print the error and retry message
                            if attempts <= 0: 
                                print(error_message)
                                print(retry_message)

                            # On subsequent attempts, print the retry message.
                            elif attempts > 0 and attempts < retries: 
                                print(retry_message)

                            # On the final attempt, log the error and raise it if requested.
                            else: 
                                print(f"Function '{func_name}' errored after {attempts + 1} retries.")
                                logger.exception(f"{error_message}\nretries: {attempts + 1}")
                                finally_e: Exception = e
                                break
                            attempts += 1
            finally:
                # Raise the exception if requested.
                if raise_exception:
                    if finally_e:
                        if exit_context: # Handle the call to __exit__ if the method has it
                            exception_info = sys.exc_info()
                            exit_context(exception_info[0], exception_info[1], exception_info[2])
                        raise finally_e
                else:
                    pass
        return wrapper
    return decorator
