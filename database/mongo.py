from datetime import datetime, timezone

from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT

from config import MONGO_URI, MONGO_DB, MONGO_COLLECTION


def obtener_coleccion():
    cliente = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
    )
    cliente.admin.command("ping")
    db = cliente[MONGO_DB]
    coleccion = db[MONGO_COLLECTION]
    return cliente, coleccion


def crear_indices():
    cliente, noticias = obtener_coleccion()

    try:
        noticias.create_index(
            [("url", ASCENDING)],
            unique=True,
            name="url_unica",
        )

        noticias.create_index(
            [("fecha_publicacion", DESCENDING)],
            name="fecha_publicacion_desc",
        )

        noticias.create_index(
            [
                ("fuente.nombre", ASCENDING),
                ("fecha_publicacion", DESCENDING),
            ],
            name="fuente_fecha",
        )

        noticias.create_index(
            [("analisis.hash_contenido", ASCENDING)],
            name="hash_contenido",
        )

        noticias.create_index(
            [
                ("titulo", TEXT),
                ("resumen", TEXT),
                ("contenido", TEXT),
            ],
            weights={
                "titulo": 5,
                "resumen": 3,
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
        documento["acopio"]["fecha_acopio"] = datetime.now(timezone.utc)

        resultado = noticias.update_one(
            {"url": documento["url"]},
            {"$setOnInsert": documento},
            upsert=True,
        )

        return resultado.upserted_id is not None
    finally:
        cliente.close()
