# Estructura de VeriNews

- `collectors/`: descubrimiento RSS/listados, robots.txt y extracción de artículos.
- `database/`: conexión MongoDB, índices y exportaciones.
- `processing/`: preprocesamiento, estadísticas, vectorización y análisis.
  - `clustering.py`: K-means temático del corpus.
  - `investigation.py`: expediente de investigación, fuentes, cronología, subgrupos de cobertura y pares similares.
  - `lsa_retrieval.py`: recuperación latente experimental (TF-IDF + TruncatedSVD).
  - `topic_classifier.py`: clasificación zero-shot opcional con mDeBERTa.
- `scripts/`: puntos de entrada CLI, GUI, recolección y evaluación.
  - `asistente_voz.py`: buscador TF-IDF y consulta de voz/texto.
  - `verinews.py`: CLI unificada.
  - `interfaz_web.py`: servidor HTTP local y API JSON.
  - `evaluar_unidad4.py`: evaluación de K-means.
  - `evaluar_recuperacion.py`: comparación TF-IDF/LSA.
  - `evaluar_busqueda_legacy.py`: compara MongoDB `$text` de la versión anterior con TF-IDF y LSA (requiere MongoDB).
  - `evaluar_unidad4_completa.py`: ejecuta las comparaciones principales.
  - `preparar_pares_duplicados.py` / `evaluar_duplicados.py`: muestreo y métricas tras etiquetado humano.
  - `preparar_muestra_clasificacion.py` / `evaluar_clasificacion.py`: muestra y evaluación del clasificador.
- `web/index.html`: GUI de investigación, grupos y estadísticas.
- `tests/`: pruebas de Unidad 3, K-means, expediente, clasificador simulado y API web.
- `data/unidad3/`: corpus procesado, estadísticas y matrices TF-IDF/BoW originales.
- `data/unidad4/`: índice LSA (se regenera por versión de scikit-learn), consultas de relevancia, resultados experimentales y plantillas de etiquetado.
- `requirements-clasificacion.txt`: dependencias opcionales para mDeBERTa; no son necesarias para la GUI base.

Los artefactos de Unidad 3 se conservan. La búsqueda predeterminada sigue siendo TF-IDF; LSA y mDeBERTa son opciones experimentales/opcionales.
