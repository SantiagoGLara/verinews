from datetime import datetime, timezone

from pymongo import (
    MongoClient,
    ASCENDING,
    DESCENDING,
    TEXT,
)

from config import (
    MONGO_URI,
    MONGO_DB,
    MONGO_COLLECTION,
)


def obtener_coleccion():
    cliente = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
    )

    # Igual que en la práctica de MongoDB:
    # comprueba que el servidor responda.
    cliente.admin.command("ping")

    db = cliente[MONGO_DB]
    coleccion = db[MONGO_COLLECTION]

    return cliente, coleccion


def crear_indices():
    cliente, noticias = obtener_coleccion()

    try:
        # URL única: ayuda a no guardar la misma noticia
        # una y otra vez.
        noticias.create_index(
            [("url", ASCENDING)],
            unique=True,
            name="url_unica",
        )

        # Índice cronológico.
        noticias.create_index(
            [("fecha_publicacion", DESCENDING)],
            name="fecha_publicacion_desc",
        )

        # Fuente + fecha.
        noticias.create_index(
            [
                ("fuente_rss", ASCENDING),
                ("fecha_publicacion", DESCENDING),
            ],
            name="fuente_fecha",
        )

        # Índice de texto para recuperación.
        noticias.create_index(
            [
                ("titulo", TEXT),
                ("resumen_rss", TEXT),
                ("contenido", TEXT),
            ],
            weights={
                "titulo": 5,
                "resumen_rss": 3,
                "contenido": 1,
            },
            name="indice_busqueda_noticias",
            default_language="spanish",
        )
    finally:
        cliente.close()


def guardar_noticia(documento):
    cliente, noticias = obtener_coleccion()

    try:
        documento["acopio"]["fecha_acopio"] = (
            datetime.now(timezone.utc)
        )

        resultado = noticias.update_one(
            {
                "url": documento["url"]
            },
            {
                "$setOnInsert": documento
            },
            upsert=True,
        )

        return resultado.upserted_id is not None
    finally:
        cliente.close()
