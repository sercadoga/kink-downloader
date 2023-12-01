import os.path
import re
from datetime import datetime
from http.cookiejar import MozillaCookieJar

import cloudscraper
from bs4 import BeautifulSoup
from requests.cookies import RequestsCookieJar

from src.files.poster import Poster
from src.files.video import Video
from src.files.zip_file import ZipFile
from src.utility.url_manager import UrlManager
from src.website.model import Model


class Shoot(UrlManager):

    def __init__(
            self,
            number: str | int | None = None,
            href: str | None = None,
            cookie: MozillaCookieJar | RequestsCookieJar = None,
            path: str | None = None
    ) -> None:
        super().__init__(UrlManager.HttpType.HTTPS, 'www.kink.com')

        self.session = None
        self.soup = None
        self.path = path

        # internal value
        self.number: str | None = None
        self.title: str | None = None
        self.description: str | None = None
        self.videos: list[Video] | None = None
        self.poster: Poster | None = None
        self.zip_image: ZipFile | None = None
        self.actors: list[Model] | None = None
        self.tags: list[str] | None = None
        self.director: str | None = None
        self.channel: str | None = None
        self.release_date: str | None = None

        if not os.path.exists(self.path):
            raise FileNotFoundError(f'directory {self.path} does not exist')

        if href and number:
            raise Exception("you cannot specify both href and number, choose only one!")

        if number:
            self.set_number(number)
        if href:
            self.set_number_from_href(href)

        if not cookie:
            raise Exception("cookie must be provided!")
        self.cookie = cookie
        self.get_data_from_soup()

        print(f"shoot: {self.__str__()}")

    @property
    def best_video(self) -> Video:
        return max((v for v in self.videos), key=lambda v: int(v.quality))

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
        self.number = self.segments[-1]

    def get_data_from_soup(self):
        self.session = cloudscraper.CloudScraper()
        req = self.session.get(self.get_url(), cookies=self.cookie)
        self.soup = BeautifulSoup(req.text, "html.parser")
        self.title = self.soup.find('h1', 'shoot-title').get_text().replace('\n\ue800\n', '')
        self.videos = [Video(val.get('download'), self.number, val.get('quality'), self.path)
                       for val in self.soup.find_all('a', download=True, quality=True)]
        self.poster = Poster(
            self.soup.find('video', poster=True).get('poster'),
            self.number,
            self.best_video.quality, self.path
        )
        self.zip_image = ZipFile(
            self.soup.find('a', 'zip-links', download=True).get('download'),
            self.number,
            self.best_video.quality, self.path
        )

        # todo actors

    def __str__(self) -> str:
        return f'<Shoot: {self.number:0>8}:{self.title:_>70}>'

    __repr__ = __str__

    def download_best(self):
        self.best_video.download()
        self.poster.download()

    def get_data_for_datatable(self):
        video = self.best_video
        return {
            'number': self.number,
            'title': self.title,
            'description': self.description,
            'quality': video.quality,
            'video': video.url,
            'poster': self.poster,
            'zip_image': self.zip_image,
        }
