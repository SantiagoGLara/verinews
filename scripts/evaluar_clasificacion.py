"""Evalúa mDeBERTa zero-shot contra etiquetas humanas en un CSV."""

import argparse
import csv
import json
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from processing.topic_classifier import CATEGORIAS_DEFAULT, clasificar_registros

ROOT = Path(__file__).resolve().parents[1]


def evaluar(ruta_csv):
    ruta = Path(ruta_csv)
    with ruta.open("r", encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    validas = [f for f in filas if (f.get("categoria_real") or "").strip()]
    if not validas:
        raise ValueError("El CSV no contiene etiquetas en la columna categoria_real.")

    categorias = CATEGORIAS_DEFAULT
    fuera_catalogo = sorted({f["categoria_real"].strip() for f in validas} - set(categorias))
    if fuera_catalogo:
        raise ValueError("Etiquetas fuera del catálogo: " + ", ".join(fuera_catalogo))

    predicciones = []
    # El clasificador acepta hasta ocho registros por lote.
    for inicio in range(0, len(validas), 8):
        lote = validas[inicio:inicio + 8]
        registros = [{
            "titulo": f.get("titulo", ""),
            "resumen": f.get("texto", ""),
            "contenido": "",
            "indice_corpus": f.get("mongo_id", ""),
        } for f in lote]
        salida = clasificar_registros(registros, categorias=categorias)
        predicciones.extend((f, p) for f, p in zip(lote, salida["predicciones"]))

    y_real = [f["categoria_real"].strip() for f, _ in predicciones]
    y_pred = [p["categoria_sugerida"] for _, p in predicciones]
    etiquetas_presentes = [c for c in categorias if c in set(y_real) or c in set(y_pred)]
    informe = classification_report(
        y_real, y_pred, labels=etiquetas_presentes,
        output_dict=True, zero_division=0,
    )
    matriz = confusion_matrix(y_real, y_pred, labels=etiquetas_presentes)

    salida_dir = ruta.parent
    ruta_pred = salida_dir / "predicciones_clasificacion.csv"
    with ruta_pred.open("w", encoding="utf-8-sig", newline="") as archivo:
        campos = ["mongo_id", "titulo", "categoria_real", "categoria_sugerida", "afinidad_modelo"]
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        for fila, pred in predicciones:
            escritor.writerow({
                "mongo_id": fila.get("mongo_id", ""),
                "titulo": fila.get("titulo", ""),
                "categoria_real": fila.get("categoria_real", ""),
                "categoria_sugerida": pred.get("categoria_sugerida", ""),
                "afinidad_modelo": pred.get("afinidad_modelo", 0),
            })

    ruta_metricas = salida_dir / "metricas_clasificacion.json"
    resultado = {
        "modelo": "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
        "muestra_evaluada": len(predicciones),
        "accuracy": accuracy_score(y_real, y_pred),
        "f1_macro": informe.get("macro avg", {}).get("f1-score", 0.0),
        "classification_report": informe,
        "etiquetas": etiquetas_presentes,
        "matriz_confusion": matriz.tolist(),
        "nota": "Métricas calculadas contra etiquetas humanas. La muestra y su balance condicionan la interpretación.",
    }
    ruta_metricas.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    with (salida_dir / "matriz_confusion_clasificacion.csv").open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["real/predicha", *etiquetas_presentes])
        for etiqueta, valores in zip(etiquetas_presentes, matriz):
            escritor.writerow([etiqueta, *valores.tolist()])

    print(f"Noticias evaluadas: {len(predicciones)}")
    print(f"Accuracy: {resultado['accuracy']:.4f}")
    print(f"F1 macro: {resultado['f1_macro']:.4f}")
    print("Archivos:", ruta_pred, ruta_metricas)
    return resultado


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", default="data/unidad4/noticias_para_etiquetar.csv")
    args = parser.parse_args()
    evaluar(ROOT / args.corpus)
