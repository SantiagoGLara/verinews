import html
import re

from bs4 import BeautifulSoup


def quitar_html(texto):
    if not texto:
        return ""

    soup = BeautifulSoup(
        html.unescape(texto),
        "lxml"
    )

    return " ".join(
        soup.get_text(
            " ",
            strip=True
        ).split()
    )


def normalizar_texto(texto):
    if not texto:
        return ""

    texto = html.unescape(texto)

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def preparar_resumen_rss(resumen):
    return normalizar_texto(
        quitar_html(resumen)
    )
