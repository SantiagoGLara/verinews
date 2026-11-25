"""Agrupamiento temático no supervisado de noticias para VeriNews.

Reutiliza la matriz TF-IDF de la Unidad 3. No modifica los documentos ni los
artefactos existentes; genera un JSON adicional con grupos y métricas.
"""

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.sparse import load_npz
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parents[1]
DIRECTORIO_DATOS = ROOT / "data" / "unidad3"
ARCHIVO_SALIDA = DIRECTORIO_DATOS / "agrupamientos_kmeans.json"

# Términos frecuentes del corpus o de plantillas editoriales que aportan poca
# información para distinguir temas. Solo se excluyen del agrupamiento; el
# buscador y la matriz TF-IDF original permanecen intactos.
STOPWORDS_TEMATICAS = {
    "no", "mexic", "ayer", "hoy", "octubr", "minut", "primer",
    "digital", "notici", "public", "aparec", "primero", "suscrib", "canal",
}


def huella_archivos(directorio=DIRECTORIO_DATOS):
    """Identifica la versión de los archivos que originaron los grupos."""
    directorio = Path(directorio)
    huella = {}
    for nombre in ("noticias_procesadas.csv", "matriz_tfidf.npz", "vocabulario_tfidf.json"):
        ruta = directorio / nombre
        stat = ruta.stat()
        huella[nombre] = {"mtime_ns": stat.st_mtime_ns, "size": stat.st_size}
    return huella


def cargar_corpus(directorio=DIRECTORIO_DATOS):
    """Carga noticias, matriz TF-IDF y vocabulario manteniendo el orden de filas."""
    directorio = Path(directorio)
    rutas = {
        "noticias": directorio / "noticias_procesadas.csv",
        "matriz": directorio / "matriz_tfidf.npz",
        "vocabulario": directorio / "vocabulario_tfidf.json",
    }
    faltantes = [ruta.name for ruta in rutas.values() if not ruta.exists()]
    if faltantes:
        raise FileNotFoundError(
            "Faltan archivos de la Unidad 3: " + ", ".join(faltantes)
            + ". Ejecute primero: python -m scripts.preparar_unidad3"
        )

    with rutas["noticias"].open("r", encoding="utf-8-sig", newline="") as archivo:
        noticias = list(csv.DictReader(archivo))
    matriz = load_npz(rutas["matriz"])
    with rutas["vocabulario"].open("r", encoding="utf-8") as archivo:
        vocabulario = json.load(archivo)

    if matriz.shape[0] != len(noticias):
        raise ValueError(
            "La cantidad de filas de la matriz TF-IDF no coincide con las noticias del CSV. "
            "Vuelva a ejecutar el pipeline de Unidad 3."
        )

    terminos = [None] * matriz.shape[1]
    for termino, indice in vocabulario.items():
        indice = int(indice)
        if 0 <= indice < len(terminos):
            terminos[indice] = termino
    if any(termino is None for termino in terminos):
        raise ValueError("El vocabulario TF-IDF no coincide con las columnas de la matriz.")

    return noticias, matriz, terminos


def preparar_matriz_tematica(matriz, terminos):
    """Retira términos generales para que K-means priorice rasgos temáticos."""
    indices = [i for i, termino in enumerate(terminos) if termino not in STOPWORDS_TEMATICAS]
    if not indices:
        raise ValueError("El filtrado temático eliminó todas las características.")
    matriz_filtrada = matriz[:, indices]
    terminos_filtrados = [terminos[i] for i in indices]
    excluidos = sorted(set(terminos) - set(terminos_filtrados))
    return matriz_filtrada, terminos_filtrados, excluidos


def _resumen_noticia(noticia):
    resumen = (noticia.get("resumen") or noticia.get("contenido") or "").strip()
    return resumen[:320]


