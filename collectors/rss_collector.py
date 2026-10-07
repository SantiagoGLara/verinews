import feedparser
from dateutil import parser as date_parser


def normalizar_fecha(valor):
    if not valor:
        return None

    try:
        return date_parser.parse(valor)
    except Exception:
        return None


def recolectar_feed(nombre_fuente, url_feed, limite=20):
    feed = feedparser.parse(url_feed)

    error = None
    if getattr(feed, "bozo", False):
        error = str(
            getattr(
                feed,
                "bozo_exception",
                "El feed presenta errores de formato"
            )
        )

    resultados = []

    for entrada in feed.entries[:limite]:
        categorias = []

        for tag in entrada.get("tags", []):
            termino = tag.get("term")
            if termino:
                categorias.append(termino)

        noticia = {
            "fuente_rss": nombre_fuente,
            "feed_url": url_feed,
            "titulo": entrada.get("title", "").strip(),
            "url": entrada.get("link", "").strip(),
            "resumen_rss": entrada.get("summary", "").strip(),
            "fecha_publicacion": normalizar_fecha(
                entrada.get("published")
                or entrada.get("updated")
            ),
            "categorias": categorias,
        }

        if noticia["url"]:
            resultados.append(noticia)

    return {
        "canal": feed.feed.get("title", nombre_fuente),
        "error": error,
        "noticias": resultados,
    }
