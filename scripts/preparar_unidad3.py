"""Ejecuta el pipeline de Unidad 3 sobre las noticias almacenadas en MongoDB.

Uso desde la raíz del proyecto:
    python -m scripts.preparar_unidad3
    python -m scripts.preparar_unidad3 --entrada-json data/unidad3/noticias_originales.json
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from database.exporters import (
    construir_registro,
    exportar_csv,
    exportar_frecuencias_csv,
    exportar_json,
    exportar_sqlite,
)
from processing.preprocessor import obtener_stopwords, preprocesar_texto
from processing.unit3_statistics import calcular_estadisticas
from processing.vectorization import vectorizar

ROOT = Path(__file__).resolve().parents[1]
SALIDA = ROOT / "data" / "unidad3"


def cargar_documentos(entrada_json=None):
    if entrada_json:
        ruta = Path(entrada_json)
        if not ruta.is_absolute():
            ruta = (Path.cwd() / ruta).resolve()
        with ruta.open("r", encoding="utf-8") as archivo:
            documentos = json.load(archivo)
        if not isinstance(documentos, list):
            raise ValueError("El JSON de entrada debe contener una lista de noticias.")
        return documentos

    from database.mongo import obtener_coleccion

    cliente, noticias = obtener_coleccion()
    try:
        return list(noticias.find({}).sort("fecha_publicacion", -1))
    finally:
        cliente.close()


def construir_texto_original(documento):
    partes = [documento.get("titulo"), documento.get("resumen"), documento.get("contenido")]
    return " ".join(str(p).strip() for p in partes if p and str(p).strip())


def guardar_grafica(estadisticas, ruta):
    datos = estadisticas["frecuencias_palabras"][:20]
    fig, ax = plt.subplots(figsize=(12, 6))
    if datos:
        etiquetas = [x["termino"] for x in reversed(datos)]
        valores = [x["frecuencia"] for x in reversed(datos)]
        ax.barh(etiquetas, valores)
        ax.set_xlabel("Frecuencia")
        ax.set_ylabel("Término")
        ax.set_title("VeriNews: 20 términos más frecuentes después del preprocesamiento")
    else:
        ax.text(0.5, 0.5, "No hay términos para graficar", ha="center", va="center")
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(ruta, dpi=160, bbox_inches="tight")
    plt.close(fig)


def escribir_reporte(estadisticas, vector_info, ruta):
    top_palabras = estadisticas["frecuencias_palabras"][:10]
    top_bi = estadisticas["frecuencias_bigramas"][:10]
    top_tri = estadisticas["frecuencias_trigramas"][:10]
    fuentes = estadisticas["por_fuente"]

    def tabla(items, campos):
        lineas = ["| " + " | ".join(campos) + " |", "|" + "|".join(["---"] * len(campos)) + "|"]
        for item in items:
            lineas.append("| " + " | ".join(str(item.get(c, "")) for c in campos) + " |")
        return "\n".join(lineas)

    texto = f"""# Informe de resultados — Unidad 3: PLN aplicado a VeriNews

**Fecha de ejecución:** {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}  
**Colección de origen:** `verinews.noticias`  
**Total de noticias procesadas:** {estadisticas['total_noticias']}  
**Noticias con texto:** {estadisticas['noticias_con_texto']}

## 1. Preparación e intercambio de datos

Se conservaron los documentos originales en JSON, se generó un CSV tabular para análisis y una base relacional SQLite con las tablas `noticias`, `frecuencias_palabras` y `ngramas`. MongoDB continúa siendo la fuente NoSQL original.

## 2. Preprocesamiento de texto

Pipeline aplicado: normalización Unicode y minúsculas → eliminación de URLs/HTML y espacios redundantes → tokenización con NLTK → filtrado de tokens no alfabéticos y números → eliminación de stopwords en español → stemming con Snowball para español. Se conservan negaciones relevantes como «no», «nunca» y «sin». El texto original no se sobrescribe.

- Tokens limpios totales: **{estadisticas['tokens_limpios_total']}**
- Vocabulario (términos distintos): **{estadisticas['vocabulario_total']}**
- Diversidad léxica del corpus (vocabulario/tokens): **{estadisticas['diversidad_lexica_corpus']}**

## 3. Estadísticas del corpus

### 10 palabras más frecuentes

{tabla(top_palabras, ['termino', 'frecuencia'])}

### 10 bigramas más frecuentes

{tabla(top_bi, ['ngrama', 'frecuencia'])}

### 10 trigramas más frecuentes

{tabla(top_tri, ['ngrama', 'frecuencia'])}

### Noticias por fuente

{tabla(fuentes, ['fuente', 'noticias', 'tokens_limpios'])}

La gráfica `grafica_frecuencias.png` representa los 20 términos más frecuentes. Las frecuencias se calculan sobre los tokens limpios, después de retirar stopwords.

## 4. Vectorización

Se construyeron dos representaciones:

- **BoW / CountVectorizer:** conteo de términos por noticia.
- **TF-IDF / TfidfVectorizer:** ponderación de términos según su frecuencia local y su capacidad discriminante en el corpus; incluye unigramas y bigramas.

