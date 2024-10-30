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
                    func_finally: Callable|Coroutine=None,
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
            async with TryExcept(func, 
                                 exception=exception, 
                                 raise_exception=raise_exception, 
                                 retries=retries, 
                                 logger=logger, 
                                 ) as te:
                te.check_for_context_manager(func, args)
            return await te.async_try_except(*args, **kwargs)
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
    def decorator(func: Coroutine) -> Coroutine:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with TryExcept(func, 
                            exception=exception, 
                            raise_exception=raise_exception, 
                            retries=retries, 
                            logger=logger,
                            ) as te:
                te.check_for_context_manager(func, args)
            return te.try_except(*args, **kwargs)
        return wrapper
    return decorator


class TryExcept:
    def __init__(self,
                func: Callable|Coroutine, 
                exception: list = [Exception], 
                raise_exception: bool = False, 
                retries: int = 0, 
                logger: Logger = None,
                ) -> None:
        self.exception = exception or [Exception]
        self.raise_exception = raise_exception or False
        self.retries = max(0, retries)  # Ensure non-negative
        self.logger = logger or Logger(logger_name=func.__module__, stacklevel=4)
        # Create the exception tuple.
        self.exception_tuple = self._make_exception_tuple_from_exception_list()

        self.attempts: int = 0
        self.finally_e: Exception = None
        self.exit_context: Callable|Coroutine = None
        self.func: Callable|Coroutine = None
        self.func_name: str = None

    @classmethod
    def start(cls, *args, **kwargs) -> 'TryExcept':
        instnace = cls(*args, **kwargs)
        return instnace

    def stop() -> None:
        return

    def __enter__(self) -> 'TryExcept':
        return self

    def __exit__(self) -> None:
        return
 
    async def __aenter__(self) -> 'TryExcept':
        return await self

    async def __aexit__(self) -> None:
        return

    def _make_exception_tuple_from_exception_list(self) -> tuple[Exception]:
        """
        Since we don't want any uncaught exceptions
        We add in Exception to the input exception list 
        if it's not specified in it.
        NOTE try-except statements expect tuples as the exception iterable.
        """
        exception_set = set(self.exception)
        exception_set.add(Exception)
        return tuple(exception_set)

    def check_for_context_manager(self, func: Callable|Coroutine, args: tuple) -> None:
        """
        Determine if the wrapped function is a method and prepare to use __exit__ or __aexit__ if it is.
        Finally, assign it to the class.
        """
        if not args:
            return

        if inspect.ismethod(func):
            instance = args[0]  # Get the class instance (self)
            exit_context_func = '__aexit__' if inspect.iscoroutinefunction(self.func) else '__exit__'
            self.exit_context = getattr(instance, exit_context_func, None)
            if self.exit_context is None:
                self.logger.warning(f"{func.__name__} is a method, but the class does not have an __exit__ or __aexit__ method.")
        # We assign func here because inspect won't identify it as a function otherwise
        self.func = func


    def retry_logic(self, e: Exception) -> None:
        """
        Handle the retry logic for exceptions caught during the wrapped function's execution.

        Args:
            e (Exception): The exception that was caught.

        Returns:
            bool: True if the retry logic should break (either due to no more retries
                  or the final attempt), False if another retry should be attempted.
        """
        # Define error messages
        error_message = f"{e.__class__.__name__} exception in '{self.func.__name__}'\n{e}"
        retry_message = f"Retrying ({self.attempts}/{self.retries})..."
    
        # If no retries are specified, log the error and set the finally_e variable to the Exception.
        if self.retries <= 0:
            self.logger.exception(error_message)
            self.finally_e = e
            return True

        # On first attempt, print the error and retry message.
        if self.attempts == 0:
            # NOTE We don't log anything but the final error, but we still want the user to see the attempts.
            print(error_message)
            print(retry_message)

        # On subsequent attempts, print the retry message.
        elif self.attempts < self.retries:
            print(retry_message)

        # On the final attempt, log the error and set the finally_e variable to the Exception.
        else:
            print(f"Function '{self.func.__name__}' errored after {self.attempts + 1} retries.")
            self.logger.exception(f"{error_message}\nretries: {self.attempts + 1}")
            self.finally_e: Exception = e
            return True

        self.attempts += 1
        return False


    async def async_try_except(self, *args, **kwargs) -> Any:
        try:
            while self.attempts <= self.retries:
                try:
                    return await self.func(*args, **kwargs)
                except self.exception_tuple as e:
                    if not self.retry_logic(e):
                        break
        finally:
            if self.raise_exception and self.finally_e: # Should only trigger if no retries were specified or if all of them are exhauseted.
                if self.exit_context and inspect.iscoroutinefunction(self.exit_context): # Handle the call to __aexit__ if the method has it
                    exec_info = sys.exc_info()
                    await self.exit_context(*exec_info)
                raise self.finally_e


    def try_except(self, *args, **kwargs) -> Any:
        try:
            while self.attempts <= self.retries:
                # Try the function.
                try:
                    return self.func(*args, **kwargs)
                except self.exception_tuple as e:
                    if not self.retry_logic(e):
                        break
        finally:
            if self.raise_exception and self.finally_e: # Should only trigger if no retries were specified or if all of them are exhauseted.
                if self.exit_context: # Handle the call to __exit__ if the method has it
                    exec_info = sys.exc_info()
                    self.exit_context(*exec_info)
                raise self.finally_e



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
            retries = retries or 0
            attempts = 0
            finally_e = None

            # Since we don't want any uncaught exceptions
            # We add in Exception to the input exception list 
            # if it's not specified in it.
            exception_list = list(exception)
            if Exception not in exception_list:
                exception_list.extend([Exception])
            exception_tuple = tuple(exception_list) # NOTE try-except statements expect tuples as the exception iterable.

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
                            # NOTE We don't want to log the error here because we're going to retry.
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
