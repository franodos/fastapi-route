# -*- coding:utf-8 -*-

import json
import typing
import http.cookies
from starlette.background import BackgroundTask
from starlette.datastructures import MutableHeaders


class APIResponse(object):
    media_type = "application/json"
    charset = "utf-8"

    def __init__(
            self,
            *,
            content: typing.Any = None,
            status_code: int = 200,
            headers: dict = None,
            media_type: str = None,
            background: BackgroundTask = None,
    ):
        self.body = content
        self.status_code = status_code
        if media_type is not None:
            self.media_type = media_type
        self.background = background
        populate_content_length, populate_content_type = self.init_headers(headers)
        self.populate_content_length = populate_content_length
        self.populate_content_type = populate_content_type

    def init_headers(self, headers: typing.Mapping[str, str] = None):
        if headers is None:
            raw_headers = []  # type: typing.List[typing.Tuple[bytes, bytes]]
            populate_content_length = True
            populate_content_type = True
        else:
            raw_headers = [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in headers.items()]
            keys = [h[0] for h in raw_headers]
            populate_content_length = b"content-length" not in keys
            populate_content_type = b"content-type" not in keys
        self.raw_headers = raw_headers
        return populate_content_length, populate_content_type

    def populate_content(self):
        keys = self.headers.keys()
        if self.body and self.populate_content_length and "content-length" not in keys:
            body = getattr(self, "body", b"")
            self.headers["content-length"] = str(len(body))
        if self.populate_content_type and "content-type" not in keys:
            self.headers["content-type"] = self.media_type

    def render(self) -> bytes:
        return json.dumps(
            self.body,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

    @property
    def headers(self) -> MutableHeaders:
        if not hasattr(self, "_headers"):
            self._headers = MutableHeaders(raw=self.raw_headers)
        return self._headers

    def set_cookie(
            self,
            key: str,
            value: str = "",
            max_age: int = None,
            expires: int = None,
            path: str = "/",
            domain: str = None,
            secure: bool = False,
            httponly: bool = False,
    ) -> None:
        cookie = http.cookies.SimpleCookie()
        cookie[key] = value
        if max_age is not None:
            cookie[key]["max-age"] = max_age  # type: ignore
        if expires is not None:
            cookie[key]["expires"] = expires  # type: ignore
        if path is not None:
            cookie[key]["path"] = path
        if domain is not None:
            cookie[key]["domain"] = domain
        if secure:
            cookie[key]["secure"] = True  # type: ignore
        if httponly:
            cookie[key]["httponly"] = True  # type: ignore
        cookie_val = cookie.output(header="").strip()
        self.raw_headers.append((b"set-cookie", cookie_val.encode("latin-1")))

    def delete_cookie(self, key: str, path: str = "/", domain: str = None) -> None:
        self.set_cookie(key, expires=0, max_age=0, path=path, domain=domain)

    async def __call__(self, scope, receive, send) -> None:
        self.body = self.render()
        self.populate_content()
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
            }
        )
        await send({"type": "http.response.body", "body": self.body})

        if self.background is not None:
            await self.background()
