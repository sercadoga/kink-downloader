import os
from http.cookiejar import MozillaCookieJar

import cloudscraper

from src.utility.factory import Factory


def main():
    try:
        cookie_file = os.path.expanduser("~/cookies.txt")
        base_url = 'www.kink.com'
        session = cloudscraper.CloudScraper()
        cookie = MozillaCookieJar(cookie_file)
        cookie.load(ignore_expires=False, ignore_discard=False)
        path = os.path.abspath(os.path.join(os.path.abspath(''), '..', 'kink'))
        factory = Factory(path=path, cookie=cookie, session=session)
        gallery = factory.get_gallery('my/favorite-scenes')
        gallery.download()
    except KeyboardInterrupt:
        print('By :)')

if __name__ == '__main__':
    main()
