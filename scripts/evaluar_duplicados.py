"""Calcula precisión, recall y F1 para candidatos de duplicación revisados."""

import argparse
import csv
import json
from pathlib import Path

from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]


def evaluar(ruta_csv):
    ruta = Path(ruta_csv)
    with ruta.open("r", encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    etiquetadas = [f for f in filas if str(f.get("duplicado_real", "")).strip() in {"0", "1"}]
    if not etiquetadas:
        raise ValueError("No hay pares etiquetados. Complete duplicado_real con 0 o 1.")
    real = [int(f["duplicado_real"]) for f in etiquetadas]
    pred = [int(f["prediccion_sistema"]) for f in etiquetadas]
    resultado = {
        "pares_evaluados": len(etiquetadas),
        "precision": precision_score(real, pred, zero_division=0),
        "recall": recall_score(real, pred, zero_division=0),
        "f1": f1_score(real, pred, zero_division=0),
        "matriz_confusion": confusion_matrix(real, pred, labels=[0, 1]).tolist(),
        "umbral_similitud": 0.78,
        "nota": "El resultado depende de la definición humana de duplicado/republicación y del conjunto de pares revisado.",
    }
    salida = ruta.parent / "metricas_duplicados.json"
    salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Pares evaluados: {resultado['pares_evaluados']}")
    print(f"Precisión: {resultado['precision']:.4f} | Recall: {resultado['recall']:.4f} | F1: {resultado['f1']:.4f}")
    print("Matriz de confusión:", resultado["matriz_confusion"])
    print("Archivo:", salida)
    return resultado


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pares", default="data/unidad4/pares_duplicados_para_etiquetar.csv")
    args = parser.parse_args()
    evaluar(ROOT / args.pares)
