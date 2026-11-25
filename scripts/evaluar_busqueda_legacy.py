"""Compara la búsqueda MongoDB $text de la versión anterior con TF-IDF/LSA.

Requiere MongoDB local con el índice de texto creado por database.mongo.crear_indices
Y la misma colección/corpus utilizada para generar noticias_procesadas.csv.
"""

import csv
import json
from pathlib import Path

from processing.lsa_retrieval import buscar_noticias_lsa
from scripts.asistente_voz import buscar_noticias
from scripts.evaluar_recuperacion import _metricas

ROOT = Path(__file__).resolve().parents[1]
DATOS = ROOT / "data" / "unidad3"
EVALUACION = ROOT / "data" / "unidad4"
CONSULTAS = EVALUACION / "consultas_relevancia.json"


def evaluar():
    try:
        from database.mongo import obtener_coleccion
    except ImportError as exc:
        raise RuntimeError("Falta pymongo. Instale requirements.txt.") from exc

    casos = json.loads(CONSULTAS.read_text(encoding="utf-8"))["consultas"]
    with (DATOS / "noticias_procesadas.csv").open("r", encoding="utf-8-sig", newline="") as archivo:
        noticias = list(csv.DictReader(archivo))
    url_a_id = {}
    for noticia in noticias:
        for url in (noticia.get("url", ""), noticia.get("url_final", "")):
            if url:
                url_a_id[url] = noticia.get("mongo_id", "")

    cliente, coleccion = obtener_coleccion()
    filas = []
    try:
        for caso in casos:
            consulta = caso["consulta"]
            relevantes = set(caso["relevantes"])
            pipeline = [
                {"$match": {"$text": {"$search": consulta}}},
                {"$set": {"score": {"$meta": "textScore"}}},
                {"$sort": {"score": {"$meta": "textScore"}}},
                {"$limit": 10},
                {"$project": {"_id": 0, "url": 1, "score": 1}},
            ]
            docs = list(coleccion.aggregate(pipeline))
            ranking_mongo = [url_a_id.get(d.get("url", ""), "") for d in docs]
            ranking_mongo = [identificador for identificador in ranking_mongo if identificador]
            ranking_tfidf, aviso_tfidf = buscar_noticias(consulta, limite=10)
            ranking_lsa, aviso_lsa = buscar_noticias_lsa(consulta, limite=10)
            if aviso_tfidf or aviso_lsa:
                raise RuntimeError(f"No se pudo recuperar la consulta '{consulta}'.")

            metricas = {}
            for nombre, ranking in [
                ("mongodb", ranking_mongo),
                ("tfidf", [r.get("mongo_id", "") for r in ranking_tfidf]),
                ("lsa", [r.get("mongo_id", "") for r in ranking_lsa]),
            ]:
                p5, r5, mrr = _metricas(ranking, relevantes, 5)
                metricas[f"precision_at_5_{nombre}"] = round(p5, 4)
                metricas[f"recall_at_5_{nombre}"] = round(r5, 4)
                metricas[f"mrr_at_10_{nombre}"] = round(mrr, 4)
            filas.append({"consulta": consulta, "relevantes_etiquetados": len(relevantes), **metricas})
    finally:
        cliente.close()

    salida = EVALUACION / "evaluacion_busqueda_legacy.csv"
    with salida.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)

    metricas = [k for k in filas[0] if k not in {"consulta", "relevantes_etiquetados"}]
    promedios = {k: sum(f[k] for f in filas) / len(filas) for k in metricas}
    lineas = [
        "# Comparación con la búsqueda de la versión anterior (MongoDB $text)",
        "",
        f"- Consultas: {len(filas)}",
        f"- Publicaciones relevantes etiquetadas: {sum(f['relevantes_etiquetados'] for f in filas)}",
        "- MongoDB utiliza el índice de texto con pesos de título=5, resumen=3 y contenido=1, como en `database/mongo.py`.",
        "- Las métricas se calculan sobre los mismos mongo_id relevantes y el mismo top 10.",
        "",
        "| Método | Precision@5 | Recall@5 | MRR@10 |",
        "|---|---:|---:|---:|",
    ]
    for metodo, etiqueta in [("mongodb", "MongoDB $text (versión anterior)"), ("tfidf", "TF-IDF (Unidad 3)"), ("lsa", "LSA (experimental)")]:
        lineas.append(
            f"| {etiqueta} | {promedios[f'precision_at_5_{metodo}']:.4f} "
            f"| {promedios[f'recall_at_5_{metodo}']:.4f} | {promedios[f'mrr_at_10_{metodo}']:.4f} |"
        )
    lineas.extend([
        "",
        "Esta comparación requiere que MongoDB contenga el mismo corpus y el índice de texto de la versión anterior. Si la colección difiere del CSV exportado, los resultados que no se puedan mapear por URL se excluyen y el reporte puede quedar incompleto.",
        "El conjunto de relevancia es piloto y se revisó manualmente a partir de títulos/resúmenes. Las métricas miden recuperación, no veracidad ni independencia de fuentes.",
    ])
    reporte = EVALUACION / "evaluacion_busqueda_legacy.md"
    reporte.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("Comparación MongoDB $text vs TF-IDF vs LSA terminada.")
    for metodo in ("mongodb", "tfidf", "lsa"):
        print(
            f"{metodo}: P@5={promedios[f'precision_at_5_{metodo}']:.4f}, "
            f"R@5={promedios[f'recall_at_5_{metodo}']:.4f}, "
            f"MRR@10={promedios[f'mrr_at_10_{metodo}']:.4f}"
        )
    print("Archivos:", salida, reporte)
    return filas, promedios


if __name__ == "__main__":
    evaluar()
