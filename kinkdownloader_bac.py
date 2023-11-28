#!/usr/bin/env python3
##############################################################################
# kinkdownloader, v0.6.1 - Downloads Kink.com videos and metadata.
#
# Copyright (C) 2020 MeanMrMustardGas <meanmrmustardgas at protonmail dot com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
##############################################################################
import argparse
import os
import datetime
import re

import cloudscraper
import sys
from xml.sax.saxutils import escape
from pathlib import Path
from bs4 import BeautifulSoup
from http.cookiejar import MozillaCookieJar
from tqdm import tqdm

# Set up command line arguments
parser = argparse.ArgumentParser(description=''' Download shoot
                                                 videos from kink.com''')
parser.add_argument("url", help="Shoot or channel gallery URL.")
parser.add_argument("-q", "--quality", help="Select video quality.",
                    choices=["1080", "720", "540", "480", "360",
                             "288", "270"])
parser.add_argument("-c", "--cookies", metavar="cookies.txt",
                    help="Location of Netscape cookies.txt file")
parser.add_argument("--no-video", action="store_true", default=False,
                    help="Don't download shoot video[s].")
parser.add_argument("-a", "--all-quality", action="store_true", default=False,
                    help="Download all quality of shoot video[s].")
parser.add_argument("-m", "--no-metadata", action="store_true", default=False,
                    help="Don't download any additional metadata,")
parser.add_argument("-n", "--no-nfo", action="store_true", default=False,
                    help="Don't create emby-compatible nfo file.")
parser.add_argument("-b", "--no-bio", action="store_true", default=False,
                    help="Don't download actor thumbnails.")
parser.add_argument("-t", "--no-thumbs", action="store_true", default=False,
                    help="Don't download shoot thumbnails.")
parser.add_argument("-p", "--no-poster", action="store_true", default=False,
                    help="Don't download shoot poster image.")
parser.add_argument("-i", "--no-images", action="store_true", default=False,
                    help="Don't download shoot image zip bundle.")
parser.add_argument("--bio-dir", default=".", metavar="dir",
                    help="Thumbnail base directory.")
parser.add_argument("-r", "--recursive", action="store_true", default=False,
                    help="Recursively download whole gallery.")
parser.add_argument("-l", "--multiple-pages",
                    help="las page number")
parser.add_argument("-d", "--debug", action="store_true", default=False,
                    help="Write debugging information to 'debug.log'")
args = parser.parse_args()

session = cloudscraper.CloudScraper()

shot_dir = None
shot_number = None


def get_html(url, cookie):
    """
    Gets html for processing.
    """
    req = session.get(url, cookies=cookie)
    soup = BeautifulSoup(req.text, "html.parser")
    return soup


def get_dl_url(html, pref_quality):
    """
    Gets download URL for chosen or nearest lower available quality.
    """
    quality_list = ["1080", "720", "540", "480", "360", "288", "270"]
    links = {}
    possibility = []
    for tag in html.find_all("a", download=True):
        tag_text = tag.get_text().strip()
        for quality_name in quality_list:
            if quality_name in tag_text:
                links[quality_name] = tag.get('download')
                break

    for quality_name in quality_list[quality_list.index(pref_quality):]:
        if quality_name in links:
            return links[quality_name]
    return None


def get_all_quality_dl_url(html, pref_quality):
    """
    Gets download URL for chosen or nearest lower available quality.
    """
    quality_list = ["1080", "720", "540", "480", "360", "288", "270"]
    links = {}
    for tag in html.find_all("a", download=True):
        tag_text = tag.get_text().strip()
        for quality_name in quality_list:
            if quality_name in tag_text:
                links[quality_name] = tag.get('download')
                break

    return links


def get_images_dl_url(html):
    """
    Gets download URL for image set zip if available.
    """
    for tag in html.find_all("a", download=True):
        if 'images' in tag.get_text():
            return tag.get('download')
    return None


def get_filename(url):
    """
    Get filename from url.
    """
    global shot_dir
    fname = url.split("/")[-1]
    fname = fname.split("?")[0]
    if shot_dir is None:
        raise Exception('no shot dir')
    if not (isinstance(shot_dir, str) and isinstance(fname, str)):
        raise Exception('What?')

    return os.path.join(shot_dir, fname)


