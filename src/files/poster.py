from src.utility.dowload_manager import DownloadManager


class Poster(DownloadManager):

    def get_filename(self) -> str:
        return f'poster.jpg'

    def __str__(self) -> str:
        return f'<Poster: {self.get_filename()}>'

    __repr__ = __str__
