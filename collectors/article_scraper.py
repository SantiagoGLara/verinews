import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from config import USER_AGENT, REQUEST_TIMEOUT, REQUEST_DELAY_SECONDS
from collectors.robots import permitido_por_robots


def _texto(elemento):
    if not elemento:
        return ""
    return " ".join(elemento.get_text(" ", strip=True).split())


def _meta(soup, atributo, valor):
    etiqueta = soup.find("meta", attrs={atributo: valor})
    if etiqueta and etiqueta.get("content"):
        return etiqueta["content"].strip()
    return ""


def extraer_titulo(soup):
    candidatos = [
        _meta(soup, "property", "og:title"),
        _meta(soup, "name", "twitter:title"),
    ]

    h1 = soup.find("h1")
    if h1:
        candidatos.append(_texto(h1))

    if soup.title:
        candidatos.append(_texto(soup.title))

    for candidato in candidatos:
        if candidato:
            return candidato
    return ""


def extraer_autor(soup):
    for atributo, valor in [
        ("name", "author"),
        ("property", "article:author"),
        ("name", "byl"),
    ]:
        valor_meta = _meta(soup, atributo, valor)
        if valor_meta:
            return valor_meta

    for selector in [
        ".author",
        ".autor",
        "[rel='author']",
        "[class*='author']",
        "[class*='autor']",
    ]:
        texto = _texto(soup.select_one(selector))
        if texto:
            return texto[:300]

    return ""


def extraer_fecha(soup):
    candidatos = [
        _meta(soup, "property", "article:published_time"),
        _meta(soup, "name", "date"),
        _meta(soup, "itemprop", "datePublished"),
    ]

    time_tag = soup.find("time")
    if time_tag and time_tag.get("datetime"):
        candidatos.append(time_tag["datetime"])

    for valor in candidatos:
        if not valor:
            continue
        try:
            return date_parser.parse(valor)
        except Exception:
            pass

    return None


def extraer_imagen_principal(soup):
    for atributo, valor in [
        ("property", "og:image"),
        ("name", "twitter:image"),
    ]:
        imagen = _meta(soup, atributo, valor)
        if imagen:
            return imagen
    return ""


def extraer_contenido(soup):
    for etiqueta in soup(["script", "style", "noscript", "svg", "form"]):
        etiqueta.decompose()

    for selector in ["nav", "footer", "aside"]:
        for elemento in soup.select(selector):
            elemento.decompose()

    candidatos = [
        soup.find("article"),
        soup.find("main"),
        soup.select_one("[class*='article-body']"),
        soup.select_one("[class*='article-content']"),
        soup.select_one("[class*='entry-content']"),
        soup.select_one("[class*='post-content']"),
        soup.body,
    ]

    for candidato in candidatos:
        texto = _texto(candidato)
        if len(texto) >= 200:
            return texto

    return _texto(soup)


def descargar_y_extraer(url):
    if not permitido_por_robots(url):
        return {
            "url_final": url,
            "dominio": urlparse(url).netloc,
            "status_http": None,
            "content_type": "",
            "titulo_scraping": "",
            "autor": "",
            "fecha_scraping": None,
            "contenido": "",
            "imagen_principal": "",
            "error_scraping": "Bloqueado por robots.txt",
        }

    time.sleep(REQUEST_DELAY_SECONDS)

    try:
        respuesta = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        respuesta.raise_for_status()
    except requests.RequestException as error:
        return {
            "url_final": url,
            "dominio": urlparse(url).netloc,
            "status_http": None,
            "content_type": "",
            "titulo_scraping": "",
            "autor": "",
            "fecha_scraping": None,
            "contenido": "",
            "imagen_principal": "",
            "error_scraping": str(error),
        }

    content_type = respuesta.headers.get("Content-Type", "").lower()
    base = {
        "url_final": respuesta.url,
        "dominio": urlparse(respuesta.url).netloc,
        "status_http": respuesta.status_code,
        "content_type": content_type,
    }

    if "text/html" not in content_type:
        return {
            **base,
            "titulo_scraping": "",
            "autor": "",
            "fecha_scraping": None,
            "contenido": "",
            "imagen_principal": "",
            "error_scraping": "El recurso no es HTML",
        }

    soup = BeautifulSoup(respuesta.text, "lxml")

    return {
        **base,
        "titulo_scraping": extraer_titulo(soup),
        "autor": extraer_autor(soup),
        "fecha_scraping": extraer_fecha(soup),
        "contenido": extraer_contenido(soup),
        "imagen_principal": extraer_imagen_principal(soup),
        "error_scraping": None,
    }
