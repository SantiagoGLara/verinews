from database.mongo import obtener_coleccion


cliente, noticias = obtener_coleccion()

try:

    pipeline = [
        {
            "$group": {
                "_id": "$fuente.nombre",

                "documentos": {
                    "$sum": 1
                },

                "tipos_acopio": {
                    "$addToSet":
                        "$fuente.tipo_acopio"
                },

                "origenes": {
                    "$addToSet":
                        "$fuente.origen_url"
                }
            }
        },

        {
            "$sort": {
                "documentos": -1
            }
        }
    ]

    print("FUENTES ALMACENADAS EN MONGODB")
    print("=" * 72)

    for fuente in noticias.aggregate(
        pipeline
    ):

        print(
            "\nFuente:",
            fuente["_id"]
        )

        print(
            "Documentos:",
            fuente["documentos"]
        )

        print(
            "Tipo de acopio:",
            ", ".join(
                fuente["tipos_acopio"]
            )
        )

        print("Orígenes:")

        for origen in fuente["origenes"]:
            print(
                "  -",
                origen
            )

finally:
    cliente.close()