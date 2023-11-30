import re
from http.cookiejar import MozillaCookieJar

import cloudscraper
from bs4 import BeautifulSoup
from requests.cookies import RequestsCookieJar

from src.url_manager import UrlManager


class Shoot(UrlManager):

    def __init__(
            self,
            number: str | int | None = None,
            href: str | None = None,
            cookie: MozillaCookieJar | RequestsCookieJar = None
    ) -> None:
        super().__init__(UrlManager.HttpType.HTTPS, 'www.kink.com')

        self.number = None
        if href and number:
            raise Exception("you cannot specify both href and number, choose only one!")

        if number:
            self.set_number(number)
        if href:
            self.set_number_from_href(href)

        if not cookie:
            raise Exception("cookie must be provided!")
        self.cookie = cookie

    def set_number(self, number: str | int):
        if isinstance(number, int):
            self.number = str(number)
        elif isinstance(number, str):
            self.number = number

        self.segments = ['shoot', self.number]

    def set_number_from_href(self, href: str):
        pattern = r'^(/)?shoot/\d+$'
        match = re.fullmatch(pattern, href)
        if not match:
            raise Exception("href is invalid! must be in format /shoot/[shoot number]")
        self.segments = [s for s in href.split('/') if s]

    def get_data_from_soup(self):
        session = cloudscraper.CloudScraper()
        req = session.get(self.get_url(), cookies=self.cookie)
        soup = BeautifulSoup(req.text, "html.parser")
