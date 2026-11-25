"""Clasificación temática zero-shot opcional con mDeBERTa NLI.

El modelo solo sugiere categorías. La puntuación es relativa a las etiquetas
candidatas y no representa veracidad, confiabilidad ni certeza factual.
"""

MODEL_NAME = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
HYPOTHESIS_TEMPLATE = "Esta noticia trata sobre {}."
CATEGORIAS_DEFAULT = [
    "Política y gobierno",
    "Economía",
    "Seguridad y justicia",
    "Sociedad",
    "Salud",
    "Tecnología y ciencia",
    "Cultura y entretenimiento",
    "Deportes",
    "Medio ambiente",
    "Otra temática",
]

_CLASIFICADOR = None


def obtener_clasificador():
    """Carga el pipeline bajo demanda; Transformers/Torch son opcionales."""
    global _CLASIFICADOR
    if _CLASIFICADOR is not None:
        return _CLASIFICADOR
    try:
        from transformers import pipeline
    except ImportError as exc:
        raise RuntimeError(
            "La clasificación zero-shot requiere dependencias opcionales. "
            "Consulte requirements-clasificacion.txt y README_UNIDAD4.md."
        ) from exc
    try:
        _CLASIFICADOR = pipeline(
            "zero-shot-classification",
            model=MODEL_NAME,
            device=-1,
        )
    except Exception as exc:
        raise RuntimeError(
            "No se pudo cargar mDeBERTa. Compruebe la instalación de PyTorch/Transformers "
            "y la conexión necesaria para descargar el modelo."
        ) from exc
    return _CLASIFICADOR


def texto_para_clasificar(noticia):
    partes = [
        noticia.get("titulo", ""),
        noticia.get("resumen", ""),
        noticia.get("contenido", ""),
    ]
    return "\n".join(str(p).strip() for p in partes if str(p or "").strip())[:3500]


def clasificar_registros(registros, categorias=None, top_n=3):
    """Devuelve categorías sugeridas para una lista de noticias.

    `registros` debe contener título, resumen y/o contenido. Se limita el tamaño
    para que la inferencia en CPU sea manejable desde la GUI local.
    """
    categorias = list(categorias or CATEGORIAS_DEFAULT)
    if len(categorias) < 2:
        raise ValueError("Se requieren al menos dos categorías candidatas.")
    if len(registros) > 8:
        raise ValueError("La clasificación desde la interfaz está limitada a 8 noticias por solicitud.")
    clasificador = obtener_clasificador()
    predicciones = []
    for noticia in registros:
        texto = texto_para_clasificar(noticia)
        if not texto:
            continue
        salida = clasificador(
            texto,
            candidate_labels=categorias,
            hypothesis_template=HYPOTHESIS_TEMPLATE,
            multi_label=False,
            truncation=True,
        )
        etiquetas = salida.get("labels", [])
        puntuaciones = salida.get("scores", [])
        predicciones.append({
            "indice_corpus": noticia.get("indice_corpus"),
            "titulo": noticia.get("titulo") or "Sin título",
            "categoria_sugerida": etiquetas[0] if etiquetas else "Sin clasificar",
            "afinidad_modelo": round(float(puntuaciones[0]), 4) if puntuaciones else 0.0,
            "alternativas": [
                {"categoria": etiqueta, "afinidad_modelo": round(float(score), 4)}
                for etiqueta, score in list(zip(etiquetas, puntuaciones))[:max(1, int(top_n))]
            ],
        })
    return {
        "modelo": MODEL_NAME,
        "categorias": categorias,
        "predicciones": predicciones,
        "nota": (
            "Sugerencias zero-shot: las afinidades son relativas a las categorías candidatas. "
            "Revise manualmente noticias ambiguas o multitemáticas; no son etiquetas verificadas."
        ),
    }
