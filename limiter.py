import os
from slowapi import Limiter
from slowapi.util import get_remote_address

def _is_rate_limiting_enabled() -> bool:
    val = os.getenv("ENABLE_RATE_LIMITING", "true").strip().lower()
    return val not in {"false", "0", "off", "disable", "disabled"}

limiter = Limiter(key_func=get_remote_address, enabled=_is_rate_limiting_enabled())
