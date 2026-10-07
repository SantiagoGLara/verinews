from config import SOURCES, MAX_ITEMS_PER_SOURCE

from collectors.source_collector import recolectar_fuente
from collectors.article_scraper import descargar_y_extraer
from processing.normalizer import normalizar_texto, preparar_resumen_rss
from processing.analyzer import analizar_texto
from database.mongo import crear_indices, guardar_noticia


def construir_documento(item):
    scraping = descargar_y_extraer(item["url"])

    titulo = item.get("titulo") or scraping.get("titulo_scraping", "")
    resumen = preparar_resumen_rss(item.get("resumen", ""))
    contenido = normalizar_texto(scraping.get("contenido", ""))
    fecha = item.get("fecha_publicacion") or scraping.get("fecha_scraping")

    texto_analisis = " ".join(
        parte
        for parte in [titulo, resumen, contenido]
        if parte
    )

    return {
        "url": item["url"],
        "url_final": scraping.get("url_final", item["url"]),
        "fuente": {
            "nombre": item["fuente_nombre"],
            "tipo_acopio": item["fuente_tipo"],
            "origen_url": item["fuente_url"],
            "dominio": scraping.get("dominio", ""),
        },
        "titulo": titulo,
        "autor": scraping.get("autor", ""),
        "fecha_publicacion": fecha,
        "resumen": resumen,
        "contenido": contenido,
        "categorias": item.get("categorias", []),
        "imagen_principal": scraping.get("imagen_principal", ""),
        "acopio": {
            "metodo": (
                "rss+scraping"
                if item["fuente_tipo"] == "rss"
                else "listing+scraping"
            ),
            "status_http": scraping.get("status_http"),
            "content_type": scraping.get("content_type", ""),
            "error_scraping": scraping.get("error_scraping"),
        },
        "analisis": analizar_texto(texto_analisis),
    }


def main():
    print("=" * 72)
    print("VERINEWS - FASE 2 - ACOPIO DE NOTICIAS")
    print("=" * 72)

    print("\nComprobando MongoDB y creando indices...")
    crear_indices()
    print("OK")

    total_descubiertas = 0
    total_nuevas = 0
    total_existentes = 0
    total_errores = 0

    for fuente in SOURCES:
        print("\n" + "=" * 72)
        print("FUENTE:", fuente["nombre"])
        print("TIPO:", fuente["tipo"])
        print("ORIGEN:", fuente["url"])

        try:
            items = recolectar_fuente(
                fuente,
                MAX_ITEMS_PER_SOURCE,
            )
        except Exception as error:
            print("ERROR DESCUBRIENDO NOTICIAS:", error)
            total_errores += 1
            continue

        print("Noticias descubiertas:", len(items))
        total_descubiertas += len(items)

        for numero, item in enumerate(items, start=1):

            try:
                documento = construir_documento(item)
                titulo_mostrar = documento.get("titulo")
                if not titulo_mostrar:
                    titilo_mostrar = "(sin titulo)"
                print(f"[{numero:02d}] " f"{titulo_mostrar[:80]}")
                insertada = guardar_noticia(documento)

                if insertada:
                    total_nuevas += 1
                    print("     -> NUEVA")
                else:
                    total_existentes += 1
                    print("     -> YA EXISTIA")

                error_scraping = documento["acopio"].get("error_scraping")
                if error_scraping:
                    print("     -> Aviso scraping:", error_scraping)

            except Exception as error:
                total_errores += 1
                print("     -> ERROR:", error)

    print("\n" + "=" * 72)
    print("RESUMEN DEL ACOPIO")
    print("=" * 72)
    print("Noticias descubiertas :", total_descubiertas)
    print("Noticias nuevas       :", total_nuevas)
    print("Noticias existentes   :", total_existentes)
    print("Errores               :", total_errores)


if __name__ == "__main__":
    main()
