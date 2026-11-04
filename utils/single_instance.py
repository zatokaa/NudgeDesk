"""Windows Single-Instance protection using Win32 Named Mutex and window activation."""

import ctypes
from ctypes import wintypes
from utils.logger import logger

ERROR_ALREADY_EXISTS = 183

class SingleInstanceChecker:
    """Ensures only a single instance of NudgeDesk is active on the system."""

    def __init__(self, mutex_name: str = "Local\\NudgeDesk_SingleInstance_Mutex"):
        self.mutex_name = mutex_name
        self.mutex_handle = None
        self._is_already_running = False

    def is_running(self) -> bool:
        """Checks if another instance is already holding the mutex."""
        kernel32 = ctypes.windll.kernel32
        
        # Create or open mutex
        self.mutex_handle = kernel32.CreateMutexW(None, False, self.mutex_name)
        last_error = kernel32.GetLastError()
        
        if last_error == ERROR_ALREADY_EXISTS:
            self._is_already_running = True
            logger.warning("Another instance of NudgeDesk is already running.")
            return True
        return False

    def activate_existing_window(self) -> bool:
        """Locates the running NudgeDesk window, un-hides it, restores it, and brings it to the front."""
        try:
            user32 = ctypes.windll.user32
            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            SW_RESTORE = 9
            SW_SHOW = 5

            target_hwnds = []
            def _enum_windows_callback(hwnd, lparam):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    if "NudgeDesk" in buff.value:
                        target_hwnds.append(hwnd)
                return True

            user32.EnumWindows(WNDENUMPROC(_enum_windows_callback), 0)
            if target_hwnds:
                hwnd = target_hwnds[0]
                user32.ShowWindow(hwnd, SW_RESTORE)
                user32.SetForegroundWindow(hwnd)
                return True
        except Exception as e:
            logger.debug(f"Could not activate existing window: {e}")
        return False

    def release(self) -> None:
        """Releases the mutex handle upon exit."""
        if self.mutex_handle:
            ctypes.windll.kernel32.CloseHandle(self.mutex_handle)
            self.mutex_handle = None
