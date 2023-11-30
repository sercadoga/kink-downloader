from enum import Enum
from typing import LiteralString


class UrlManager:
    class HttpType(Enum):
        HTTP = "http"
        HTTPS = "https"

    def __init__(
            self,
            schema: HttpType, base_url: str,
            segments: list[str | LiteralString] | str = None,
            query_param: dict[str, str] = None
    ):
        self.schema = schema
        self.base_url = base_url
        if isinstance(segments, str):
            self.segments = [s for s in segments.split('/') if s]
        elif isinstance(segments, list):
            self.segments = segments or []
        self.query_param = query_param or dict()

    def __str__(self):
        return f'<UrlManager: {self.get_url()}>'

    __repr__ = __str__

    def add_query_param(self, key: str, value: str):
        self.query_param[key] = value

    def add_segment(self, value: str | list[str]):
        if isinstance(value, list):
            self.segments = [*self.segments, *value]
        elif isinstance(value, str):
            self.segments.append(value)

        raise Exception("value is not a list or str")

    def set_page(self, value: str):
        self.query_param['page'] = value

    def get_url(self):
        segments = '/'.join(self.segments) if self.segments else ""
        query_param = '?' + "&".join([F"{key}={value}" for key, value in self.query_param.items()]) if len(
            self.query_param) > 0 else ""
        return f"{self.schema.value}://{self.base_url}/{segments}/{query_param}"
