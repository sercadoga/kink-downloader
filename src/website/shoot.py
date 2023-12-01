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


class Shoot(UrlManager):

    def __init__(
            self,
            number: str | int | None = None,
            href: str | None = None,
            cookie: MozillaCookieJar | RequestsCookieJar = None,
            path: str | None = None
    ) -> None:
        super().__init__(UrlManager.HttpType.HTTPS, 'www.kink.com')

        self.best_metadata = None
        self.session = None
        self.soup = None
        self.title = None
        self.number = None
        self.videos: list[Video] | None = None
        self.best_video: Video | None = None
        self.best_poster = None
        self.zip_image = None
        self.path = path

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
        self.best_video = max((v for v in self.videos), key=lambda v: int(v.quality))
        self.best_poster = Poster(
            self.soup.find('video', poster=True).get('poster'),
            self.number,
            self.best_video.quality, self.path
        )
        self.zip_image = ZipFile(
            self.soup.find('a', 'zip-links', download=True).get('download'),
            self.number,
            self.best_video.quality, self.path
        )

        self.best_metadata = self.get_metadata()
        # todo actors

    def __str__(self) -> str:
        return f'<Shoot: {self.number:0>8}:{self.title:_>70}>'

    __repr__ = __str__

    def get_metadata(self):
        """
        Parse src for shoot metadata.
        """
        title = self.soup.find("h1", "shoot-title").get_text(strip=True)[:-1]

        desc = self.soup.find("span", "description-text")
        desc = desc.find("p")
        if desc is None:
            desc = "No Desription Available"
        else:
            desc = desc.get_text()

        shoot_date = self.soup.find("span", "shoot-date")
        shoot_date = datetime.strptime(shoot_date.get_text(), '%B %d, %Y')
        shoot_date = shoot_date.strftime("%Y-%m-%d")

        actors = []
        genres = []
        actor_thumbs = []

        for actors_tag in self.soup.find_all("span", "names h5"):
            for bio in actors_tag.find_all("a"):
                name = bio.get_text().replace(',', '').strip()
                actors.append(name)
                bio_url = "https://www.kink.com" + bio.attrs['href']
                bio_page = BeautifulSoup(self.session.get(bio_url).text, "html.parser")

                if bio_page.find("img", "bio-slider-img") is None:
                    if bio_page.find("img", "bio-img") is None:
                        img = "https://cdnp.kink.com/imagedb/43869/i/h/410/16.jpg"
                    else:
                        img = bio_page.find("img", "bio-img").attrs['src']
                else:
                    img = bio_page.find("img", "bio-slider-img").attrs['src']
                actor_thumbs.append(img)

        for tag in self.soup.find_all("a", "tag"):
            g = tag.get_text().replace(',', '').strip()
            genres.append(g)

        metadata = {"title": title,
                    "description": desc,
                    "releasedate": shoot_date,
                    "genres": genres,
                    "actors": actors,
                    "actor_thumbs": actor_thumbs}
        return metadata

    def download_best(self):
        self.best_video.download()
        self.best_poster.download()
