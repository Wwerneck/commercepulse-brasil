import logging
from collections.abc import Mapping
from time import sleep
from typing import Any

import requests

logger = logging.getLogger(__name__)


class HttpRequestError(RuntimeError):
    """Raised when an HTTP request fails after retries."""


def get_json(
    url: str,
    params: Mapping[str, Any] | None = None,
    timeout: int = 30,
    retries: int = 3,
) -> Any:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            logger.warning("request_failed attempt=%s url=%s error=%s", attempt + 1, url, exc)
            if attempt < retries:
                sleep(min(2**attempt, 8))
    raise HttpRequestError(f"GET {url} failed after {retries + 1} attempts") from last_error
