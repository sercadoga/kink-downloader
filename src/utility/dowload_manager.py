import os.path
import tempfile
import httpx
import rich.progress


class DowloadManager:

    def __init__(self, url: str, number: int, quality: str, path: str) -> None:
        self._url = url
        self.quality = quality
        self.number = number
        self.path = path

    def get_filename(self) -> str:
        raise NotImplemented()

    def __str__(self) -> str:
        return '<Base File Class>'

    __repr__ = __str__

    def download(self):
        with open(os.path.join(self.path, self.get_filename())) as download_file:
            url = self.url
            with httpx.stream("GET", url) as response:
                total = int(response.headers["Content-Length"])

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
