import asyncio
from collections import defaultdict
import datetime
from dataclasses import dataclass
from typing import Dict, Callable, Any

@dataclass
class CacheEntry:
    t: datetime.datetime
    contents: Any

    def is_obsolete(self, current_time, timeout: int):
        return current_time > self.t + datetime.timedelta(seconds=timeout)

cache_contents: Dict[Callable[[], Any], CacheEntry] = {}
cache_locks = defaultdict(lambda: asyncio.Lock())

async def cache_force_add(function, current_time):
    contents = await function()
    cache_contents[function] = CacheEntry(current_time, contents)
    return contents

async def simple_cache(function, timeout: int=3):
    # if one job is currently executing the function, wait for it to finish
    async with cache_locks[function]:
        current_time = datetime.datetime.now()
        if function not in cache_contents.keys():
            return await cache_force_add(function, current_time)

        cache_entry = cache_contents[function]
        
        if cache_entry.is_obsolete(current_time, timeout):
            return await cache_force_add(function, current_time)

        return cache_entry.contents