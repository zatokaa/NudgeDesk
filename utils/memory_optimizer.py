"""Windows memory optimization utility to keep RAM usage ultra-low."""

import os
import gc
import ctypes
from utils.logger import logger

PROCESS_SET_QUOTA = 0x0100
PROCESS_QUERY_INFORMATION = 0x0400

def trim_memory() -> None:
    """
    Performs generational garbage collection and requests Windows kernel
    to trim the working set pages. This drops RAM footprint down to ~5-20 MB.
    """
    try:
        # 1. Python GC
        gc.collect()

        # 2. Windows Working Set Trim
        pid = os.getpid()
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_SET_QUOTA | PROCESS_QUERY_INFORMATION,
            False,
            pid
        )
        if handle:
            ctypes.windll.psapi.EmptyWorkingSet(handle)
            ctypes.windll.kernel32.CloseHandle(handle)
            logger.debug("Memory trimmed successfully.")
    except Exception as e:
        logger.debug(f"Memory trim skipped: {e}")

