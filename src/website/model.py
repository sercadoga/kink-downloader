from src.utility.url_manager import UrlManager


class Model(UrlManager):

    def __init__(self, href: str | list[str]):
        super().__init__(UrlManager.HttpType.HTTPS, 'www.kink.com', segments=href)
