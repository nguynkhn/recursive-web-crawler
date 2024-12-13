from urllib.parse import urlsplit, urlparse, urljoin
import os
import sys
import requests
from bs4 import BeautifulSoup

visited = {}
outdir = "output"
timeout = 10

def write_file(url, content=None):
    if not content:
        if url in visited:
            content = visited[url]
        else:
            try:
                res = requests.get(url, timeout=timeout)
                if not res.ok:
                    print(f"Requesting {url} failed")
                    return

                content = res.content
            except:
                print(f"Requesting {url} failed")
                return

    visited[url] = content

    filename = os.path.join(outdir, urlparse(url).path[1:])
    dirname = os.path.dirname(filename)

    os.makedirs(dirname, exist_ok=True)
    with open(filename, "wb") as file:
        file.write(content)

def crawl(url):
    if url in visited:
        return

    res = requests.get(url, timeout=timeout)
    if not res.ok:
        print(f"Requesting {url} failed")
        return

    write_file(url, res.content)

    print(f"Crawling {url}...")
    soup = BeautifulSoup(res.text, 'html.parser')

    hostname = urlparse(url).netloc
    def validate_url(path):
        if not path:
            return False

        uri = urlparse(path)

        if uri.scheme and uri.scheme not in ["http", "https"]:
            return False

        if uri.netloc:
            if uri.netloc != hostname:
                # don't go too far away from our hostname
                return False
        else:
            # relative path
            return urljoin(url, path)

        return path

    # images, audio, gif, css, ...
    media_elems = soup.find_all(src=True) + soup.find_all("link", rel="stylesheet")
    for elem in media_elems:
        src = validate_url(elem.get("src") or elem.get("href"))
        if not src:
            continue

        write_file(src)

    href_elems = soup.find_all(href=True)
    for elem in href_elems:
        href = validate_url(elem.get("href"))
        if not href:
            continue

        crawl(href)

if __name__ == "__main__":
    url = sys.argv[1]
    crawl(url)