"""Recuperación experimental mediante LSA (TF-IDF + TruncatedSVD).

LSA se ofrece como alternativa experimental a la búsqueda TF-IDF original.
No reemplaza el buscador base: la evaluación determina si conviene utilizarlo.
"""

import csv
import json
import threading
from pathlib import Path

import joblib
import numpy as np
from scipy.sparse import load_npz
import sklearn
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

from processing.preprocessor import obtener_stopwords, preprocesar_texto

ROOT = Path(__file__).resolve().parents[1]
DATOS = ROOT / "data" / "unidad3"
SALIDA = ROOT / "data" / "unidad4"
MODELO = SALIDA / "lsa_model.joblib"
VECTORES = SALIDA / "lsa_corpus.npy"
METADATOS = SALIDA / "lsa_metadata.json"
_LOCK = threading.Lock()
_CACHE = None


def _huella():
    ruta = DATOS / "matriz_tfidf.npz"
    stat = ruta.stat()
    return {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def preparar_indice_lsa(n_componentes=100):
    """Carga el índice LSA o lo genera si no existe o cambió el corpus."""
    global _CACHE
    with _LOCK:
        if _CACHE is not None:
            return _CACHE
        SALIDA.mkdir(parents=True, exist_ok=True)
        huella = _huella()
        if MODELO.exists() and VECTORES.exists() and METADATOS.exists():
            try:
                meta = json.loads(METADATOS.read_text(encoding="utf-8"))
                if meta.get("huella") == huella and meta.get("sklearn_version") == sklearn.__version__:
                    modelo = joblib.load(MODELO)
                    corpus = np.load(VECTORES)
                    _CACHE = (modelo, corpus, meta)
                    return _CACHE
            except (OSError, ValueError, json.JSONDecodeError):
                pass

        matriz = load_npz(DATOS / "matriz_tfidf.npz")
        componentes = min(int(n_componentes), matriz.shape[0] - 1, matriz.shape[1] - 1)
        if componentes < 2:
            raise ValueError("El corpus es demasiado pequeño para generar el índice LSA.")
        modelo = TruncatedSVD(n_components=componentes, n_iter=7, random_state=42)
        corpus = normalize(modelo.fit_transform(matriz))
        meta = {
            "huella": huella,
            "componentes": componentes,
            "varianza_explicada_acumulada": float(modelo.explained_variance_ratio_.sum()),
            "algoritmo": "TruncatedSVD sobre TF-IDF; vectores normalizados",
            "random_state": 42,
            "sklearn_version": sklearn.__version__,
        }
        joblib.dump(modelo, MODELO)
        np.save(VECTORES, corpus)
        METADATOS.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        _CACHE = (modelo, corpus, meta)
        return _CACHE


def limpiar_cache_lsa():
    global _CACHE
    with _LOCK:
        _CACHE = None


def buscar_noticias_lsa(consulta, limite=10):
    """Busca noticias usando la proyección latente LSA del corpus TF-IDF."""
    consulta = (consulta or "").strip()
    if not consulta:
        return [], "Escriba una consulta para buscar noticias."

    ruta_vectorizador = DATOS / "vectorizador_tfidf.joblib"
    ruta_csv = DATOS / "noticias_procesadas.csv"
    if not ruta_vectorizador.exists() or not ruta_csv.exists():
        raise FileNotFoundError("Faltan los artefactos TF-IDF de Unidad 3.")

    vectorizador = joblib.load(ruta_vectorizador)
    procesado = preprocesar_texto(consulta, obtener_stopwords())
    texto = procesado["texto_stem"]
    if not texto.strip():
        return [], "La consulta no contiene términos suficientes después del preprocesamiento."
    vector_consulta = vectorizador.transform([texto])
    if vector_consulta.nnz == 0:
        return [], "No encontré términos de la consulta dentro del vocabulario indexado."

    modelo, corpus_lsa, _ = preparar_indice_lsa()
    consulta_lsa = normalize(modelo.transform(vector_consulta))
    puntajes = cosine_similarity(consulta_lsa, corpus_lsa).ravel()
    indices = puntajes.argsort()[::-1][:max(1, min(int(limite), 30))]

    with ruta_csv.open("r", encoding="utf-8-sig", newline="") as archivo:
        noticias = list(csv.DictReader(archivo))

    resultados = []
    for indice in indices:
        puntaje = float(puntajes[indice])
        if puntaje <= 0:
            continue
        noticia = noticias[int(indice)]
        resultados.append({
            "titulo": noticia.get("titulo") or "Sin título",
            "fuente": noticia.get("fuente_nombre") or "Fuente desconocida",
            "fecha": noticia.get("fecha_publicacion") or "",
            "url": noticia.get("url") or "",
            "resumen": noticia.get("resumen") or "",
            "contenido": noticia.get("contenido") or "",
            "similitud": round(puntaje, 4),
            "indice_corpus": int(indice),
            "mongo_id": noticia.get("mongo_id") or "",
            "dominio": noticia.get("fuente_dominio") or "",
            "hash_contenido": noticia.get("hash_contenido_original") or "",
            "palabras_acopio": int(noticia.get("numero_palabras_acopio") or 0),
            "cobertura_textual": (
                "Contenido extraído disponible"
                if (noticia.get("contenido") or "").strip()
                else "Sin cuerpo extraído; se usa titular/resumen"
            ),
        })
    if not resultados:
        return [], "No encontré noticias con similitud latente positiva."
    return resultados, ""
