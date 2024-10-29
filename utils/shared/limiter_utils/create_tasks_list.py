from typing import Any, Callable, Coroutine

import pandas as pd

async def create_tasks_list(inputs: Any, func: Callable, enum: bool, *args, **kwargs) -> list[Coroutine[Any, Any, Any]]:

    if isinstance(inputs, (list,set,tuple)):
        if enum:
            coroutine_list = [func(idx, inp, *args, **kwargs) for idx, inp in enumerate(inputs, start=1)]
        else:
            coroutine_list = [func(1, inp, *args, **kwargs) for inp in inputs]

    elif isinstance(inputs, dict):
        if enum:
            coroutine_list = [func(idx, (key, value), *args, **kwargs) for idx, (key, value) in enumerate(inputs.items(), start=1)]
        else:
            coroutine_list = [func(1, (key, value), *args, **kwargs) for key, value in inputs.items()]

    elif isinstance(inputs, pd.DataFrame):
        if enum:
            coroutine_list = [func(idx, row, *args, idx=idx, **kwargs) for idx, row in enumerate(inputs.itertuples(), start=1)]
        else:
            coroutine_list = [func(1, row, *args, **kwargs) for row in inputs.itertuples()]

    else:
        raise ValueError(f"Argument 'inputs' has an unsupported type '{type(inputs)}'")
    return coroutine_list