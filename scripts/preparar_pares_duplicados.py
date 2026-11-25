"""Prepara pares de noticias para revisión humana de duplicación."""

import csv
import random
from pathlib import Path

from sklearn.metrics.pairwise import cosine_similarity

from processing.clustering import cargar_corpus

ROOT = Path(__file__).resolve().parents[1]
DATOS = ROOT / "data" / "unidad3"
SALIDA = ROOT / "data" / "unidad4" / "pares_duplicados_para_etiquetar.csv"
UMBRAL = 0.78
MIN_PALABRAS = 100


def preparar_pares(max_positivos=40, max_negativos=40, semilla=42):
    noticias, matriz, _ = cargar_corpus(DATOS)
    similitudes = cosine_similarity(matriz)
    positivos = []
    negativos = []
    for i in range(len(noticias)):
        for j in range(i + 1, len(noticias)):
            a, b = noticias[i], noticias[j]
            palabras_a = int(a.get("numero_palabras_acopio") or 0)
            palabras_b = int(b.get("numero_palabras_acopio") or 0)
            if min(palabras_a, palabras_b) < MIN_PALABRAS:
                continue
            score = float(similitudes[i, j])
            mismo_hash = bool(a.get("hash_contenido_original")) and a.get("hash_contenido_original") == b.get("hash_contenido_original")
            fila = {
                "mongo_id_a": a.get("mongo_id", ""),
                "mongo_id_b": b.get("mongo_id", ""),
                "titulo_a": a.get("titulo", ""),
                "titulo_b": b.get("titulo", ""),
                "fuente_a": a.get("fuente_nombre", ""),
                "fuente_b": b.get("fuente_nombre", ""),
                "similitud_coseno": round(score, 4),
                "prediccion_sistema": int(mismo_hash or score >= UMBRAL),
                "duplicado_real": "",
            }
            if fila["prediccion_sistema"]:
                positivos.append(fila)
            elif 0.25 <= score < UMBRAL:
                negativos.append(fila)

    rng = random.Random(semilla)
    rng.shuffle(positivos)
    rng.shuffle(negativos)
    seleccion = positivos[:max_positivos] + negativos[:max_negativos]
    rng.shuffle(seleccion)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    campos = list(seleccion[0]) if seleccion else []
    with SALIDA.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(seleccion)
    print(f"Pares preparados: {len(seleccion)}")
    print(f"Candidatos positivos del sistema: {min(len(positivos), max_positivos)}")
    print(f"Pares negativos de similitud intermedia: {min(len(negativos), max_negativos)}")
    print("Complete duplicado_real con 1 (duplicado/republicación) o 0 (cobertura distinta).")
    print("Archivo:", SALIDA)
    return SALIDA


if __name__ == "__main__":
    preparar_pares()