def get_metadata(src):
    """
    Parse src for shoot metadata.
    """
    title = src.find("h1", "shoot-title").get_text(strip=True)[:-1]

    desc = src.find("span", "description-text")
    desc = desc.find("p")
    if desc is None:
        desc = "No Desription Available"
    else:
        desc = desc.get_text()

    shoot_date = src.find("span", "shoot-date")
    shoot_date = datetime.datetime.strptime(shoot_date.get_text(), '%B %d, %Y')
    shoot_date = shoot_date.strftime("%Y-%m-%d")

    actors = []
    genres = []
    actor_thumbs = []

    for actors_tag in src.find_all("span", "names h5"):
        for bio in actors_tag.find_all("a"):
            name = bio.get_text().replace(',', '').strip()
            actors.append(name)
            bio_url = "https://www.kink.com" + bio.attrs['href']
            bio_page = BeautifulSoup(session.get(bio_url).text, "html.parser")

            if bio_page.find("img", "bio-slider-img") is None:
                if bio_page.find("img", "bio-img") is None:
                    img = "https://cdnp.kink.com/imagedb/43869/i/h/410/16.jpg"
                else:
                    img = bio_page.find("img", "bio-img").attrs['src']
            else:
                img = bio_page.find("img", "bio-slider-img").attrs['src']
            actor_thumbs.append(img)

    for tag in src.find_all("a", "tag"):
        g = tag.get_text().replace(',', '').strip()
        genres.append(g)

    metadata = {"title": title,
                "description": desc,
                "releasedate": shoot_date,
                "genres": genres,
                "actors": actors,
                "actor_thumbs": actor_thumbs}
    return metadata


def get_thumb_url(html):
    """
    Parse html for thumbnail zip url
    """
    tag = html.find("a", "zip-links")
    try:
        thumb_url = tag['href']
    except TypeError:
        print("Thumbnail URL not found. Skipping.")
        return None
    return thumb_url


def get_poster_url(html):
    """
    Parse html for poster url
    """
    tag = html.find("video", {"id": "kink-player"})
    try:
        poster_url = tag['poster']
    except TypeError:
        print("Poster URL not found. Skipping.")
        return None
    return poster_url


def download_file(url, fname, cookie):
    """
    Download url and save as filename with progressbar
    """
    fpath = Path(fname)

    if fpath.exists():
        r = session.head(url, cookies=cookie)
        length = r.headers['Content-Length']
        fsize = fpath.stat().st_size
        if int(length) <= fsize:
            print("File " + fname + " exists: Skipping.")
            return 1

    chunk_size = 1024 * 512  # 512 KB
    dl = session.get(url, cookies=cookie, stream=True, allow_redirects=True)
    with open(fname, "wb") as fout:
        with tqdm(unit="B", unit_scale=True, unit_divisor=1024, miniters=1,
                  desc=fname, total=int(dl.headers.get('content-length'))
                  ) as pbar:
            for chunk in dl.iter_content(chunk_size=chunk_size):
                pbar.update(fout.write(chunk))


