"""Construcción de expedientes de investigación para VeriNews.

El módulo no emite veredictos de veracidad. Reúne publicaciones recuperadas,
cronología, diversidad de medios y candidatos a duplicación/similitud para que
el usuario inspeccione la evidencia y sus límites.
"""

from collections import Counter, defaultdict
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from processing.clustering import cargar_corpus
from scripts.asistente_voz import buscar_noticias

ROOT = Path(__file__).resolve().parents[1]
DATOS = ROOT / "data" / "unidad3"
UMBRAL_SIMILITUD_ALTA = 0.78
UMBRAL_COBERTURA = 0.25
MIN_PALABRAS_COMPARABLES = 100


@lru_cache(maxsize=1)
def _cargar_datos():
    """Carga una vez el corpus y la matriz en memoria durante la sesión web."""
    noticias, matriz, terminos = cargar_corpus(DATOS)
    return noticias, matriz, terminos


def limpiar_cache_corpus():
    """Permite refrescar datos después de regenerar el corpus de Unidad 3."""
    _cargar_datos.cache_clear()


def _fecha(valor):
    if not valor:
        return None
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _texto_corto(noticia):
    return (noticia.get("resumen") or noticia.get("contenido") or "").strip()[:320]


def _agrupar_fuentes(resultados, registros):
    acumulado = defaultdict(list)
    for resultado in resultados:
        indice = resultado.get("indice_corpus")
        registro = registros[indice] if isinstance(indice, int) and 0 <= indice < len(registros) else {}
        nombre = resultado.get("fuente") or registro.get("fuente_nombre") or "Fuente desconocida"
        acumulado[nombre].append((resultado, registro))

    fuentes = []
    for nombre, elementos in acumulado.items():
        fechas = [r.get("fecha") or reg.get("fecha_publicacion") or "" for r, reg in elementos]
        fechas_validas = sorted(f for f in fechas if f)
        dominios_encontrados = set()
        for r, reg in elementos:
            dominio = r.get("dominio") or reg.get("fuente_dominio") or ""
            if not dominio:
                url = r.get("url") or reg.get("url") or ""
                dominio = urlparse(url).netloc.lower() if url else ""
                if dominio.startswith("www."):
                    dominio = dominio[4:]
            if dominio:
                dominios_encontrados.add(dominio)
        dominios = sorted(dominios_encontrados)
        fuentes.append({
            "fuente": nombre,
            "dominios": dominios,
            "publicaciones": len(elementos),
            "primera_publicacion": fechas_validas[0] if fechas_validas else "",
            "ultima_publicacion": fechas_validas[-1] if fechas_validas else "",
            "tipo_fuente": "Sin determinar",
            "urls": [r.get("url", "") for r, _ in elementos if r.get("url")][:5],
        })
    return sorted(fuentes, key=lambda x: (-x["publicaciones"], x["fuente"].casefold()))


def _construir_cronologia(resultados):
    dias = defaultdict(list)
    sin_fecha = []
    for noticia in resultados:
        valor = noticia.get("fecha") or ""
        fecha = _fecha(valor)
        if fecha:
            dias[fecha.date().isoformat()].append(noticia)
        else:
            sin_fecha.append(noticia)

    cronologia = []
    for dia in sorted(dias):
        publicaciones = sorted(
            dias[dia],
            key=lambda x: (_fecha(x.get("fecha")) or datetime.min, x.get("fuente", "")),
        )
        cronologia.append({
            "fecha": dia,
            "cantidad": len(publicaciones),
            "publicaciones": [
                {
                    "titulo": n.get("titulo", "Sin título"),
                    "fuente": n.get("fuente", "Fuente desconocida"),
                    "url": n.get("url", ""),
                    "hora": n.get("fecha", ""),
                }
                for n in publicaciones
            ],
        })
    return cronologia, len(sin_fecha)


