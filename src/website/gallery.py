import time
from typing import TYPE_CHECKING

import cloudscraper
from bs4 import BeautifulSoup

from src.files.poster import Poster

if TYPE_CHECKING:
    from src.utility.factory import Factory
from src.utility.url_manager import UrlManager
from src.website.shoot import Shoot


class Gallery(UrlManager):
    """
    Work only on favorite
    """

    def __init__(self, href: str | list[str], cookie, session):
        super().__init__(UrlManager.HttpType.HTTPS, 'www.kink.com', segments=href)
        self.pages_number = 0
        self.cookie = cookie
        self.soup = None
        self.session = session
        self.name: str | None = None
        self.shoots: list[Shoot] | None = []
        from src.utility.factory import Factory
        self.factory: Factory = Factory()
        print('initializing gallery')
        self.set_soup()
        self.get_page_number()
        print(f'number of pages: {self.pages_number}')
        self.get_shoots()

    def set_soup(self):
        req = self.session.get(self.get_url(), cookies=self.cookie)
        self.soup = BeautifulSoup(req.text, "html.parser")

    def get_shoots(self):
        for page in range(1, self.pages_number + 1, 1):
            start_time = time.time()
            print(f'page: {page}')
            self.set_page(str(page))
            self.set_soup()
            shots = [self.factory.get_shoot(el.get('href')) for el in
                     self.soup.select('div.col-sm-6 > div:nth-child(1) > div:nth-child(2) > a')]
            self.shoots = [*self.shoots, *shots]
            end_time = time.time()
            print(f"Time for this page: {round((end_time - start_time) // 60)}mm  {round((end_time - start_time) % 60, 2)}ss")
            print("============================================================================")

    def get_page_number(self):
        last_page_of_favorites_fav = self.soup.select('li.page-item:last-child > a:nth-child(1)')
        last_page_of_favorites_gallery = self.soup.select(
            '.paginated-nav > ul:nth-child(1) > li:nth-child(13) > a:nth-child(1)')
        if len(last_page_of_favorites_fav):
            last_val = last_page_of_favorites_fav[0].get_text()
        elif len(last_page_of_favorites_gallery):
            last_val = last_page_of_favorites_fav[0].get_text()
        else:
            last_val = 0
        self.pages_number = int(last_val)

    def download(self):
        print(f'Downloading {self.get_url()} gallery...')
        shot: Shoot
        for shot in self.shoots:
            shot.download_best()
