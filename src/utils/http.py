"""Minimal HTTP client built on urllib to avoid external dependencies."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, Optional


@dataclass
class HttpResponse:
    status_code: int
    headers: Mapping[str, str]
    content: bytes

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="ignore")

    def json(self) -> Any:
        return json.loads(self.text) if self.content else {}

    def raise_for_status(self) -> None:
        if 400 <= self.status_code:
            raise urllib.error.HTTPError(
                url="", code=self.status_code, msg=self.text, hdrs=None, fp=None
            )


class HttpSession:
    """A tiny subset of the requests.Session API."""

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        data: Optional[Mapping[str, Any]] = None,
        json_body: Any = None,
        headers: Optional[MutableMapping[str, str]] = None,
        timeout: float | None = None,
    ) -> HttpResponse:
        method = method.upper()
        headers = {**(headers or {})}
        data_bytes: Optional[bytes] = None

        if params:
            query = urllib.parse.urlencode({k: _stringify(v) for k, v in params.items()})
            separator = "&" if urllib.parse.urlparse(url).query else "?"
            url = f"{url}{separator}{query}"

        if json_body is not None:
            data_bytes = json.dumps(json_body).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
        elif data is not None:
            data_bytes = urllib.parse.urlencode({k: _stringify(v) for k, v in data.items()}).encode("utf-8")
            headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

        request = urllib.request.Request(url=url, data=data_bytes, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout or 10) as response:
                return HttpResponse(
                    status_code=response.getcode(),
                    headers=dict(response.info()),
                    content=response.read(),
                )
        except urllib.error.HTTPError as exc:
            return HttpResponse(
                status_code=exc.code,
                headers=dict(exc.headers or {}),
                content=exc.read() if exc.fp else b"",
            )


def _stringify(value: Any) -> str:
    if isinstance(value, (list, tuple, set)):
        return ",".join(str(item) for item in value)
    return str(value)
