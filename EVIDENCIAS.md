# Evidencias para la revisión presencial

Toma capturas de estas partes:

1. `python run_acopio.py`
   mostrando feeds consultados y documentos insertados.

2. Segunda ejecución de `python run_acopio.py`
   mostrando que las URLs existentes no se duplican.

3. MongoDB:
   `use verinews`
   `db.noticias.countDocuments()`

4. Un documento:
   `db.noticias.findOne()`

5. Índices:
   `db.noticias.getIndexes()`

6. Búsqueda:
   `python -m scripts.probar_busqueda`

7. Dentro de un documento muestra los bloques:
   - `acopio`
   - `analisis`


## Evidencias de Unidad 3 — Procesamiento de Lenguaje Natural

Ejecuta `python -m scripts.preparar_unidad3`

8. `data/unidad3/noticias_procesadas.csv`, mostrando tokens y texto limpio.
9. `data/unidad3/frecuencias_palabras.csv` y `frecuencias_ngrama.csv`.
10. `data/unidad3/grafica_frecuencias.png`.
11. `data/unidad3/noticias.sqlite`, mostrando las tablas `noticias`, `frecuencias_palabras` y `ngramas`.
12. `data/unidad3/vectorizacion_info.json`, `matriz_bow.npz` y `matriz_tfidf.npz`, junto con `vocabulario_tfidf.json`.
13. `python -m scripts.asistente_voz` con una consulta hablada y respuesta oral. Si no hay micrófono disponible, prueba la búsqueda con `python -m scripts.asistente_voz --texto "noticias de seguridad en Michoacán" --solo-texto`.
14. `data/unidad3/reporte_resultados.md`, que contiene las métricas reales de esa ejecución.
