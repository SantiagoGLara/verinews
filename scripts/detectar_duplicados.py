from database.mongo import obtener_coleccion

cliente, noticias = obtener_coleccion()

try:
    pipeline = [
        {
            "$match": {
                "analisis.numero_palabras": {"$gte": 100}
            }
        },
        {
            "$group": {
                "_id": "$analisis.hash_contenido",
                "cantidad": {"$sum": 1},
                "noticias": {
                    "$push": {
                        "titulo": "$titulo",
                        "fuente": "$fuente.nombre",
                        "url": "$url",
                    }
                },
            }
        },
        {"$match": {"cantidad": {"$gt": 1}}},
        {"$sort": {"cantidad": -1}},
    ]

    grupos = list(noticias.aggregate(pipeline))
    print("Grupos de duplicados exactos:", len(grupos))

    for grupo in grupos:
        print("\n" + "=" * 72)
        print("Cantidad:", grupo["cantidad"])

        for noticia in grupo["noticias"]:
            print("-", noticia["fuente"], "|", noticia["titulo"])
            print(" ", noticia["url"])
finally:
    cliente.close()
