import re
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from config import USER_AGENT, REQUEST_TIMEOUT
from collectors.robots import permitido_por_robots


def normalizar_fecha(valor):
    if not valor:
        return None

    try:
        return date_parser.parse(valor)
    except Exception:
        return None


def recolectar_rss(fuente, limite):
    feed = feedparser.parse(fuente["url"])
    resultados = []

    for entrada in feed.entries[:limite]:
        categorias = []

        for tag in entrada.get("tags", []):
            termino = tag.get("term")
            if termino:
                categorias.append(termino)

        url = entrada.get("link", "").strip()
        if not url:
            continue

        resultados.append({
            "fuente_nombre": fuente["nombre"],
            "fuente_tipo": "rss",
            "fuente_url": fuente["url"],
            "titulo": entrada.get("title", "").strip(),
            "url": url,
            "resumen": entrada.get("summary", "").strip(),
            "fecha_publicacion": normalizar_fecha(
                entrada.get("published") or entrada.get("updated")
            ),
            "categorias": categorias,
        })

    return resultados


def recolectar_listing(fuente, limite):
    if not permitido_por_robots(fuente["url"]):
        print(
            "  robots.txt no permite consultar la pagina indice:",
            fuente["url"]
        )
        return []

    respuesta = requests.get(
        fuente["url"],
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    respuesta.raise_for_status()

    soup = BeautifulSoup(respuesta.text, "lxml")
    patron = re.compile(fuente["include_regex"])
    vistos = set()
    resultados = []

    for enlace in soup.find_all("a", href=True):
        absoluta = urljoin(
            respuesta.url,
            enlace["href"]
        ).split("#")[0]

        if absoluta in vistos:
            continue
        if not patron.search(absoluta):
            continue

        vistos.add(absoluta)
        titulo = " ".join(
            enlace.get_text(" ", strip=True).split()
        )

        if len(titulo) < 20:
            continue

        resultados.append({
            "fuente_nombre": fuente["nombre"],
            "fuente_tipo": "listing",
            "fuente_url": fuente["url"],
            "titulo": titulo,
            "url": absoluta,
            "resumen": "",
            "fecha_publicacion": None,
            "categorias": [],
        })

        if len(resultados) >= limite:
            break

    return resultados


def recolectar_fuente(fuente, limite):
    tipo = fuente["tipo"].lower()

    if tipo == "rss":
        return recolectar_rss(fuente, limite)

    if tipo == "listing":
        return recolectar_listing(fuente, limite)

    raise ValueError(f"Tipo de fuente no soportado: {tipo}")
