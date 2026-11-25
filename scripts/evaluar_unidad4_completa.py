"""Ejecuta las comparaciones experimentales reproducibles de la Parte 4."""

import argparse

from scripts.evaluar_recuperacion import evaluar as evaluar_recuperacion
from scripts.evaluar_unidad4 import evaluar as evaluar_kmeans


def main(incluir_mongodb=False):
    print("\n" + "=" * 68)
    print("VERINEWS · EVALUACIÓN EXPERIMENTAL DE UNIDAD 4")
    print("=" * 68)
    print("\n[1/2] Agrupamiento temático K-means")
    evaluar_kmeans()
    print("\n[2/2] Recuperación TF-IDF frente a LSA")
    evaluar_recuperacion()
    if incluir_mongodb:
        print("\n[3/3] Comparación con la búsqueda anterior MongoDB $text")
        from scripts.evaluar_busqueda_legacy import evaluar as evaluar_legacy
        evaluar_legacy()
    print("\nComparaciones principales terminadas.")
    if not incluir_mongodb:
        print("Si MongoDB está iniciado y contiene la misma colección/índice de la versión anterior, agregue --mongodb para compararla con TF-IDF y LSA.")
    print("Para completar la evaluación de duplicados:")
    print("  1. Revise data/unidad4/pares_duplicados_para_etiquetar.csv")
    print("  2. Complete duplicado_real con 1 o 0")
    print("  3. Ejecute python -m scripts.evaluar_duplicados")
    print("Para completar la evaluación de clasificación:")
    print("  1. Complete categoria_real en noticias_para_etiquetar.csv")
    print("  2. Instale requirements-clasificacion.txt")
    print("  3. Ejecute python -m scripts.evaluar_clasificacion")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mongodb", action="store_true", help="Incluye la búsqueda MongoDB $text de la versión anterior.")
    args = parser.parse_args()
    main(incluir_mongodb=args.mongodb)