def _detectar_pares_similares(resultados, registros, matriz):
    """Busca duplicados exactos y pares con similitud textual alta.

    Los pares por similitud son candidatos a revisión, no afirmaciones de copia.
    Se exige una longitud mínima para reducir falsos positivos en titulares cortos.
    """
    # Evita que una publicación de baja relevancia para la consulta aparezca
    # como duplicada solo porque coincide con otra publicación irrelevante.
    max_score = max((float(n.get("similitud") or 0) for n in resultados), default=0.0)
    umbral_consulta = max(0.08, max_score * 0.50)
    resultados = [n for n in resultados if float(n.get("similitud") or 0) >= umbral_consulta]
    indices = [
        n.get("indice_corpus") for n in resultados
        if isinstance(n.get("indice_corpus"), int)
        and 0 <= n["indice_corpus"] < matriz.shape[0]
    ]
    if len(indices) < 2:
        return []

    posiciones = {n.get("indice_corpus"): n for n in resultados}
    similitudes = cosine_similarity(matriz[indices], matriz[indices])
    pares = {}

    # Primero se identifican coincidencias exactas a partir del hash almacenado.
    por_hash = defaultdict(list)
    for resultado in resultados:
        hash_texto = resultado.get("hash_contenido")
        if hash_texto:
            por_hash[hash_texto].append(resultado)
    for elementos in por_hash.values():
        if len(elementos) > 1:
            for i in range(len(elementos)):
                for j in range(i + 1, len(elementos)):
                    a, b = elementos[i], elementos[j]
                    clave = tuple(sorted((a["indice_corpus"], b["indice_corpus"])))
                    pares[clave] = {
                        "tipo": "duplicado_exacto",
                        "similitud": 1.0,
                        "explicacion": "Coincide el hash del contenido registrado en el corpus.",
                    }

    for i in range(len(indices)):
        idx_a = indices[i]
        a = posiciones.get(idx_a, {})
        for j in range(i + 1, len(indices)):
            idx_b = indices[j]
            b = posiciones.get(idx_b, {})
            similitud = float(similitudes[i, j])
            if similitud < UMBRAL_SIMILITUD_ALTA:
                continue
            palabras_a = int(a.get("palabras_acopio") or 0)
            palabras_b = int(b.get("palabras_acopio") or 0)
            if min(palabras_a, palabras_b) < MIN_PALABRAS_COMPARABLES:
                continue
            clave = tuple(sorted((idx_a, idx_b)))
            if clave in pares:
                continue
            pares[clave] = {
                "tipo": "similitud_alta",
                "similitud": round(similitud, 4),
                "explicacion": (
                    "Los textos presentan similitud alta; revisar si es una republicación, "
                    "una actualización o cobertura del mismo hecho."
                ),
            }

    salida = []
    for (idx_a, idx_b), datos in pares.items():
        a = posiciones.get(idx_a, {})
        b = posiciones.get(idx_b, {})
        salida.append({
            **datos,
            "noticia_a": {
                "titulo": a.get("titulo", "Sin título"),
                "fuente": a.get("fuente", "Fuente desconocida"),
                "fecha": a.get("fecha", ""),
                "url": a.get("url", ""),
            },
            "noticia_b": {
                "titulo": b.get("titulo", "Sin título"),
                "fuente": b.get("fuente", "Fuente desconocida"),
                "fecha": b.get("fecha", ""),
                "url": b.get("url", ""),
            },
        })
    salida.sort(key=lambda x: (x["tipo"] != "duplicado_exacto", -x["similitud"]))
    return salida[:15]


def _agrupar_coberturas(resultados, matriz, terminos):
    """Propone subgrupos locales de publicaciones relacionadas por TF-IDF.

    Solo considera resultados con puntuación de consulta suficiente. Los grupos
    son sugerencias de similitud textual, no confirmaciones de un mismo evento.
    """
    if len(resultados) < 2:
        return []
    max_score = max(float(n.get("similitud") or 0) for n in resultados)
    umbral_consulta = max(0.08, max_score * 0.50)
    candidatos = [
        n for n in resultados
        if float(n.get("similitud") or 0) >= umbral_consulta
        and isinstance(n.get("indice_corpus"), int)
        and 0 <= n["indice_corpus"] < matriz.shape[0]
    ]
    if len(candidatos) < 2:
        return []

    indices = [n["indice_corpus"] for n in candidatos]
    similitudes = cosine_similarity(matriz[indices])
    padre = list(range(len(indices)))

    def encontrar(x):
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    def unir(a, b):
        a, b = encontrar(a), encontrar(b)
        if a != b:
            padre[b] = a

    for i in range(len(indices)):
        for j in range(i + 1, len(indices)):
            if float(similitudes[i, j]) >= UMBRAL_COBERTURA:
                unir(i, j)

    componentes = defaultdict(list)
    for posicion in range(len(indices)):
        componentes[encontrar(posicion)].append(posicion)

    grupos = []
    for posiciones in componentes.values():
        if len(posiciones) < 2:
            continue
        ids_corpus = [indices[pos] for pos in posiciones]
        noticias_grupo = [candidatos[pos] for pos in posiciones]
        suma = np.asarray(matriz[ids_corpus].sum(axis=0)).ravel()
        top = np.argsort(suma)[::-1][:6]
        terminos_grupo = [
            terminos[int(i)] for i in top
            if int(i) < len(terminos) and suma[int(i)] > 0
        ]
        fuentes = sorted({n.get("fuente", "Fuente desconocida") for n in noticias_grupo})
        valores = [
            float(similitudes[posiciones[i], posiciones[j]])
            for i in range(len(posiciones))
            for j in range(i + 1, len(posiciones))
        ]
        noticias_grupo.sort(key=lambda n: float(n.get("similitud") or 0), reverse=True)
        grupos.append({
            "cantidad": len(noticias_grupo),
            "medios_distintos": len(fuentes),
            "fuentes": fuentes,
            "terminos_representativos": terminos_grupo,
            "similitud_interna_promedio": round(sum(valores) / len(valores), 4) if valores else 1.0,
            "noticias": [
                {
                    "titulo": n.get("titulo", "Sin título"),
                    "fuente": n.get("fuente", "Fuente desconocida"),
                    "fecha": n.get("fecha", ""),
                    "url": n.get("url", ""),
                    "similitud_consulta": n.get("similitud", 0),
                }
                for n in noticias_grupo
            ],
        })
    grupos.sort(key=lambda g: (-g["cantidad"], -g["similitud_interna_promedio"]))
    for numero, grupo in enumerate(grupos, start=1):
        grupo["grupo"] = numero
    return grupos


