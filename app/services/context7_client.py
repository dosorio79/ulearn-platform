"""Context7 API client for documentation snippets."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

_BASE_URL = "https://context7.com/api/v2"
_TIMEOUT_SECONDS = 4


def fetch_context_snippets(
    *,
    api_key: str,
    library_name: str,
    query: str,
) -> list[dict[str, Any]]:
    """Fetch documentation snippets for a library query."""
    library = _search_library(api_key=api_key, library_name=library_name, query=query)
    if not library:
        return []
    library_id = library.get("id")
    if not library_id:
        return []
    return _get_context(api_key=api_key, library_id=library_id, query=query)


def _search_library(*, api_key: str, library_name: str, query: str) -> dict[str, Any] | None:
    params = urllib.parse.urlencode({"libraryName": library_name, "query": query})
    url = f"{_BASE_URL}/libs/search?{params}"
    data = _request_json(url, api_key)
    if not isinstance(data, list) or not data:
        return None
    return data[0]


def _get_context(*, api_key: str, library_id: str, query: str) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"libraryId": library_id, "query": query})
    url = f"{_BASE_URL}/context?{params}"
    data = _request_json(url, api_key)
    if isinstance(data, list):
        return data
    return []


def _request_json(url: str, api_key: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)
