from urllib.parse import urlparse, urljoin
import os
import sys
import requests
from bs4 import BeautifulSoup

queue = [sys.argv[1]]
visited = {}
outdir = "output"
timeout = 60

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
    res = requests.get(url, timeout=timeout)
    if not res.ok:
        print(f"Requesting {url} failed")
        return

    write_file(url, res.content)

    print(f"Crawling {url}...")
    soup = BeautifulSoup(res.text, "html.parser")

    hostname = urlparse(url).netloc
    def validate_url(path):
        if not path:
            return False

        uri = urlparse(path.lower())._replace(query="", fragment="")
        if uri.scheme and uri.scheme not in ["http", "https"]:
            return False

        if uri.netloc:
            if uri.netloc != hostname:
                # don't go too far away from our hostname
                return False
        else:
            # relative path
            return urljoin(url, uri.geturl())

        return uri.geturl()

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
        if not href or href in visited:
            continue

        queue.append(href)

if __name__ == "__main__":
    while len(queue) > 0:
        url = queue.pop()
        crawl(url)
