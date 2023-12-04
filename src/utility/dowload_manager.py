import os.path
import tempfile
import httpx
import rich.progress


class DownloadManager:

    def __init__(self, url: str, number: int | str, quality: str = None, path: str = None) -> None:
        self.url = url
        self.quality = quality
        self.number = str(number)
        self.path = path
        self._dir_path = os.path.join(os.path.abspath(self.path), self.number)

    def get_filename(self) -> str:
        raise NotImplemented()

    def __str__(self) -> str:
        return '<Base File Class>'

    __repr__ = __str__

    def export_data(self):
        return {
            'url': self.url,
            'quality': self.quality,
            'number': self.number,
            'path': self.path,
        }

    def download(self):
        if not os.path.exists(self._dir_path):
            os.mkdir(self._dir_path)
        file_path = os.path.join(self._dir_path, self.get_filename())
        print(f"filename: {file_path}")
        with open(file_path, 'wb') as download_file:
            with httpx.stream("GET", self.url) as response:
                total = int(response.headers["Content-Length"])
                if os.path.exists(file_path) and os.path.getsize(file_path) == total:
                    print(f"File {self.get_filename()} already downloaded")
                with rich.progress.Progress(
                        "[progress.percentage]{task.percentage:>3.0f}%",
                        rich.progress.BarColumn(bar_width=None),
                        rich.progress.DownloadColumn(),
                        rich.progress.TransferSpeedColumn(),
                ) as progress:
                    download_task = progress.add_task("Download", total=total)
                    for chunk in response.iter_bytes():
                        download_file.write(chunk)
                        progress.update(download_task, completed=response.num_bytes_downloaded)
