from typing import Any

import streamlit as st

from dashboard_client import APIClientError, api_request


def fetch_api(
    path: str,
    *,
    params: dict[str, Any] | None = None,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        return api_request(path, method=method, params=params, payload=payload)
    except APIClientError as exc:
        st.error(str(exc))
        st.stop()
        raise
