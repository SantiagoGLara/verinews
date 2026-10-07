from database.mongo import obtener_coleccion

cliente, noticias = obtener_coleccion()

try:
    print("Total:", noticias.count_documents({}))

    cursor = noticias.find(
        {},
        {
            "_id": 0,
            "titulo": 1,
            "fuente.nombre": 1,
            "fecha_publicacion": 1,
            "analisis.numero_palabras": 1,
            "acopio.error_scraping": 1,
        }
    ).sort("fecha_publicacion", -1).limit(20)

    for doc in cursor:
        print("\n" + "-" * 72)
        print("Titulo:", doc.get("titulo"))
        print("Fuente:", (doc.get("fuente") or {}).get("nombre"))
        print("Fecha:", doc.get("fecha_publicacion"))
        print("Palabras:", (doc.get("analisis") or {}).get("numero_palabras"))
        print("Error scraping:", (doc.get("acopio") or {}).get("error_scraping"))
finally:
    cliente.close()
