from database.mongo import obtener_coleccion

consulta = input("Texto a buscar: ").strip()
cliente, noticias = obtener_coleccion()

try:
    pipeline = [
        {"$match": {"$text": {"$search": consulta}}},
        {"$set": {"score": {"$meta": "textScore"}}},
        {"$sort": {"score": -1}},
        {"$limit": 10},
        {
            "$project": {
                "_id": 0,
                "titulo": 1,
                "fuente.nombre": 1,
                "fecha_publicacion": 1,
                "url": 1,
                "score": 1,
            }
        },
    ]

    resultados = list(noticias.aggregate(pipeline))
    print("\nResultados:", len(resultados))

    for numero, doc in enumerate(resultados, start=1):
        print(f"\n{numero}. {doc.get('titulo')}")
        print("Fuente:", (doc.get("fuente") or {}).get("nombre"))
        print("Score:", round(doc.get("score", 0), 3))
        print("URL:", doc.get("url"))
finally:
    cliente.close()
