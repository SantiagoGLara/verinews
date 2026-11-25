"""Interfaz CLI unificada de VeriNews.

Ejecutar desde la raíz del proyecto: python -m scripts.verinews
"""

import json
from pathlib import Path

from processing.clustering import (
    cargar_agrupamientos,
    generar_agrupamientos,
)
from scripts.asistente_voz import (
    buscar_noticias,
    reconocer_voz,
    sintetizar,
)

ROOT = Path(__file__).resolve().parents[1]
DATOS = ROOT / "data" / "unidad3"


def imprimir_resultados(resultados):
    if not resultados:
        print("No se encontraron noticias relacionadas.")
        return
    print("\nNoticias relacionadas (ordenadas por similitud TF-IDF):")
    for numero, noticia in enumerate(resultados, start=1):
        print(f"\n{numero}. {noticia['titulo']}")
        print(f"   Fuente: {noticia['fuente']} | Similitud: {noticia['similitud']:.4f}")
        if noticia.get("fecha"):
            print(f"   Fecha: {noticia['fecha']}")
        if noticia.get("url"):
            print(f"   URL: {noticia['url']}")
        extracto = (noticia.get("resumen") or noticia.get("contenido") or "").strip()
        if extracto:
            print("   Extracto:", extracto[:260])


def menu_busqueda(por_voz=False):
    if por_voz:
        try:
            consulta = reconocer_voz()
        except Exception as exc:
            print(f"No fue posible realizar la consulta por voz: {exc}")
            return
    else:
        consulta = input("Escriba el tema o acontecimiento que desea investigar: ").strip()
    if not consulta:
        print("La consulta está vacía.")
        return

    print(f"\nConsulta: {consulta}")
    try:
        resultados, aviso = buscar_noticias(consulta, limite=5)
    except Exception as exc:
        print(f"No se pudo completar la búsqueda: {exc}")
        return
    if aviso:
        print(aviso)
        if por_voz:
            sintetizar(aviso)
        return
    imprimir_resultados(resultados)
    if por_voz and resultados:
        primero = resultados[0]
        respuesta = (
            f"Encontré {len(resultados)} noticias relacionadas. "
            f"La más cercana es {primero['titulo']}, de {primero['fuente']}."
        )
        sintetizar(respuesta)


def asegurar_agrupamientos(recalcular=False):
    resultado = None if recalcular else cargar_agrupamientos(DATOS)
    if resultado is None:
        print("Generando agrupamientos temáticos con K-means...")
        resultado = generar_agrupamientos(DATOS, n_clusters=14)
        print("Resultado guardado en data/unidad3/agrupamientos_kmeans.json")
    return resultado


def menu_grupos():
    try:
        resultado = asegurar_agrupamientos()
    except Exception as exc:
        print(f"No fue posible generar los grupos: {exc}")
        return

    print(
        f"\nClasificación no supervisada con K-means: {resultado['documentos']} noticias, "
        f"{resultado['numero_grupos']} grupos. "
        f"Silhouette (coseno): {resultado['silhouette_coseno']:.4f}"
    )
    print("Nota: un valor cercano a 0 indica que algunos grupos se solapan.")
    for grupo in resultado["grupos"]:
        palabras = ", ".join(x["termino"] for x in grupo["terminos_representativos"][:5])
        print(
            f"\nGrupo {grupo['grupo']} — {grupo['cantidad']} noticias "
            f"({grupo['porcentaje']:.1f}%)"
        )
        print("   Términos:", palabras or "Sin términos representativos")
        fuentes = ", ".join(
            f"{x['fuente']} ({x['cantidad']})" for x in grupo["fuentes"][:3]
        )
        print("   Fuentes:", fuentes or "Sin fuente")

    while True:
        opcion = input("\nNúmero de grupo para ver noticias (Enter para volver): ").strip()
        if not opcion:
            return
        if not opcion.isdigit():
            print("Escriba un número de grupo válido.")
            continue
        numero = int(opcion)
        if not 1 <= numero <= len(resultado["grupos"]):
            print("Ese grupo no existe.")
            continue
        grupo = next(g for g in resultado["grupos"] if g["grupo"] == numero)
        print(f"\nNoticias del grupo {numero}:")
        for noticia in grupo["noticias"][:10]:
            print(f"\n- {noticia['titulo']}")
            print(
                f"  {noticia['fuente']} | {noticia['fecha']} "
                f"| similitud al centroide: {noticia['similitud_centroide']:.3f}"
            )
            print(f"  {noticia['url']}")


def menu_estadisticas():
    ruta = DATOS / "estadisticas.json"
    if not ruta.exists():
        print("No se encontraron estadísticas. Ejecute python -m scripts.preparar_unidad3.")
        return
    with ruta.open("r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    print("\nEstadísticas del corpus VeriNews")
    print("Noticias procesadas:", datos.get("total_noticias", 0))
    print("Noticias con texto:", datos.get("noticias_con_texto", 0))
    print("Tokens limpios:", datos.get("tokens_limpios_total", 0))
    print("Vocabulario:", datos.get("vocabulario_total", 0))
    print("Diversidad léxica:", datos.get("diversidad_lexica_corpus", 0))
    print("\nNoticias por fuente:")
    for fuente in sorted(datos.get("por_fuente", []), key=lambda x: x.get("noticias", 0), reverse=True):
        print(f"- {fuente['fuente']}: {fuente['noticias']} noticias")


def main():
    while True:
        print("\n" + "=" * 48)
        print("                 VERINEWS")
        print(" Exploración y recuperación de noticias")
        print("=" * 48)
        print("1. Buscar noticias por texto")
        print("2. Buscar noticias por voz")
        print("3. Explorar clasificación y grupos temáticos")
        print("4. Consultar estadísticas y fuentes")
        print("5. Recalcular grupos temáticos")
        print("0. Salir")
        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            menu_busqueda()
        elif opcion == "2":
            menu_busqueda(por_voz=True)
        elif opcion == "3":
            menu_grupos()
        elif opcion == "4":
            menu_estadisticas()
        elif opcion == "5":
            try:
                resultado = asegurar_agrupamientos(recalcular=True)
                print(
                    f"Agrupamientos actualizados: {resultado['numero_grupos']} grupos; "
                    f"Silhouette={resultado['silhouette_coseno']:.4f}"
                )
            except Exception as exc:
                print(f"No fue posible recalcular: {exc}")
        elif opcion == "0":
            print("Hasta luego. VeriNews finalizó.")
            break
        else:
            print("Opción no válida. Intente de nuevo.")


if __name__ == "__main__":
    main()