def write_metadata_nfo(metadata, fname):
    """
    Write metadata to emby compatible NFO file.
    """
    global shot_dir, shot_number
    fname = os.path.join(shot_dir, shot_number + ".nfo")
    with open(fname, "w") as nfo:
        nfo.write('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        nfo.write("<movie>\n")
        nfo.write("  <plot>" + escape(metadata['description']) + "</plot>\n")
        nfo.write("  <title>" + escape(metadata['title']) + "</title>\n")
        nfo.write("  <releasedate>" + escape(metadata['releasedate']) +
                  "</releasedate>\n")
        for tag in metadata['genres']:
            nfo.write("  <tag>" + escape(tag.strip()) + "</tag>\n")
        nfo.write("  <studio>Kink.com</studio>\n")
        for i, actor in enumerate(metadata['actors']):
            nfo.write("  <actor>\n")
            nfo.write("    <name>" + escape(actor.strip()) + "</name>\n")
            nfo.write("    <type>Actor</type>\n")
            nfo.write("    <thumb>" + escape(metadata['actor_thumbs'][i]) +
                      "</thumb>\n")
            nfo.write("  </actor>\n")
        nfo.write("</movie>\n")


def dl_actor_thumb(metadata, path):
    """
    Download actor thumbnail
    """
    if not metadata['actors']:
        print("No performers listed for shoot.\n")
        return False
    for i, actor in enumerate(metadata['actors']):
        dl_path = path + "/" + actor[0].upper() + "/" + actor
        if not os.path.isdir(dl_path):
            try:
                os.makedirs(dl_path)
            except OSError:
                print("Creation of directory %s failed." % dl_path)
        if not os.path.isfile(dl_path + "/poster.jpg"):
            dl = session.get(metadata['actor_thumbs'][i])
            with open(dl_path + "/poster.jpg", "wb") as fout:
                fout.write(dl.content)
    return True


def process_shoot(url, quality, cookie, _is_gallery):
    """
    Downloads shoot video & metadata
    """
    soup = get_html(url, cookie)
    dl_url = get_dl_url(soup, quality)
    if dl_url is None:
        if not _is_gallery:
            sys.exit("Download unavailable for url: " + url + "\n")
        return

    fname = get_filename(dl_url)

    if args.no_metadata is True:
        args.no_bio = True
        args.no_thumbs = True
        args.no_nfo = True
        args.no_poster = True

    if args.no_video is False:
        if args.all_quality:
            links = get_all_quality_dl_url(soup, quality)
            for key, link in links.items():
                shot_name = os.path.join(shot_dir, f"{shot_number} - [{key}p].{fname.split('.')[-1]}")
                download_file(link, shot_name, cookie)

        else:
            download_file(dl_url, fname, cookie)

    if args.no_images is False:
        img_dl_url = get_images_dl_url(soup)
        if img_dl_url:
            download_file(img_dl_url, get_filename(img_dl_url), cookie)

    if args.no_nfo is False:
        write_metadata_nfo(get_metadata(soup), fname)

    if args.no_bio is False:
        dl_actor_thumb(get_metadata(soup),
                       os.path.expanduser(args.bio_dir))

    if args.no_thumbs is False:
        thumb_url = get_thumb_url(soup)
        if thumb_url:
            download_file(thumb_url, get_filename(thumb_url), cookie)

    if args.no_poster is False:
        poster_url = get_poster_url(soup)
        if poster_url is None:
            return
        match = re.search(r'(\w+\.(png|jpg|gif|bmp|jpeg))', poster_url)
        if not match:
            return

        pext = match.group()
        pname = get_filename(pext)
        download_file(poster_url, pname, cookie)


def get_shoot_list(url, cookie):
    """
    Returns list of shoots from single gallery page
    """
    soup = get_html(url, cookie)
    shoots = soup.find_all("a", "shoot-link")
    shoot_urls = ["https://www.kink.com" + link.get('href') for link in shoots]

    return shoot_urls


def process_gallery(url, cookie):
    """
    Returns list of shoots to download from selected gallery.
    """
    soup = get_html(url, cookie)
    shoot_urls = []

    if args.recursive is True:
        if '&page=' in url:
            cur_page = int(url.split('&page=')[-1])
            url = url.split('&page=')[-2]
        else:
            cur_page = 1
        num_pages = int(soup.find("nav", "paginated-nav").find_all("li")[-2].text)

        while cur_page <= num_pages:
            page_url = url + '&page=' + str(cur_page)
            shoot_urls += get_shoot_list(page_url, cookie)
            cur_page += 1
    elif args.multiple_pages:

        for i in range(1, int(args.multiple_pages) + 1, 1):
            page_url = f"{url}/page/{i}"
            shoot_urls += get_shoot_list(page_url, cookie)
    else:
        shoot_urls = get_shoot_list(url, cookie)

    return shoot_urls


def process_url(url):
    url = url.split("//")[1]
    type = url.split("/")[1]
    tags = {}
    if "?" in type:
        for pair in type.split("?")[1].split("&"):
            tag = pair.split("=")[0]
            val = pair.split("=")[1]
            tags[tag] = val
        type = type.split("?")[0]
    if type == "shoot":
        tags['is_gallery'] = False
    else:
        tags['is_gallery'] = True
    return tags


def wrap_process_video():
    ...


def main():
    # Grab cookies from netscape cookie format file, and create cookie jar.
    global shot_dir, shot_number
    if args.cookies is None:
        cookie_file = os.path.expanduser("~/cookies.txt")
    else:
        cookie_file = os.path.expanduser(args.cookies)

    cookie = MozillaCookieJar(cookie_file)
    cookie.load(ignore_expires=True, ignore_discard=True)

    if args.quality is None:
        quality = "1080"
    else:
        quality = args.quality

    # Grab shoot url from commandline arguments
    if process_url(args.url)['is_gallery']:
        shoot_urls = process_gallery(args.url, cookie)
        print(f'you are going to download {len(shoot_urls)} videos')
        for index, download in enumerate(shoot_urls):
            print(f'==== video {index + 1} of {len(shoot_urls)} ================')

            download.split('/')
            shot_dir = os.path.join(args.bio_dir, download.split('/')[-1])
            shot_number = download.split('/')[-1]
            if not os.path.exists(shot_dir):
                os.makedirs(shot_dir)
            process_shoot(download, quality, cookie, True)
            print(f'============================================================')
    else:
        process_shoot(args.url, quality, cookie, False)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('by :)')
        exit(0)
