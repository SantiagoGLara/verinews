from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from config import USER_AGENT, REQUEST_TIMEOUT

_CACHE = {}


def permitido_por_robots(url):
    parsed = urlparse(url)

    if not parsed.scheme or not parsed.netloc:
        return False

    base = f"{parsed.scheme}://{parsed.netloc}"

    if base in _CACHE:
        parser = _CACHE[base]
        return parser.can_fetch(USER_AGENT, url)

    robots_url = f"{base}/robots.txt"
    parser = RobotFileParser()
    parser.set_url(robots_url)

    try:
        respuesta = requests.get(
            robots_url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )

        if respuesta.status_code == 404:
            parser.parse([])
        elif respuesta.ok:
            parser.parse(respuesta.text.splitlines())
        else:
            parser.parse([])

    except requests.RequestException:
        parser.parse([])

    _CACHE[base] = parser
    return parser.can_fetch(USER_AGENT, url)
