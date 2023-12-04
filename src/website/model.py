import json

import cloudscraper
from bs4 import BeautifulSoup

from src.files.poster import Poster
from src.utility.url_manager import UrlManager


class Model(UrlManager):

    def __init__(self, href: str | list[str], cookie, session):
        super().__init__(UrlManager.HttpType.HTTPS, 'www.kink.com', segments=href)
        self.cookie = cookie
        self.soup = None
        self.session = session
        self.name: str | None = None
        self.description: str | None = None
        self.tag: list[str] | None = None
        self.poster: Poster | None = None

    def get_data(self):
        req = self.session.get(self.get_url(), cookies=self.cookie)
        self.soup = BeautifulSoup(req.text, "html.parser")
        self.name = self.soup.select('.page-title')[0].get_text().split('\n')[0].strip()
        if models := self.soup.select('#expand-text'):
            self.description = models[0].get_text()

        self.tag = [el.get_text() for el in self.soup.select('.bio-tags > a')]

    def export_data(self):
        return {
            'url': self.get_url(),
            'name': self.name,
            'description': self.description,
            'tag': self.tag,
            'poster': self.poster.export_data() if self.poster else None
        }

    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        model = Model(href=data.get('href'), cookie=data.get('cookie'), session=None)
        model.soup = data.get('soup')
        model.name = data.get('name')
        model.description = data.get('description')
        model.tag = data.get('tag')
        return model
