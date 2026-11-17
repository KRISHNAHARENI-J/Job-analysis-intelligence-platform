import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv


class APIClientError(RuntimeError):
    pass


load_dotenv()


def _api_base_url() -> str:
    configured = os.getenv("API_BASE_URL", "http://127.0.0.1:8001").strip().rstrip("/")
    return configured if "://" in configured else f"https://{configured}"


def api_request(
    path: str,
    *,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = f"{_api_base_url()}{path}"
    if params:
        url = f"{url}?{urlencode(params, doseq=True)}"
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=headers, method=method)

    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            error_body = json.loads(exc.read().decode("utf-8"))
            detail = error_body.get("detail", str(exc))
        except (UnicodeDecodeError, json.JSONDecodeError):
            detail = str(exc)
        raise APIClientError(f"API request failed: {detail}") from exc
    except URLError as exc:
        raise APIClientError(
            f"Cannot reach the API at {_api_base_url()}. "
            "Start the API locally or set API_BASE_URL to its deployed URL."
        ) from exc
