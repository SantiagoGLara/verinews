from database.mongo import obtener_coleccion

cliente, noticias = obtener_coleccion()

try:
    pipeline = [
        {
            "$group": {
                "_id": "$fuente.nombre",
                "documentos": {"$sum": 1},
                "con_contenido": {
                    "$sum": {
                        "$cond": [
                            {"$gte": ["$analisis.numero_palabras", 100]},
                            1,
                            0,
                        ]
                    }
                },
            }
        },
        {"$sort": {"documentos": -1}},
    ]

    print("RESUMEN POR FUENTE")
    print("-" * 72)

    for fila in noticias.aggregate(pipeline):
        print(
            f"{fila['_id']}: {fila['documentos']} documentos, "
            f"{fila['con_contenido']} con texto suficiente"
        )
finally:
    cliente.close()
