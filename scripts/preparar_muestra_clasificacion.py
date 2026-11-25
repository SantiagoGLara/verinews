"""Genera una muestra reproducible de 100 noticias para etiquetado humano."""

import csv
import random
from pathlib import Path

from processing.clustering import cargar_corpus

ROOT = Path(__file__).resolve().parents[1]
DATOS = ROOT / "data" / "unidad3"
SALIDA = ROOT / "data" / "unidad4" / "noticias_para_etiquetar.csv"


def preparar_muestra(tamano=100, semilla=42):
    noticias, _, _ = cargar_corpus(DATOS)
    rng = random.Random(semilla)
    indices = list(range(len(noticias)))
    rng.shuffle(indices)
    seleccion = indices[:min(int(tamano), len(indices))]
    campos = ["mongo_id", "titulo", "texto", "fuente", "fecha", "categoria_real"]
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        for indice in seleccion:
            noticia = noticias[indice]
            texto = " ".join([
                noticia.get("titulo", ""),
                noticia.get("resumen", ""),
                noticia.get("contenido", ""),
            ]).strip()
            escritor.writerow({
                "mongo_id": noticia.get("mongo_id", ""),
                "titulo": noticia.get("titulo", ""),
                "texto": texto,
                "fuente": noticia.get("fuente_nombre", ""),
                "fecha": noticia.get("fecha_publicacion", ""),
                "categoria_real": "",
            })
    print(f"Muestra creada: {SALIDA}")
    print(f"Noticias: {len(seleccion)} | semilla: {semilla}")
    print("Complete categoria_real mediante revisión humana antes de evaluar el modelo.")
    return SALIDA


if __name__ == "__main__":
    preparar_muestra()
