from datetime import datetime, timezone

from config import (
    RSS_SOURCES,
    MAX_ITEMS_PER_FEED,
)

from collectors.rss_collector import (
    recolectar_feed,
)

from collectors.article_scraper import (
    descargar_y_extraer,
)

from processing.normalizer import (
    normalizar_texto,
    preparar_resumen_rss,
)

from processing.analyzer import (
    analizar_texto,
)

from database.mongo import (
    crear_indices,
    guardar_noticia,
)


def construir_documento(item):
    scraping = descargar_y_extraer(
        item["url"]
    )

    contenido = normalizar_texto(
        scraping.get(
            "contenido",
            ""
        )
    )

    resumen = preparar_resumen_rss(
        item.get(
            "resumen_rss",
            ""
        )
    )

    texto_analisis = " ".join(
        parte
        for parte in [
            item.get("titulo", ""),
            resumen,
            contenido,
        ]
        if parte
    )

    documento = {
        "url": item["url"],

        "url_final":
            scraping.get(
                "url_final",
                item["url"]
            ),

        "fuente_rss":
            item["fuente_rss"],

        "feed_url":
            item["feed_url"],

        "dominio":
            scraping.get(
                "dominio",
                ""
            ),

        "titulo":
            item.get(
                "titulo",
                ""
            ),

        "autor":
            scraping.get(
                "autor",
                ""
            ),

        "fecha_publicacion":
            item.get(
                "fecha_publicacion"
            ),

        "resumen_rss":
            resumen,

        "contenido":
            contenido,

        "imagen_principal":
            scraping.get(
                "imagen_principal",
                ""
            ),

        "categorias":
            item.get(
                "categorias",
                []
            ),

        "acopio": {
            "metodo":
                "rss+scraping",

            "status_http":
                scraping.get(
                    "status_http"
                ),

            "content_type":
                scraping.get(
                    "content_type",
                    ""
                ),

            "error_scraping":
                scraping.get(
                    "error_scraping"
                ),

            "fecha_acopio":
                datetime.now(
                    timezone.utc
                ),
        },

        "analisis":
            analizar_texto(
                texto_analisis
            ),
    }

    return documento


def main():
    print("=" * 70)
    print(
        "VERINEWS - FASE 2 - "
        "ACOPIO AUTOMATIZADO"
    )
    print("=" * 70)

    print(
        "\n[1/3] Comprobando MongoDB "
        "y creando indices..."
    )

    crear_indices()

    print("OK")

    total_encontradas = 0
    total_insertadas = 0
    total_existentes = 0
    total_errores = 0

    print(
        "\n[2/3] Consultando feeds RSS..."
    )

    for fuente in RSS_SOURCES:
        print(
            "\nFUENTE:",
            fuente["nombre"]
        )

        print(
            "FEED:",
            fuente["url"]
        )

        try:
            resultado_feed = recolectar_feed(
                fuente["nombre"],
                fuente["url"],
                limite=MAX_ITEMS_PER_FEED,
            )
        except Exception as error:
            print(
                "ERROR AL LEER FEED:",
                error
            )
            total_errores += 1
            continue

        if resultado_feed["error"]:
            print(
                "Aviso del feed:",
                resultado_feed["error"]
            )

        noticias = (
            resultado_feed["noticias"]
        )

        print(
            "Entradas recuperadas:",
            len(noticias)
        )

        total_encontradas += len(
            noticias
        )

        for numero, item in enumerate(
            noticias,
            start=1
        ):
            titulo_corto = (
                item["titulo"][:75]
            )

            print(
                f"  [{numero:02d}] "
                f"{titulo_corto}"
            )

            try:
                documento = (
                    construir_documento(
                        item
                    )
                )

                insertada = (
                    guardar_noticia(
                        documento
                    )
                )

                if insertada:
                    total_insertadas += 1

                    print(
                        "       -> NUEVA: "
                        "almacenada en MongoDB"
                    )
                else:
                    total_existentes += 1

                    print(
                        "       -> EXISTENTE: "
                        "no se duplico"
                    )

            except Exception as error:
                total_errores += 1

                print(
                    "       -> ERROR:",
                    error
                )

    print(
        "\n[3/3] RESUMEN"
    )
    print("-" * 70)

    print(
        "Entradas RSS revisadas :",
        total_encontradas
    )

    print(
        "Noticias nuevas        :",
        total_insertadas
    )

    print(
        "Noticias ya existentes :",
        total_existentes
    )

    print(
        "Errores                 :",
        total_errores
    )

    print("-" * 70)
    print("Proceso terminado.")


if __name__ == "__main__":
    main()
