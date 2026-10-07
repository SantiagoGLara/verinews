from database.mongo import (
    obtener_coleccion,
)


cliente, noticias = obtener_coleccion()

try:
    total = noticias.count_documents({})

    print(
        "Total de documentos:",
        total
    )

    cursor = noticias.find(
        {},
        {
            "_id": 0,
            "titulo": 1,
            "fuente_rss": 1,
            "fecha_publicacion": 1,
            "analisis.numero_palabras": 1,
            "url": 1,
        }
    ).sort(
        "fecha_publicacion",
        -1
    ).limit(10)

    for doc in cursor:
        print(
            "\n" + "-" * 70
        )

        print(
            "Titulo :",
            doc.get("titulo")
        )

        print(
            "Fuente :",
            doc.get("fuente_rss")
        )

        print(
            "Fecha  :",
            doc.get(
                "fecha_publicacion"
            )
        )

        print(
            "Palabras:",
            (
                doc.get(
                    "analisis"
                )
                or {}
            ).get(
                "numero_palabras"
            )
        )

        print(
            "URL    :",
            doc.get("url")
        )
finally:
    cliente.close()
