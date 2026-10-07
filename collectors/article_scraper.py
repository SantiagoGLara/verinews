import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from config import (
    USER_AGENT,
    REQUEST_TIMEOUT,
    REQUEST_DELAY_SECONDS,
)


def texto_limpio(elemento):
    if not elemento:
        return ""

    return " ".join(
        elemento.get_text(" ", strip=True).split()
    )


def extraer_autor(soup):
    candidatos_meta = [
        ("name", "author"),
        ("property", "article:author"),
        ("name", "byl"),
    ]

    for atributo, valor in candidatos_meta:
        meta = soup.find(
            "meta",
            attrs={atributo: valor}
        )

        if meta and meta.get("content"):
            return meta["content"].strip()

    selectores = [
        ".author",
        ".autor",
        "[rel='author']",
        "[class*='author']",
        "[class*='autor']",
    ]

    for selector in selectores:
        elemento = soup.select_one(selector)
        texto = texto_limpio(elemento)

        if texto:
            return texto[:300]

    return ""


def extraer_imagen_principal(soup):
    candidatos = [
        ("property", "og:image"),
        ("name", "twitter:image"),
    ]

    for atributo, valor in candidatos:
        meta = soup.find(
            "meta",
            attrs={atributo: valor}
        )

        if meta and meta.get("content"):
            return meta["content"].strip()

    return ""


def extraer_contenido(soup):
    # Se eliminan elementos que normalmente no forman parte
    # del cuerpo editorial de una noticia.
    for etiqueta in soup(
        ["script", "style", "noscript", "svg", "form"]
    ):
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
        texto = texto_limpio(candidato)

        if len(texto) >= 200:
            return texto

    return texto_limpio(soup)


def descargar_y_extraer(url):
    headers = {
        "User-Agent": USER_AGENT
    }

    # Pequeña pausa para no golpear al servidor
    # con solicitudes consecutivas.
    time.sleep(REQUEST_DELAY_SECONDS)

    respuesta = requests.get(
        url,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
        allow_redirects=True,
    )

    respuesta.raise_for_status()

    content_type = respuesta.headers.get(
        "Content-Type",
        ""
    ).lower()

    resultado_base = {
        "status_http": respuesta.status_code,
        "content_type": content_type,
        "url_final": respuesta.url,
        "dominio": urlparse(
            respuesta.url
        ).netloc,
    }

    if "text/html" not in content_type:
        return {
            **resultado_base,
            "autor": "",
            "contenido": "",
            "imagen_principal": "",
            "error_scraping":
                "El recurso recuperado no es HTML",
        }

    soup = BeautifulSoup(
        respuesta.text,
        "lxml"
    )

    return {
        **resultado_base,
        "autor": extraer_autor(soup),
        "contenido": extraer_contenido(soup),
        "imagen_principal":
            extraer_imagen_principal(soup),
        "error_scraping": None,
    }
