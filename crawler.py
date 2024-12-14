from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import requests
import os
import sys

class WebCrawler:
    def __init__(self, start_url, **kwargs):
        uri = self.parse_url(start_url)
        self.hostname = uri.netloc

        self.visited = set()
        self.downloaded = {}
        self.queue = { uri.geturl() }

        self.outdir = kwargs.get("outdir", "output")
        self.timeout = kwargs.get("timeout", 10)

    def parse_url(self, url):
        return urlparse(url.lower())._replace(query="", fragment="")

    def validate_url(self, url, path):
        uri = self.parse_url(path)

        if uri.scheme and uri.scheme not in ["http", "https"]:
            return False

        if uri.netloc:
            if uri.netloc != self.hostname:
                return False
        else:
            return urljoin(url, uri.geturl())

        return uri.geturl()

    def download(self, url):
        if url in self.downloaded:
            return self.downloaded[url]

        try:
            res = requests.get(url, timeout=self.timeout)
            content = res.content

            uri = self.parse_url(url)
            url = uri.netloc + uri.path
            filename = os.path.normpath(os.path.join(self.outdir, url))
            dirname = os.path.dirname(filename)

            os.makedirs(dirname, exist_ok=True)
            with open(filename, "wb") as file:
                file.write(content)

            assert res.ok
            self.downloaded[url] = content
            return content
        except:
            print(f"Requesting {url} failed!")
            return None

    def start(self):
        while len(self.queue) > 0:
            url = self.queue.pop()
            self.visited.add(url)
            print(f"Crawling {url}...")

            content = self.download(url)
            if not content:
                continue

            soup = BeautifulSoup(content, "html.parser")

            # find all hrefs
            href_tags = soup.find_all(href=True)
            for href_tag in href_tags:
                href_url = self.validate_url(url, href_tag.get("href"))
                if not href_url or href_url in self.visited:
                    continue

                self.queue.add(href_url)

            # find all media (image, css, gif, ...)
            # javascript code too i guess :P
            media_tags = soup.find_all(src=True) + soup.find_all("link", rel="stylesheet")
            for media_tag in media_tags:
                media_url = self.validate_url(url, media_tag.get("src") or media_tag.get("href"))
                if not media_url:
                    continue

                self.download(media_url)

if __name__ == "__main__":
    url = sys.argv[1]
    crawler = WebCrawler(url)
    crawler.start()