from src.files.poster import Poster
from src.utility.url_manager import UrlManager


class Model(UrlManager):

    def __init__(self, href: str | list[str]):
        super().__init__(UrlManager.HttpType.HTTPS, 'www.kink.com', segments=href)
        self.name: str | None = None
        self.description: str | None = None
        self.tag: list[str] | None = None
        self.poster: Poster | None = None
