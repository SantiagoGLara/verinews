"""Compara la recuperación TF-IDF original con la variante experimental LSA."""

import csv
import json
import platform
from pathlib import Path

from processing.lsa_retrieval import buscar_noticias_lsa, preparar_indice_lsa
from scripts.asistente_voz import buscar_noticias

ROOT = Path(__file__).resolve().parents[1]
DATOS = ROOT / "data" / "unidad4"
ARCHIVO_CONSULTAS = DATOS / "consultas_relevancia.json"


def _metricas(ranking, relevantes, k=5):
    relevantes = set(relevantes)
    primeros = ranking[:k]
    aciertos = sum(1 for identificador in primeros if identificador in relevantes)
    precision = aciertos / k if k else 0.0
    recall = aciertos / len(relevantes) if relevantes else 0.0
    reciprocal_rank = 0.0
    for posicion, identificador in enumerate(ranking, start=1):
        if identificador in relevantes:
            reciprocal_rank = 1.0 / posicion
            break
    return precision, recall, reciprocal_rank


def evaluar():
    if not ARCHIVO_CONSULTAS.exists():
        raise FileNotFoundError(f"No existe {ARCHIVO_CONSULTAS}")
    conjunto = json.loads(ARCHIVO_CONSULTAS.read_text(encoding="utf-8"))
    filas = []

    # Construye el índice LSA una sola vez para toda la evaluación.
    _, _, meta_lsa = preparar_indice_lsa()
    for caso in conjunto["consultas"]:
        consulta = caso["consulta"]
        relevantes = set(caso["relevantes"])
        resultados_tfidf, aviso_tfidf = buscar_noticias(consulta, limite=10)
        resultados_lsa, aviso_lsa = buscar_noticias_lsa(consulta, limite=10)
        if aviso_tfidf or aviso_lsa:
            raise RuntimeError(f"No se pudo evaluar la consulta '{consulta}': {aviso_tfidf or aviso_lsa}")

        ranking_tfidf = [r.get("mongo_id", "") for r in resultados_tfidf]
        ranking_lsa = [r.get("mongo_id", "") for r in resultados_lsa]
        p5_t, r5_t, mrr_t = _metricas(ranking_tfidf, relevantes, 5)
        p5_l, r5_l, mrr_l = _metricas(ranking_lsa, relevantes, 5)
        p10_t, r10_t, _ = _metricas(ranking_tfidf, relevantes, 10)
        p10_l, r10_l, _ = _metricas(ranking_lsa, relevantes, 10)
        filas.append({
            "consulta": consulta,
            "relevantes_etiquetados": len(relevantes),
            "precision_at_5_tfidf": round(p5_t, 4),
            "precision_at_5_lsa": round(p5_l, 4),
            "recall_at_5_tfidf": round(r5_t, 4),
            "recall_at_5_lsa": round(r5_l, 4),
            "mrr_at_10_tfidf": round(mrr_t, 4),
            "mrr_at_10_lsa": round(mrr_l, 4),
            "precision_at_10_tfidf": round(p10_t, 4),
            "precision_at_10_lsa": round(p10_l, 4),
            "recall_at_10_tfidf": round(r10_t, 4),
            "recall_at_10_lsa": round(r10_l, 4),
        })

    columnas = list(filas[0])
    ruta_csv = DATOS / "evaluacion_recuperacion.csv"
    with ruta_csv.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas)

    metricas = [c for c in columnas if c != "consulta" and c != "relevantes_etiquetados"]
    promedios = {m: sum(float(f[m]) for f in filas) / len(filas) for m in metricas}
    lineas = [
        "# Evaluación comparativa de recuperación — VeriNews",
        "",
        f"- Consultas evaluadas: {len(filas)}",
        f"- Python utilizado: {platform.python_version()}",
        f"- Publicaciones relevantes etiquetadas: {sum(f['relevantes_etiquetados'] for f in filas)}",
        f"- Componentes LSA: {meta_lsa['componentes']}",
        f"- scikit-learn utilizado: {meta_lsa.get('sklearn_version', 'desconocido')}",
        f"- Varianza explicada acumulada por LSA: {meta_lsa['varianza_explicada_acumulada']:.4f}",
        "- Línea base: buscador TF-IDF de Unidad 3.",
        "- Variante: TruncatedSVD (LSA) aplicado sobre la misma matriz TF-IDF.",
        "",
        "## Resultados por consulta",
        "",
        "| Consulta | P@5 TF-IDF | P@5 LSA | R@5 TF-IDF | R@5 LSA | MRR@10 TF-IDF | MRR@10 LSA |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for f in filas:
        lineas.append(
            f"| {f['consulta']} | {f['precision_at_5_tfidf']:.3f} | {f['precision_at_5_lsa']:.3f} "
            f"| {f['recall_at_5_tfidf']:.3f} | {f['recall_at_5_lsa']:.3f} "
            f"| {f['mrr_at_10_tfidf']:.3f} | {f['mrr_at_10_lsa']:.3f} |"
        )
    lineas.extend([
        "",
        "## Promedios del conjunto piloto",
        "",
        "| Métrica | TF-IDF | LSA |",
        "|---|---:|---:|",
    ])
    for nombre, tfidf, lsa in [
        ("Precision@5", promedios["precision_at_5_tfidf"], promedios["precision_at_5_lsa"]),
        ("Recall@5", promedios["recall_at_5_tfidf"], promedios["recall_at_5_lsa"]),
        ("MRR@10", promedios["mrr_at_10_tfidf"], promedios["mrr_at_10_lsa"]),
        ("Precision@10", promedios["precision_at_10_tfidf"], promedios["precision_at_10_lsa"]),
        ("Recall@10", promedios["recall_at_10_tfidf"], promedios["recall_at_10_lsa"]),
    ]:
        lineas.append(f"| {nombre} | {tfidf:.4f} | {lsa:.4f} |")

    delta_p5 = promedios["precision_at_5_lsa"] - promedios["precision_at_5_tfidf"]
    delta_r5 = promedios["recall_at_5_lsa"] - promedios["recall_at_5_tfidf"]
    delta_mrr = promedios["mrr_at_10_lsa"] - promedios["mrr_at_10_tfidf"]
    lineas.extend([
        "",
        "## Interpretación",
        "",
        f"- Diferencia LSA − TF-IDF en Precision@5: {delta_p5:+.4f}.",
        f"- Diferencia LSA − TF-IDF en Recall@5: {delta_r5:+.4f}.",
        f"- Diferencia LSA − TF-IDF en MRR@10: {delta_mrr:+.4f}.",
        "- LSA se mantiene como alternativa experimental; no sustituye al buscador original automáticamente.",
        "- El conjunto es pequeño (consultas de acontecimientos presentes en este corpus) y las etiquetas se revisaron manualmente a partir de títulos/resúmenes. No representa todos los temas ni permite generalizar a otros corpus.",
        "- Los resultados miden recuperación de publicaciones relacionadas, no veracidad, exactitud factual ni independencia de las fuentes.",
        "",
        "El detalle numérico se conserva en `evaluacion_recuperacion.csv`.",
    ])
    ruta_md = DATOS / "evaluacion_recuperacion.md"
    ruta_md.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("Evaluación de recuperación terminada.")
    print(f"Consultas: {len(filas)} | relevantes etiquetadas: {sum(f['relevantes_etiquetados'] for f in filas)}")
    print(f"P@5: TF-IDF={promedios['precision_at_5_tfidf']:.4f} | LSA={promedios['precision_at_5_lsa']:.4f}")
    print(f"R@5: TF-IDF={promedios['recall_at_5_tfidf']:.4f} | LSA={promedios['recall_at_5_lsa']:.4f}")
    print(f"MRR@10: TF-IDF={promedios['mrr_at_10_tfidf']:.4f} | LSA={promedios['mrr_at_10_lsa']:.4f}")
    print("Archivos:", ruta_csv, ruta_md)
    return filas, promedios


if __name__ == "__main__":
    evaluar()
