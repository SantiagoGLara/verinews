"""Vectorización BoW y TF-IDF de las noticias procesadas."""

import json
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from scipy.sparse import save_npz


def vectorizar(registros, directorio_salida, max_features=10000):
    salida = Path(directorio_salida)
    salida.mkdir(parents=True, exist_ok=True)
    textos = [r.get("texto_stem", "") or "" for r in registros]

    if not textos or not any(texto.strip() for texto in textos):
        raise ValueError(
            "No hay tokens para vectorizar. Revise el contenido recuperado y el preprocesamiento."
        )

    parametros = {
        "tokenizer": str.split,
        "preprocessor": None,
        "token_pattern": None,
        "lowercase": False,
    }
    vectorizador_bow = CountVectorizer(
        **parametros,
        binary=False,
        ngram_range=(1, 1),
        max_features=max_features,
    )
    matriz_bow = vectorizador_bow.fit_transform(textos)
    save_npz(salida / "matriz_bow.npz", matriz_bow)
    joblib.dump(vectorizador_bow, salida / "vectorizador_bow.joblib")

    vectorizador_tfidf = TfidfVectorizer(
        **parametros,
        ngram_range=(1, 2),
        min_df=1,
        max_df=1.0,
        max_features=max_features,
        sublinear_tf=True,
        norm="l2",
    )
    matriz_tfidf = vectorizador_tfidf.fit_transform(textos)
    save_npz(salida / "matriz_tfidf.npz", matriz_tfidf)
    joblib.dump(vectorizador_tfidf, salida / "vectorizador_tfidf.joblib")

    vocabulario_bow = {
        termino: int(indice)
        for termino, indice in vectorizador_bow.vocabulary_.items()
    }
    vocabulario_tfidf = {
        termino: int(indice)
        for termino, indice in vectorizador_tfidf.vocabulary_.items()
    }
    with (salida / "vocabulario_bow.json").open("w", encoding="utf-8") as f:
        json.dump(vocabulario_bow, f, ensure_ascii=False, indent=2, sort_keys=True)
    with (salida / "vocabulario_tfidf.json").open("w", encoding="utf-8") as f:
        json.dump(vocabulario_tfidf, f, ensure_ascii=False, indent=2, sort_keys=True)

    return {
        "documentos": int(matriz_tfidf.shape[0]),
        "terminos_bow": int(matriz_bow.shape[1]),
        "terminos_tfidf_con_bigramas": int(matriz_tfidf.shape[1]),
        "forma_matriz_bow": list(matriz_bow.shape),
        "forma_matriz_tfidf": list(matriz_tfidf.shape),
        "elementos_no_cero_bow": int(matriz_bow.nnz),
        "elementos_no_cero_tfidf": int(matriz_tfidf.nnz),
        "densidad_tfidf": float(matriz_tfidf.nnz / (matriz_tfidf.shape[0] * matriz_tfidf.shape[1]))
        if matriz_tfidf.shape[0] and matriz_tfidf.shape[1] else 0.0,
        "formato_matriz": "matriz dispersa CSR guardada como .npz",
        "vectorizador_tfidf": "TfidfVectorizer, ngram_range=(1, 2), sublinear_tf=True",
    }
