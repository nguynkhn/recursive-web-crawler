from urllib.parse import urlsplit, urljoin
from bs4 import BeautifulSoup
import os
import requests
import argparse

parse_uri = lambda url: urlsplit(url.lower())._replace(query='', fragment='')
get_uri_paths = lambda uri: uri.path.strip('/').split('/')[:-1]

class WebCrawler:
    def __init__(self, args):
        self.args = args

        self.uri = parse_uri(self.args.url)
        self.base_paths = get_uri_paths(self.uri)

        self.queue = set()
        self.cache = {}

    def validate_uri(self, uri):
        return not uri.scheme or uri.scheme in ['http', 'https'] \
            and uri.netloc == self.uri.netloc

    def check_depth(self, uri):
        test_paths = get_uri_paths(uri)
        base_level, test_level = len(self.base_paths), len(test_paths)

        if self.args.depth < 0:
            match_len = max(base_level + self.args.depth, 0)
            return self.base_paths[:match_len] == test_paths[:match_len]

        if test_level < base_level:
            # test url can't be shorter
            return False

        return test_paths[:base_level] == self.base_paths \
            and test_level - base_level <= self.args.depth

    def fetch_and_save(self, uri):
        if uri in self.cache:
            return self.cache[uri]

        try:
            res = requests.get(uri.geturl(), timeout=self.args.timeout)

            if res.ok:
                self.cache[uri] = res

                filename = os.path.normpath(uri.netloc + uri.path)
                filepath = os.path.join(self.args.output, filename)
                dirpath = os.path.dirname(filepath)

                os.makedirs(dirpath, exist_ok=True)
                with open(filepath, 'wb') as f:
                    f.write(res.content)

                return res
        except Exception as e:
            print(e)

        return None

    def crawl(self, uri):
        res = self.fetch_and_save(uri)
        if not res:
            print(f"Requesting {uri.geturl()} failed!")
            return

        if not res.headers['Content-Type'].startswith('text/html'):
            # not html file... skip
            return

        soup = BeautifulSoup(res.content, 'html.parser')

        # find all hrefs
        href_tags = soup.find_all(href=True)
        for href_tag in href_tags:
            href_url = urljoin(uri.geturl(), href_tag.get('href'))
            href_uri = parse_uri(href_url)
            if not self.validate_uri(href_uri) or href_uri in self.cache \
                or not self.check_depth(href_uri):
                continue

            self.queue.add(href_uri)

        # find all media (image, gif, ...)
        # js code too i guess
        media_tags = soup.find_all(src=True)
        for media_tag in media_tags:
            media_url = urljoin(uri.geturl(), media_tag.get('src'))
            media_uri = parse_uri(media_url)
            if not self.validate_uri(media_uri):
                continue

            self.fetch_and_save(media_uri)

    def start(self):
        self.queue.add(self.uri)

        while len(self.queue) > 0:
            uri = self.queue.pop()

            print(f"Crawling {uri.geturl()}...")
            self.crawl(uri)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url', type=str, help='starting url')
    parser.add_argument(
        '-o', '--output', type=str, default='output/',
        help='output directory (default: output/)',
    )
    parser.add_argument(
        '-t', '--timeout', type=int, default=10,
        help='request\'s timeout in seconds (default: 10)',
    )
    parser.add_argument(
        '-d', '--depth', type=int, default=0,
        help='maximum depth of url (default: 0)',
    )

    args = parser.parse_args()
    crawler = WebCrawler(args)
    crawler.start()
