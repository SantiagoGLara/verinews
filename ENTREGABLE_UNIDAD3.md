# Entregable de Unidad 3 — VeriNews

## Objetivo
Aplicar técnicas clásicas de procesamiento de lenguaje natural a las noticias recolectadas por VeriNews para convertirlas en datos interoperables, analizables y vectorizados, incorporando una prueba de reconocimiento y síntesis de voz.

## Arquitectura

`MongoDB (noticias) → exportación JSON/CSV/SQLite → normalización → tokenización → limpieza/stopwords → stemming → estadísticas y n-gramas → BoW/TF-IDF → similitud coseno → consulta por voz y respuesta hablada`

## Relación de requisitos con archivos

1. **Datos y formatos:** `database/exporters.py` y `scripts/preparar_unidad3.py`. Exporta la colección NoSQL original a JSON, una vista tabular a CSV y una base relacional SQLite.
2. **Preprocesamiento:** `processing/preprocessor.py`. Normaliza el texto, tokeniza con NLTK, elimina números/puntuación y stopwords, y aplica stemming Snowball en español.
3. **Estadísticas:** `processing/unit3_statistics.py`. Calcula `FreqDist`, vocabulario, diversidad léxica, palabras frecuentes, bigramas, trigramas y estadísticas por fuente. Genera CSV y una gráfica.
4. **Reconocimiento y síntesis de voz:** `scripts/asistente_voz.py`. SpeechRecognition transcribe consultas habladas; `pyttsx3` lee los resultados. La búsqueda de noticias utiliza la matriz TF-IDF.
5. **Vectorización:** `processing/vectorization.py`. Genera BoW y TF-IDF como matrices dispersas CSR, guarda los vocabularios y registra las dimensiones de las matrices.


