from typing import Never

def raise_value_error_if_absent(*args) -> Never:
    """
    Take a list of arguments and raise a Value Error if any of them are absent.
    """
    args = [*args]
    if not all(args):
        args = " ,".join(args)
        raise ValueError(f"{args} must be provided.")