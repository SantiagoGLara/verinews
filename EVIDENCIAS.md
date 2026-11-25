# Evidencias para la revisión del proyecto VeriNews

## Recolección y Unidad 2

1. Ejecutar `python run_acopio.py` y mostrar fuentes consultadas y documentos insertados.
2. Repetir la ejecución y mostrar que no se duplican URLs existentes.
3. En MongoDB: `db.noticias.countDocuments()`, `db.noticias.findOne()` y `db.noticias.getIndexes()`.
4. Mostrar en un documento los bloques `acopio` y `analisis`.
5. Ejecutar `python -m scripts.detectar_duplicados` y explicar el hash exacto.

## Unidad 3 — PLN

1. Ejecutar `python -m scripts.preparar_unidad3`.
2. Mostrar `noticias_procesadas.csv`, tokens, texto limpio y stemming.
3. Mostrar frecuencias, n-gramas, gráfica, SQLite, matrices BoW/TF-IDF y vocabulario.
4. Probar `python -m scripts.asistente_voz --texto "noticias de seguridad en Michoacán" --solo-texto`.
5. Probar el micrófono de forma independiente cuando el equipo esté disponible.

## Unidad 4 — Expediente de investigación

1. Ejecutar `python -m scripts.interfaz_web` y abrir `http://127.0.0.1:8000`.
2. Introducir una consulta real del corpus, por ejemplo `huracán Simon Michoacán`.
3. Mostrar el resumen: publicaciones recuperadas, medios distintos, cuerpo extraído, publicaciones con solo resumen y pares similares.
4. Mostrar la cronología y abrir los enlaces originales.
5. Mostrar el análisis de procedencia y explicar por qué el tipo de fuente aparece como «Sin determinar» cuando no hay evidencia documental.
6. Mostrar subgrupos de cobertura sugeridos y explicar que son agrupamientos por similitud, no confirmación de un mismo evento.
7. Mostrar pares con hash idéntico y similitud alta, distinguiendo duplicado confirmado por hash de candidato por similitud.
8. Usar «LSA · experimental» y explicar que TF-IDF sigue siendo el método predeterminado por los resultados piloto.
9. Explorar grupos K-means y explicar que Silhouette bajo implica grupos exploratorios.
10. Consultar estadísticas generales, destacando la diferencia entre cuerpo extraído y resumen/titular.
11. Si se habilita el modelo opcional, clasificar noticias con mDeBERTa y revisar las categorías sugeridas.

## Evaluación experimental

1. Ejecutar `python -m scripts.evaluar_unidad4_completa`.
2. Mostrar `data/unidad3/evaluacion_kmeans.md` y `data/unidad4/evaluacion_recuperacion.md`.
3. Si MongoDB de la versión anterior está disponible, ejecutar `python -m scripts.evaluar_unidad4_completa --mongodb` y mostrar la comparación MongoDB `$text` vs TF-IDF vs LSA.
4. Completar `duplicado_real` en `pares_duplicados_para_etiquetar.csv` y ejecutar `python -m scripts.evaluar_duplicados`.
5. Completar `categoria_real` en `noticias_para_etiquetar.csv`, habilitar mDeBERTa y ejecutar `python -m scripts.evaluar_clasificacion`.
6. Ejecutar `python -m unittest discover -s tests -v` y mostrar el total de pruebas aprobadas.

No presentar como resultados medidos las evaluaciones que todavía dependen de etiquetado humano. No interpretar número de medios, similitud o clasificación temática como veracidad.