Las matrices se guardan como archivos `.npz` dispersos (CSR), porque la mayoría de las celdas documento-término son cero. Las columnas corresponden a términos del vocabulario y las filas a noticias, en el mismo orden que `noticias_procesadas.csv`.

- Forma BoW (documentos × términos): **{vector_info['forma_matriz_bow']}**
- Forma TF-IDF (documentos × características): **{vector_info['forma_matriz_tfidf']}**
- Elementos no cero TF-IDF: **{vector_info['elementos_no_cero_tfidf']}**
- Densidad TF-IDF: **{vector_info['densidad_tfidf']:.6f}**

## 5. Reconocimiento y síntesis de voz

El módulo `scripts/asistente_voz.py` permite formular una consulta con el micrófono usando SpeechRecognition con el servicio de reconocimiento de Google en español (`es-MX`) y buscar noticias similares con TF-IDF y similitud coseno. La respuesta se puede leer en voz alta con `pyttsx3`. El reconocimiento necesita Internet; la síntesis utiliza una voz instalada localmente y su disponibilidad depende del sistema operativo.

## 6. Archivos generados

- `noticias_originales.json`
- `noticias_procesadas.json` y `noticias_procesadas.csv`
- `noticias.sqlite`
- `frecuencias_palabras.csv`, `frecuencias_ngrama.csv`, `estadisticas_fuentes.csv`
- `estadisticas.json`, `grafica_frecuencias.png`
- `matriz_bow.npz`, `matriz_tfidf.npz`
- `vectorizador_bow.joblib`, `vectorizador_tfidf.joblib`
- `vocabulario_bow.json`, `vocabulario_tfidf.json`, `vectorizacion_info.json`

## 7. Interpretación y limitaciones

Las palabras y n-gramas más frecuentes muestran temas recurrentes en el conjunto recolectado, pero su frecuencia no demuestra por sí sola relevancia, veracidad ni causalidad. El stemming reduce variantes morfológicas, aunque puede producir raíces que no son palabras completas. TF-IDF permite comparar noticias y consultas por similitud léxica, pero la similitud coseno no es una probabilidad de que el contenido sea verdadero. Los resultados dependen de la cantidad y calidad del texto recuperado por cada fuente.
"""
    ruta.write_text(texto, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Procesa los datos de VeriNews para la Unidad 3.")
    parser.add_argument("--entrada-json", help="Usar una lista JSON en lugar de conectarse a MongoDB.")
    parser.add_argument("--max-features", type=int, default=10000, help="Máximo de características por matriz.")
    args = parser.parse_args()

    SALIDA.mkdir(parents=True, exist_ok=True)
    documentos = cargar_documentos(args.entrada_json)
    if not documentos:
        raise SystemExit("No hay noticias en la fuente seleccionada. Ejecute el acopio o revise el JSON.")

    print(f"Noticias recuperadas: {len(documentos)}")
    exportar_json(documentos, SALIDA / "noticias_originales.json")

    stopwords_es = obtener_stopwords()
    registros = []
    for documento in documentos:
        texto_original = construir_texto_original(documento)
        procesado = preprocesar_texto(texto_original, stopwords_es)
        registros.append(construir_registro(documento, procesado))

    exportar_json(registros, SALIDA / "noticias_procesadas.json")
    exportar_csv(registros, SALIDA / "noticias_procesadas.csv")

    estadisticas = calcular_estadisticas(registros, limite=30)
    exportar_json(estadisticas, SALIDA / "estadisticas.json")
    exportar_frecuencias_csv(
        estadisticas["frecuencias_palabras"],
        SALIDA / "frecuencias_palabras.csv",
        ["termino", "frecuencia"],
    )
    exportar_frecuencias_csv(
        estadisticas["frecuencias_bigramas"] + estadisticas["frecuencias_trigramas"],
        SALIDA / "frecuencias_ngrama.csv",
        ["n", "ngrama", "frecuencia"],
    )
    exportar_frecuencias_csv(
        estadisticas["por_fuente"],
        SALIDA / "estadisticas_fuentes.csv",
        ["fuente", "noticias", "tokens_limpios"],
    )
    guardar_grafica(estadisticas, SALIDA / "grafica_frecuencias.png")

    exportar_sqlite(
        registros,
        estadisticas["frecuencias_palabras"],
        estadisticas["frecuencias_bigramas"] + estadisticas["frecuencias_trigramas"],
        SALIDA / "noticias.sqlite",
    )

    vector_info = vectorizar(registros, SALIDA, max_features=args.max_features)
    with (SALIDA / "vectorizacion_info.json").open("w", encoding="utf-8") as archivo:
        json.dump(vector_info, archivo, ensure_ascii=False, indent=2)
    escribir_reporte(estadisticas, vector_info, SALIDA / "reporte_resultados.md")

    print("\nUnidad 3 completada. Archivos generados en:", SALIDA)
    print("Noticias:", estadisticas["total_noticias"])
    print("Tokens limpios:", estadisticas["tokens_limpios_total"])
    print("Vocabulario:", estadisticas["vocabulario_total"])
    print("Matriz TF-IDF:", vector_info["forma_matriz_tfidf"])
    print("Reporte:", SALIDA / "reporte_resultados.md")


if __name__ == "__main__":
    main()
