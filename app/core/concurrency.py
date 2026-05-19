"""Concurrency helpers for isolating blocking work from async endpoints."""

from collections.abc import Callable
from typing import Any, TypeVar

from starlette.concurrency import run_in_threadpool


ResultT = TypeVar("ResultT")


async def run_blocking_io(
    func: Callable[..., ResultT],
    *args: Any,
    **kwargs: Any,
) -> ResultT:
    return await run_in_threadpool(func, *args, **kwargs)