def construir_expediente(consulta, limite=20, metodo="tfidf"):
    """Recupera publicaciones y organiza un expediente transparente.

    metodo='tfidf' reutiliza el buscador existente. metodo='lsa' utiliza la
    variante experimental LSA si está disponible.
    """
    consulta = (consulta or "").strip()
    if not consulta:
        raise ValueError("Escriba una afirmación, titular o acontecimiento.")
    limite = max(1, min(int(limite), 30))

    if metodo == "lsa":
        from processing.lsa_retrieval import buscar_noticias_lsa
        resultados, aviso = buscar_noticias_lsa(consulta, limite=limite)
    else:
        resultados, aviso = buscar_noticias(consulta, limite=limite)
        metodo = "tfidf"

    if aviso or not resultados:
        return {
            "consulta": consulta,
            "metodo_recuperacion": metodo,
            "resultados": [],
            "fuentes": [],
            "cronologia": [],
            "grupos_cobertura": [],
            "pares_similares": [],
            "resumen": {
                "publicaciones_recuperadas": 0,
                "medios_distintos": 0,
                "publicaciones_con_contenido": 0,
                "publicaciones_solo_resumen": 0,
                "fechas_distintas": 0,
                "grupos_cobertura": 0,
            },
            "avisos": [aviso] if aviso else ["No se encontraron publicaciones relevantes."],
        }

    registros, matriz, terminos = _cargar_datos()
    # Enriquecer con datos originales del CSV, conservando la salida del buscador.
    enriquecidos = []
    for resultado in resultados:
        indice = resultado.get("indice_corpus")
        registro = registros[indice] if isinstance(indice, int) and 0 <= indice < len(registros) else {}
        noticia = dict(resultado)
        noticia["dominio"] = noticia.get("dominio") or registro.get("fuente_dominio") or ""
        noticia["cobertura_textual"] = (
            "Contenido extraído disponible"
            if (registro.get("contenido") or "").strip()
            else "Sin cuerpo extraído; se usa titular/resumen"
        )
        noticia["tipo_fuente"] = "Sin determinar"
        noticia["extracto"] = _texto_corto(registro) or noticia.get("titulo", "")
        noticia["palabras_acopio"] = int(registro.get("numero_palabras_acopio") or 0)
        enriquecidos.append(noticia)

    fuentes = _agrupar_fuentes(enriquecidos, registros)
    cronologia, sin_fecha = _construir_cronologia(enriquecidos)
    grupos_cobertura = _agrupar_coberturas(enriquecidos, matriz, terminos)
    pares = _detectar_pares_similares(enriquecidos, registros, matriz)
    con_contenido = sum(
        bool((registros[n["indice_corpus"]].get("contenido") or "").strip())
        for n in enriquecidos
        if isinstance(n.get("indice_corpus"), int)
    )
    solo_resumen = len(enriquecidos) - con_contenido
    fechas = [d for d in cronologia]
    avisos = []
    if solo_resumen:
        avisos.append(
            f"{solo_resumen} de {len(enriquecidos)} publicaciones recuperadas no tienen cuerpo "
            "de artículo extraído; el análisis usa el titular y/o resumen disponible."
        )
    if pares:
        avisos.append(
            "La similitud alta señala publicaciones que conviene revisar; no demuestra por sí sola "
            "que exista copia ni que las fuentes sean dependientes."
        )
    avisos.append(
        "El número de medios distintos no equivale al número de fuentes independientes. "
        "La clasificación primaria/secundaria permanece sin determinar cuando no hay evidencia documental."
    )

    return {
        "consulta": consulta,
        "metodo_recuperacion": metodo,
        "resultados": enriquecidos,
        "fuentes": fuentes,
        "cronologia": cronologia,
        "grupos_cobertura": grupos_cobertura,
        "pares_similares": pares,
        "resumen": {
            "publicaciones_recuperadas": len(enriquecidos),
            "medios_distintos": len(fuentes),
            "publicaciones_con_contenido": con_contenido,
            "publicaciones_solo_resumen": solo_resumen,
            "fechas_distintas": len(fechas),
            "sin_fecha": sin_fecha,
            "primera_fecha": fechas[0]["fecha"] if fechas else "",
            "ultima_fecha": fechas[-1]["fecha"] if fechas else "",
            "pares_similares": len(pares),
            "duplicados_exactos": sum(p["tipo"] == "duplicado_exacto" for p in pares),
            "grupos_cobertura": len(grupos_cobertura),
        },
        "avisos": avisos,
        "criterios": {
            "umbral_similitud_alta": UMBRAL_SIMILITUD_ALTA,
            "minimo_palabras_para_comparar": MIN_PALABRAS_COMPARABLES,
            "umbral_relativo_consulta_para_pares": 0.50,
            "umbral_similitud_cobertura": UMBRAL_COBERTURA,
            "tipo_fuente": "Sin determinar; no hay metadatos suficientes para inferir primariedad.",
        },
    }
