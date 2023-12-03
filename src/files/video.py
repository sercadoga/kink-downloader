from src.utility.dowload_manager import DownloadManager


class Video(DownloadManager):

    def get_filename(self) -> str:
        return f'{self.number} - {self.quality}p.mp4'
    def __str__(self) -> str:
        return f'<Video: {self.get_filename()}>'

    __repr__ = __str__