def generar_agrupamientos(
    directorio=DIRECTORIO_DATOS,
    n_clusters=14,
    random_state=42,
    n_init=10,
    top_terminos=8,
):
    """Ejecuta K-means y guarda los grupos junto con una evaluación Silhouette."""
    noticias, matriz_original, terminos_originales = cargar_corpus(directorio)
    matriz, terminos, terminos_excluidos = preparar_matriz_tematica(
        matriz_original, terminos_originales
    )
    total = matriz.shape[0]
    if not 2 <= n_clusters < total:
        raise ValueError(f"El número de grupos debe estar entre 2 y {total - 1}.")

    modelo = KMeans(
        n_clusters=n_clusters,
        init="k-means++",
        n_init=n_init,
        max_iter=300,
        random_state=random_state,
    )
    etiquetas = modelo.fit_predict(matriz)
    if len(set(etiquetas)) < 2:
        raise ValueError("K-means generó menos de dos grupos; revise el corpus.")

    # La métrica se calcula sobre todo el corpus para que sea reproducible.
    silhouette = float(silhouette_score(
        matriz, etiquetas, metric="cosine",
        sample_size=min(1000, total), random_state=random_state,
    ))

    grupos = []
    for etiqueta in range(n_clusters):
        indices = np.flatnonzero(etiquetas == etiqueta)
        centroide = modelo.cluster_centers_[etiqueta].reshape(1, -1)
        similitudes = cosine_similarity(matriz[indices], centroide).ravel()
        orden = np.argsort(similitudes)[::-1]

        pesos = modelo.cluster_centers_[etiqueta]
        indices_terminos = np.argsort(pesos)[::-1][:top_terminos]
        terminos_grupo = [
            {"termino": terminos[int(i)], "peso": round(float(pesos[int(i)]), 6)}
            for i in indices_terminos
            if pesos[int(i)] > 0
        ]

        noticias_grupo = []
        fuentes = Counter()
        fechas = []
        for posicion in orden:
            indice = int(indices[posicion])
            noticia = noticias[indice]
            fuente = noticia.get("fuente_nombre") or "Fuente desconocida"
            fecha = noticia.get("fecha_publicacion") or ""
            fuentes[fuente] += 1
            if fecha:
                fechas.append(fecha)
            noticias_grupo.append({
                "indice_corpus": indice,
                "titulo": noticia.get("titulo") or "Sin título",
                "fuente": fuente,
                "fecha": fecha,
                "url": noticia.get("url") or "",
                "resumen": _resumen_noticia(noticia),
                "similitud_centroide": round(float(similitudes[posicion]), 4),
            })

        grupos.append({
            "etiqueta_modelo": int(etiqueta),
            "cantidad": int(len(indices)),
            "porcentaje": round(100 * len(indices) / total, 2),
            "terminos_representativos": terminos_grupo,
            "fuentes": [
                {"fuente": fuente, "cantidad": cantidad}
                for fuente, cantidad in fuentes.most_common()
            ],
            "fecha_inicial": min(fechas) if fechas else "",
            "fecha_final": max(fechas) if fechas else "",
            "noticias": noticias_grupo,
        })

    # Los IDs de presentación se ordenan por tamaño; la etiqueta K-means original
    # se conserva para permitir reproducir el resultado del modelo.
    grupos.sort(key=lambda grupo: grupo["cantidad"], reverse=True)
    for numero, grupo in enumerate(grupos, start=1):
        grupo["grupo"] = numero

    resultado = {
        "generado": datetime.now().astimezone().isoformat(timespec="seconds"),
        "algoritmo": "KMeans",
        "representacion": "Matriz TF-IDF de la Unidad 3 (unigramas y bigramas)",
        "documentos": int(total),
        "caracteristicas_originales": int(matriz_original.shape[1]),
        "caracteristicas_utilizadas": int(matriz.shape[1]),
        "terminos_generales_excluidos": terminos_excluidos,
        "numero_grupos": int(n_clusters),
        "random_state": int(random_state),
        "n_init": int(n_init),
        "silhouette_coseno": round(silhouette, 6),
        "huella_archivos": huella_archivos(directorio),
        "interpretacion_metrica": (
            "Silhouette cercano a 1 indica grupos separados; cercano a 0 indica solapamiento. "
            "Un valor bajo debe interpretarse como agrupamiento exploratorio, no como temas perfectamente separados."
        ),
        "grupos": grupos,
    }

    ruta_salida = Path(directorio) / "agrupamientos_kmeans.json"
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    with ruta_salida.open("w", encoding="utf-8") as archivo:
        json.dump(resultado, archivo, ensure_ascii=False, indent=2)
    return resultado


def cargar_agrupamientos(directorio=DIRECTORIO_DATOS):
    ruta = Path(directorio) / "agrupamientos_kmeans.json"
    if not ruta.exists():
        return None
    with ruta.open("r", encoding="utf-8") as archivo:
        resultado = json.load(archivo)
    # Si el CSV o la matriz cambiaron, no reutilizar agrupamientos obsoletos.
    try:
        if resultado.get("huella_archivos") != huella_archivos(directorio):
            return None
    except FileNotFoundError:
        return None
    return resultado
