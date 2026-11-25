"""Evaluación experimental de K-means para la Parte 4 de VeriNews."""

import csv
from pathlib import Path

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from processing.clustering import cargar_corpus, preparar_matriz_tematica

ROOT = Path(__file__).resolve().parents[1]
DATOS = ROOT / "data" / "unidad3"


def evaluar(valores_k=(4, 6, 8, 10, 12, 14)):
    noticias, matriz_original, terminos_originales = cargar_corpus(DATOS)
    matriz, _, terminos_excluidos = preparar_matriz_tematica(
        matriz_original, terminos_originales
    )
    resultados = []
    muestra = min(1000, len(noticias))
    for k in valores_k:
        if not 2 <= k < len(noticias):
            continue
        modelo = KMeans(
            n_clusters=k,
            init="k-means++",
            n_init=10,
            max_iter=300,
            random_state=42,
        )
        etiquetas = modelo.fit_predict(matriz)
        puntuacion = float(silhouette_score(
            matriz, etiquetas, metric="cosine",
            sample_size=muestra, random_state=42,
        ))

        # Línea base: mismo K-means sobre la matriz TF-IDF original, sin filtrar
        # términos generales. Permite medir el efecto del ajuste temático.
        modelo_base = KMeans(
            n_clusters=k, init="k-means++", n_init=10, max_iter=300, random_state=42
        )
        etiquetas_base = modelo_base.fit_predict(matriz_original)
        puntuacion_base = float(silhouette_score(
            matriz_original, etiquetas_base, metric="cosine",
            sample_size=muestra, random_state=42,
        ))

        tamaños = [int((etiquetas == etiqueta).sum()) for etiqueta in range(k)]
        resultados.append({
            "k": int(k),
            "silhouette_tfidf_original": round(puntuacion_base, 6),
            "silhouette_tfidf_filtrado": round(puntuacion, 6),
            "grupo_mas_pequeno": min(tamaños),
            "grupo_mas_grande": max(tamaños),
            "noticias": len(noticias),
            "caracteristicas": int(matriz.shape[1]),
        })

    resultados.sort(key=lambda x: x["k"])
    ruta = DATOS / "evaluacion_kmeans.csv"
    with ruta.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(resultados[0]))
        escritor.writeheader()
        escritor.writerows(resultados)

    print("Evaluación de K-means sobre el corpus VeriNews")
    print(f"Características TF-IDF originales: {matriz_original.shape[1]}")
    print(f"Características usadas: {matriz.shape[1]}")
    print(f"Términos generales excluidos: {len(terminos_excluidos)}")
    print("k | TF-IDF original | TF-IDF filtrado | Grupo mínimo | Grupo máximo")
    for item in resultados:
        print(
            f"{item['k']:2} | {item['silhouette_tfidf_original']:.6f} "
            f"| {item['silhouette_tfidf_filtrado']:.6f} "
            f"| {item['grupo_mas_pequeno']:12} | {item['grupo_mas_grande']:12}"
        )
    mejor = max(resultados, key=lambda x: x["silhouette_tfidf_filtrado"])
    mejora_absoluta = (
        mejor["silhouette_tfidf_filtrado"] - mejor["silhouette_tfidf_original"]
    )
    mejora_relativa = (
        100 * mejora_absoluta / mejor["silhouette_tfidf_original"]
        if mejor["silhouette_tfidf_original"] else 0.0
    )
    print(
        f"\nMayor Silhouette filtrado en el rango evaluado: k={mejor['k']} "
        f"({mejor['silhouette_tfidf_filtrado']:.6f})."
    )
    print(
        f"Comparación para k={mejor['k']}: "
        f"{mejor['silhouette_tfidf_original']:.6f} → "
        f"{mejor['silhouette_tfidf_filtrado']:.6f} "
        f"({mejora_absoluta:+.6f}; {mejora_relativa:+.1f}%)."
    )
    print("Archivo generado:", ruta)
    interpretacion = (
        "Silhouette cercano a 1 indica grupos compactos y separados; cercano a 0 indica "
        "solapamiento. Los resultados de este corpus son bajos y deben interpretarse "
        "como agrupamiento exploratorio, no como separación temática fuerte."
    )
    print("Interpretación:", interpretacion)

    ruta_md = DATOS / "evaluacion_kmeans.md"
    lineas = [
        "# Evaluación experimental de K-means — VeriNews",
        "",
        f"- Noticias evaluadas: {len(noticias)}",
        f"- Características TF-IDF originales: {matriz_original.shape[1]}",
        f"- Características utilizadas: {matriz.shape[1]}",
        f"- Términos generales excluidos del agrupamiento: {len(terminos_excluidos)}",
        "- Distancia de Silhouette: coseno",
        f"- Parámetros: `random_state=42`, `n_init=10`, `max_iter=300`, muestra de evaluación={muestra}",
        "",
        "| k | TF-IDF original | TF-IDF filtrado | Grupo mínimo | Grupo máximo |",
        "|---:|---:|---:|---:|---:|",
    ]
    for item in resultados:
        lineas.append(
            f"| {item['k']} | {item['silhouette_tfidf_original']:.6f} | "
            f"{item['silhouette_tfidf_filtrado']:.6f} | "
            f"{item['grupo_mas_pequeno']} | {item['grupo_mas_grande']} |"
        )
    lineas.extend([
        "",
        f"**Mayor Silhouette filtrado en el rango evaluado:** k={mejor['k']} "
        f"({mejor['silhouette_tfidf_filtrado']:.6f}).",
        "",
        f"Para k={mejor['k']}, la línea base obtuvo {mejor['silhouette_tfidf_original']:.6f} "
        f"y la representación filtrada {mejor['silhouette_tfidf_filtrado']:.6f} "
        f"(diferencia {mejora_absoluta:+.6f}; {mejora_relativa:+.1f}% relativo).",
        "",
        "La columna TF-IDF original es la línea base sin exclusión de términos generales; "
        "la columna TF-IDF filtrado corresponde a la representación utilizada por VeriNews Parte 4.",
        "",
        interpretacion,
        "",
        "La métrica no demuestra que dos noticias describan exactamente el mismo acontecimiento "
        "ni que sus fuentes sean independientes. Los grupos requieren inspección de títulos, "
        "fechas, fuentes y enlaces.",
    ])
    ruta_md.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("Informe generado:", ruta_md)
    return resultados


if __name__ == "__main__":
    evaluar()
