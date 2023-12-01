from src.utility.dowload_manager import DowloadManager


class ZipFile(DowloadManager):

    def get_filename(self) -> str:
        return f'{self.number}.zip'
    def __str__(self) -> str:
        return f'<ZipFile: {self.get_filename()}>'

    __repr__ = __str__
