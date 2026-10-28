"""Estadísticas de frecuencia para el corpus de noticias VeriNews."""

from collections import Counter, defaultdict
from nltk import FreqDist
from nltk.util import ngrams


def calcular_estadisticas(registros, limite=30):
    tokens_por_documento = [
        (r.get("tokens_limpios") or "").split()
        for r in registros
    ]
    todos_tokens = [token for lista in tokens_por_documento for token in lista]
    distribucion = FreqDist(todos_tokens)
    bigramas = FreqDist(
        ngrama
        for tokens in tokens_por_documento
        for ngrama in ngrams(tokens, 2)
    )
    trigramas = FreqDist(
        ngrama
        for tokens in tokens_por_documento
        for ngrama in ngrams(tokens, 3)
    )

    por_fuente = defaultdict(lambda: {"noticias": 0, "tokens_limpios": 0})
    for registro, tokens in zip(registros, tokens_por_documento):
        fuente = registro.get("fuente_nombre") or "Sin fuente"
        por_fuente[fuente]["noticias"] += 1
        por_fuente[fuente]["tokens_limpios"] += len(tokens)

    total_tokens = len(todos_tokens)
    vocabulario = set(todos_tokens)
    diversidad = len(vocabulario) / total_tokens if total_tokens else 0.0

    return {
        "total_noticias": len(registros),
        "noticias_con_texto": sum(bool((r.get("texto_original") or "").strip()) for r in registros),
        "tokens_limpios_total": total_tokens,
        "vocabulario_total": len(vocabulario),
        "diversidad_lexica_corpus": round(diversidad, 6),
        "frecuencias_palabras": [
            {"termino": termino, "frecuencia": frecuencia}
            for termino, frecuencia in distribucion.most_common(limite)
        ],
        "frecuencias_bigramas": [
            {"n": 2, "ngrama": " ".join(ng), "frecuencia": frecuencia}
            for ng, frecuencia in bigramas.most_common(limite)
        ],
        "frecuencias_trigramas": [
            {"n": 3, "ngrama": " ".join(ng), "frecuencia": frecuencia}
            for ng, frecuencia in trigramas.most_common(limite)
        ],
        "por_fuente": [
            {"fuente": fuente, **valores}
            for fuente, valores in sorted(por_fuente.items())
        ],
    }
