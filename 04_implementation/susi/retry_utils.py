
"""
retry_utils.py: Provides a generic retry decorator with exponential backoff for robust error handling.

Features:
    - Retry any function on specified exceptions, with exponential backoff.
    - Configurable number of tries, delay, and backoff multiplier.
    - Logs warnings or prints to stdout if logger is not provided.

Developer hints:
    - Use @retry on functions that call unreliable external services (APIs, network, etc).
    - Pass a logger for structured logging, or leave as None for stdout.
    - Use specific exception types to avoid retrying on programming errors.

Error/warning message hints:
    - If you see repeated retry warnings, check the underlying service or network.
    - If all retries fail, the last exception is raised to the caller.
    - Use logs to diagnose persistent failures.
"""

import time
import logging
from functools import wraps


from typing import Callable, Type, Optional, Any, Tuple, Union

def retry(
    ExceptionToCheck: Union[Type[BaseException], Tuple[Type[BaseException], ...]],
    tries: int = 3,
    delay: int = 1,
    backoff: int = 2,
    logger: Optional[logging.Logger] = None
) -> Callable:
    """
    Decorator for retrying a function call with exponential backoff on specified exceptions.

    Args:
        ExceptionToCheck (Exception or tuple): The exception(s) to check for retry.
        tries (int): Number of attempts before giving up.
        delay (int): Initial delay between retries in seconds.
        backoff (int): Multiplier applied to delay after each failure.
        logger (Optional[logging.Logger]): Logger to use for warnings. If None, prints to stdout.

    Returns:
        Callable: The decorated function with retry logic.

    Developer hints:
        - Use for functions that may fail transiently (e.g., network, API, I/O).
        - Set tries/delay/backoff based on expected failure/recovery time.
        - Use a logger for production, or None for quick scripts.

    Error/warning message hints:
        - If you see repeated retry warnings, check the underlying service or network.
        - If all retries fail, the last exception is raised to the caller.
        - Use logs to diagnose persistent failures.
    """
    def deco_retry(f: Callable) -> Callable:
        @wraps(f)
        def f_retry(*args, **kwargs) -> Any:
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    # Log or print the retry warning
                    msg = f"{f.__name__}: {str(e)}, Retrying in {mdelay} seconds... ({mtries-1} tries left)"
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            # Final attempt, will raise if it fails
            return f(*args, **kwargs)
        return f_retry
    return deco_retry
