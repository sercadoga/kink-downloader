from typing import TYPE_CHECKING




class Factory:
    singleton = None

    def __new__(cls, path=None, session=None, cookie=None):
        if cls.singleton is None:
            if path is None or session is None or cookie is None:
                raise Exception("you need to setup prorerl the fatory the first time you run")

            cls.singleton = super().__new__(cls)
            cls.path = path
            cls.session = session
            cls.cookie = cookie
            cls._model_cache = {}
            return cls.singleton

        return cls.singleton

    def get_gallery(self, href):
        from src.website.gallery import Gallery
        return Gallery(href=href, cookie=self.cookie, session=self.session)

    def get_shoot(self, href):
        from src.website.shoot import Shoot
        return Shoot(href=href, path=self.path, cookie=self.cookie, session=self.session)

    def get_model(self, href):
        if model := self._model_cache.get(href):
            return model

        from src.website.model import Model
        model = Model(href=href, cookie=self.cookie, session=self.session)
        self._model_cache[href] = model
        return model
