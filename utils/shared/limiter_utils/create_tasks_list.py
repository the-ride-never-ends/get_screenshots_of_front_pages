from typing import Any, Callable, Coroutine

import pandas as pd

async def create_tasks_list(inputs: Any, func: Callable, enum: bool, *args, **kwargs) -> list[Coroutine[Any, Any, Any]]:

    if isinstance(inputs, (list,set,tuple)):
        if enum:
            return [func(idx, inp, *args, **kwargs) for idx, inp in enumerate(inputs)]
        else:
            return [func(inp, *args, **kwargs) for inp in inputs]

    elif isinstance(inputs, dict):
        if enum:
            return [func(idx, (key, value), *args, **kwargs) for idx, (key, value) in enumerate(inputs.items())]
        else:
            return [func((key, value), *args, **kwargs) for key, value in inputs.items()]

    elif isinstance(inputs, pd.DataFrame):
        if enum:
            return [func(idx, row, *args, **kwargs) for idx, row in enumerate(inputs.itertuples())]
        else:
            return [func(row, *args, **kwargs) for row in inputs.itertuples()]

    else:
        raise ValueError(f"Argument 'inputs' has an unsupported type '{type(inputs)}'")