"""Exportadores CSV, JSON y SQLite para los datos de VeriNews."""

import csv
import json
import sqlite3
from datetime import date, datetime
from pathlib import Path


CSV_FIELDS = [
    "mongo_id", "url", "url_final", "titulo", "autor", "fecha_publicacion",
    "resumen", "contenido", "fuente_nombre", "fuente_tipo_acopio",
    "fuente_dominio", "categorias", "metodo_acopio", "status_http",
    "error_scraping", "numero_palabras_acopio", "hash_contenido_original",
    "palabras_clave_originales", "texto_original", "texto_normalizado",
    "tokens_alfabeticos", "tokens_limpios", "texto_limpio", "tokens_stem",
    "texto_stem", "numero_tokens_originales", "numero_tokens_alfabeticos",
    "numero_tokens_limpios", "vocabulario_documento", "diversidad_lexica",
]


def json_seguro(valor):
    """Convierte tipos de Mongo/Python a valores serializables en JSON."""
    if isinstance(valor, dict):
        return {str(k): json_seguro(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [json_seguro(v) for v in valor]
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if valor is None or isinstance(valor, (str, int, float, bool)):
        return valor
    # ObjectId y cualquier otro tipo especial de MongoDB.
    return str(valor)


def fecha_iso(valor):
    if valor is None:
        return ""
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    return str(valor)


def construir_registro(documento, procesado):
    fuente = documento.get("fuente") or {}
    acopio = documento.get("acopio") or {}
    analisis = documento.get("analisis") or {}
    tokens_originales = procesado["tokens_originales"]
    tokens_alfabeticos = procesado["tokens_alfabeticos"]
    tokens_limpios = procesado["tokens_limpios"]
    vocabulario = len(set(tokens_limpios))
    diversidad = vocabulario / len(tokens_limpios) if tokens_limpios else 0.0

    partes = [
        documento.get("titulo") or "",
        documento.get("resumen") or "",
        documento.get("contenido") or "",
    ]
    texto_original = " ".join(str(p).strip() for p in partes if str(p or "").strip())

    return {
        "mongo_id": str(documento.get("_id", "")),
        "url": documento.get("url", "") or "",
        "url_final": documento.get("url_final", "") or "",
        "titulo": documento.get("titulo", "") or "",
        "autor": documento.get("autor", "") or "",
        "fecha_publicacion": fecha_iso(documento.get("fecha_publicacion")),
        "resumen": documento.get("resumen", "") or "",
        "contenido": documento.get("contenido", "") or "",
        "fuente_nombre": fuente.get("nombre", "") or "",
        "fuente_tipo_acopio": fuente.get("tipo_acopio", "") or "",
        "fuente_dominio": fuente.get("dominio", "") or "",
        "categorias": " | ".join(str(x) for x in (documento.get("categorias") or [])),
        "metodo_acopio": acopio.get("metodo", "") or "",
        "status_http": acopio.get("status_http") if acopio.get("status_http") is not None else "",
        "error_scraping": acopio.get("error_scraping", "") or "",
        "numero_palabras_acopio": analisis.get("numero_palabras", ""),
        "hash_contenido_original": analisis.get("hash_contenido", "") or "",
        "texto_original": texto_original,
        "texto_normalizado": procesado["texto_normalizado"],
        "tokens_alfabeticos": " ".join(tokens_alfabeticos),
        "tokens_limpios": " ".join(tokens_limpios),
        "texto_limpio": procesado["texto_limpio"],
        "tokens_stem": " ".join(procesado["tokens_stem"]),
        "texto_stem": procesado["texto_stem"],
        "numero_tokens_originales": len(tokens_originales),
        "numero_tokens_alfabeticos": len(tokens_alfabeticos),
        "numero_tokens_limpios": len(tokens_limpios),
        "vocabulario_documento": vocabulario,
        "diversidad_lexica": round(diversidad, 6),
        # Conserva campos de análisis original como referencia, si existen.
        "palabras_clave_originales": analisis.get("palabras_clave", []),
    }


def exportar_json(documentos, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8") as archivo:
        json.dump(json_seguro(documentos), archivo, ensure_ascii=False, indent=2)


def exportar_csv(registros, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=CSV_FIELDS, extrasaction="ignore")
        escritor.writeheader()
        for registro in registros:
            fila = dict(registro)
            for campo, valor in fila.items():
                if isinstance(valor, list):
                    fila[campo] = " | ".join(str(item) for item in valor)
            escritor.writerow(fila)


def exportar_frecuencias_csv(frecuencias, ruta, columnas):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(frecuencias)


def exportar_sqlite(registros, frecuencias_palabras, frecuencias_ngrama, ruta):
    """Crea una base relacional con noticias, frecuencias y n-gramas."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if ruta.exists():
        ruta.unlink()

    conexion = sqlite3.connect(ruta)
    try:
        conexion.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE noticias (
                mongo_id TEXT PRIMARY KEY,
                url TEXT NOT NULL UNIQUE,
                titulo TEXT NOT NULL,
                autor TEXT,
                fecha_publicacion TEXT,
                fuente TEXT,
                dominio TEXT,
                resumen TEXT,
                contenido TEXT,
                texto_limpio TEXT,
                texto_stem TEXT,
                numero_tokens_limpios INTEGER,
                vocabulario_documento INTEGER,
                diversidad_lexica REAL,
                error_scraping TEXT
            );
            CREATE INDEX idx_noticias_fuente ON noticias(fuente);
            CREATE INDEX idx_noticias_fecha ON noticias(fecha_publicacion);

            CREATE TABLE frecuencias_palabras (
                termino TEXT PRIMARY KEY,
                frecuencia INTEGER NOT NULL
            );

            CREATE TABLE ngramas (
                n INTEGER NOT NULL,
                ngrama TEXT NOT NULL,
                frecuencia INTEGER NOT NULL,
                PRIMARY KEY (n, ngrama)
            );
            """
        )

        filas_noticias = []
        for r in registros:
            filas_noticias.append((
                r.get("mongo_id", ""), r.get("url", ""), r.get("titulo", ""),
                r.get("autor", ""), r.get("fecha_publicacion", ""),
                r.get("fuente_nombre", ""), r.get("fuente_dominio", ""),
                r.get("resumen", ""), r.get("contenido", ""),
                r.get("texto_limpio", ""), r.get("texto_stem", ""),
                int(r.get("numero_tokens_limpios", 0) or 0),
                int(r.get("vocabulario_documento", 0) or 0),
                float(r.get("diversidad_lexica", 0) or 0),
                r.get("error_scraping", ""),
            ))

        conexion.executemany(
            """INSERT INTO noticias VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            filas_noticias,
        )
        conexion.executemany(
            "INSERT INTO frecuencias_palabras VALUES (?, ?)",
            [(x["termino"], int(x["frecuencia"])) for x in frecuencias_palabras],
        )
        conexion.executemany(
            "INSERT INTO ngramas VALUES (?, ?, ?)",
            [(int(x["n"]), x["ngrama"], int(x["frecuencia"])) for x in frecuencias_ngrama],
        )
        conexion.commit()
    finally:
        conexion.close()
