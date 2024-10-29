from typing import Never

def raise_value_error_if_absent(*args) -> Never:
    """
    Take a list of arguments and raise a Value Error if any of them are absent.
    TODO Fix this, for some reason it throws an error saying its a string and not a list???
    """
    pass
    # args_list = [arg for arg in args]
    # if not all(args_list):
    #     args = " ,".join(args_list)
    #     raise ValueError(f"{args} must be provided.")