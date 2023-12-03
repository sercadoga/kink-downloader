import os.path
import re
from datetime import datetime
from http.cookiejar import MozillaCookieJar
from typing import TYPE_CHECKING

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
            path: str | None = None,
            cookie: MozillaCookieJar | RequestsCookieJar = None,
            session: cloudscraper.CloudScraper | None = None,
    ) -> None:
        super().__init__(UrlManager.HttpType.HTTPS, 'www.kink.com')
        from src.utility.factory import Factory
        self.factory = Factory(path, cookie, session)
        self.session = session
        self.soup = None
        self.path = path

        # internal value
        self.number: str | None = None
        self.title: str | None = None
        self.description: str | None = None
        self.videos: list[Video] | None = None
        self.poster: Poster | None = None
        self.zip_image: ZipFile | None = None
        self.models: list[Model] | None = None
        self.tags: list[str] | None = None
        # self.director: str | None = None
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
        self.dir_path = os.path.join(self.path, str(self.number))
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
        if os.path.exists(os.path.join(self.dir_path, 'data.json')):
            self.load_from_json()

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

        self.description = self.soup.select('.description-text > p:nth-child(1)')[0].get_text()

        # self.models = [Model(el.get('href'), self.cookie, self.session) for el in self.soup.select('.names > a')]
        self.models = [self.factory.get_model(el.get('href')) for el in self.soup.select('.names > a')]
        self.tags = [el.get_text() for el in self.soup.select('a.tag')]
        _director = [Model(el.get('href'), self.cookie, self.session) for el in self.soup.select('.director-name > a')]
        if _director:
            self.director = _director[0]
        text = self.soup.select('.shoot-date')[0].get_text()
        shoot_date = datetime.strptime(text, "%B %d, %Y")
        self.release_date = shoot_date.strftime("%Y-%m-%d")
        if data := self.soup.select('.shoot-logo > a:nth-child(1)'):
            self.channel = data[0].get('href').split('/')[-1]

    def __str__(self) -> str:
        return f'<Shoot: {self.number:0>8}:{self.title:_>70}>'

    __repr__ = __str__

    def download_best(self):
        os.makedirs(self.dir_path, exist_ok=True)
        print(f'Downloading {str(self)}')
        self.write_metadata_nfo(self.dir_path)
        # self.best_video.download()
        # self.poster.download()
        # self.zip_image.download()

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

    def write_metadata_nfo(self, fname):
        """
        Write metadata to emby compatible NFO file.
        """
        global shot_dir, shot_number
        fname = os.path.join(shot_dir, shot_number + ".nfo")
        with open(fname, "w") as nfo:
            nfo.write('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
            nfo.write("<movie>\n")
            nfo.write("  <plot>" + self.escape(self.description) + "</plot>\n")
            nfo.write("  <title>" + self.escape(self.title) + "</title>\n")
            nfo.write("  <releasedate>" + self.escape(self.release_date) +
                      "</releasedate>\n")
            nfo.write("  <genre>" + self.escape(self.channel) +
                      "</genre>\n")
            for tag in self.tags:
                nfo.write("  <tag>" + self.escape(tag.strip()) + "</tag>\n")
            nfo.write("  <studio>Kink.com</studio>\n")
            for i, actor in enumerate(self.models):
                nfo.write("  <actor>\n")
                nfo.write("    <name>" + self.escape(actor.name.strip()) + "</name>\n")
                nfo.write("    <type>Actor</type>\n")
                # nfo.write("    <thumb>" + self.escape(metadata['actor_thumbs'][i]) +
                #           "</thumb>\n")
                nfo.write("  </actor>\n")
        nfo.write("</movie>\n")

    def escape(self, data, entities={}) -> str:
        """Escape &, <, and > in a string of data.

        You can escape other strings of data by passing a dictionary as
        the optional entities parameter.  The keys and values must all be
        strings; each key will be replaced with its corresponding value.
        """

        # must do ampersand first
        data = data.replace("&", "&amp;")
        data = data.replace(">", "&gt;")
        data = data.replace("<", "&lt;")
        if entities:
            data = self.__dict_replace(data, entities)
        return data

    def __dict_replace(self, s, d):
        """Replace substrings of a string using a dictionary."""
        for key, value in d.items():
            s = s.replace(key, value)
        return s

    def export_data(self):
        return {
            'number': self.number,
            'title': self.title,
            'description': self.description,
            'videos': [vid.export_data() for vid in self.videos],
            'poster': self.poster.export_data() if self.poster else None,
            'zip_image': self.zip_image,
            'models': [mod.export_data() for mod in self.models],
            'tags': self.tags,
            # 'director': self.director.export_data(),
            'channel': self.channel,
            'release_date': self.release_date,
        }

    def import_data(self, data):
        self.number = data.get('number')
        self.title = data.get('title')
        self.description = data.get('description')

        if 'videos' in data and data['videos']:
            self.videos = [Video(**vid) for vid in data['videos']]

        if 'poster' in data and data['poster']:
            self.poster = Poster(**data)

        self.zip_image = ZipFile(**data.get('zip_image'))

        if 'models' in data and data['models']:
            self.models = [Model(**mod) for mod in data['models']]

        self.tags = data.get('tags')
        # self.director = Director().import_data(data['director'])
        self.channel = data.get('channel')
        self.release_date = data.get('release_date')
