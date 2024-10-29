import asyncio
from typing import Any, Coroutine


import pandas as pd


async def create_tasks_list_with_outer_task_name(inputs: Any, func: Coroutine, enum: bool, outer_task_name: str, *args, **kwargs) -> list[asyncio.Task]:

    if isinstance(inputs, (list,set,tuple)):
        if enum:
            return [
                asyncio.create_task(
                    func(idx, inp, *args, **kwargs), 
                    name=outer_task_name
                ) for idx, inp in enumerate(inputs)
            ]
        else:
            return [
                asyncio.create_task(
                    func(inp, *args, **kwargs), 
                    name=outer_task_name
                ) for inp in inputs
            ]

    elif isinstance(inputs, dict):
        if enum:
            return [
                asyncio.create_task(
                    func(idx, (key, value), *args, **kwargs), 
                    name=outer_task_name
                    ) for idx, (key, value) in enumerate(inputs.items())
                ]
        else:
            return [
                asyncio.create_task(
                    func((key, value), *args, **kwargs),
                    name=outer_task_name,
                    ) for (key, value) in inputs.items()
                ]

    elif isinstance(inputs, pd.DataFrame):
        if enum:
            return [
                asyncio.create_task(
                    func(idx, row, *args, **kwargs), 
                    name=outer_task_name
                ) for idx, row in enumerate(inputs.itertuples())
            ]
        else:
            return [
                asyncio.create_task(
                    func(row, *args, **kwargs), 
                    name=outer_task_name
                ) for row in inputs.itertuples()
            ]

    else:
        raise ValueError(f"Argument 'inputs' has an unsupported type '{type(inputs)}'")