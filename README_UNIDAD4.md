# VeriNews — Unidad 4 / Parte 4

La Parte 4 convierte el prototipo de búsqueda en un flujo de investigación de afirmaciones y acontecimientos. La aplicación reúne publicaciones del corpus, organiza su procedencia y fechas, detecta candidatos a duplicación y ofrece clasificación temática opcional. No emite dictámenes automáticos de verdad o falsedad.

## Objetivo funcional

El flujo principal de VeriNews es:

1. **Entrada:** el usuario escribe una afirmación, titular o acontecimiento.
2. **Recuperación:** se localizan publicaciones relacionadas mediante TF-IDF y similitud coseno. LSA está disponible como alternativa experimental.
3. **Análisis:** se comparan publicaciones, se identifican hashes idénticos y pares con similitud textual alta; se resume la cobertura por medio.
4. **Cronología:** se ordenan por fecha las publicaciones recuperadas.
5. **Fuentes:** se muestran medios, dominios y metadatos disponibles. El tipo de fuente (primaria/secundaria) se conserva como «Sin determinar» si el corpus no permite demostrarlo.
6. **Salida:** se presenta un expediente con documentos, coincidencias, cronología, procedencia y avisos de incertidumbre/cobertura.

El número de medios distintos no equivale al número de fuentes independientes. Una similitud alta no demuestra por sí sola copia: puede indicar republicación, actualización o cobertura del mismo hecho. El usuario debe revisar las publicaciones originales.

## Alcance implementado

- Se conserva el buscador TF-IDF de Unidad 3 y la consulta por voz original.
- La GUI principal ahora construye un **expediente de investigación**: publicaciones, puntuaciones, medios, dominios, cronología, cobertura textual y pares similares.
- Se identifican duplicados exactos mediante el hash de contenido registrado en el corpus.
- Se proponen pares de similitud alta con TF-IDF, umbral inicial de 0.78 y mínimo de 100 palabras registradas. Son candidatos de revisión, no duplicados confirmados.
- Se conserva K-means para explorar temas generales del corpus. Además, cada expediente propone subgrupos locales de cobertura mediante componentes conectados de similitud TF-IDF (umbral 0.25), aplicados solo a resultados con puntuación de consulta suficiente. No se presentan como detector definitivo de acontecimientos.
- Se incorpora recuperación LSA (TruncatedSVD sobre TF-IDF) como alternativa experimental, no como sustituto automático de TF-IDF.
- Se incorpora clasificación temática zero-shot opcional con `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`.
- Se conservan la CLI y la vista general de estadísticas.

## Corpus y limitaciones

El corpus incluido contiene 909 publicaciones de siete medios. En la exportación procesada, 466 registros tienen cuerpo de artículo y 443 dependen de titular/resumen porque no se extrajo el cuerpo. La GUI muestra esta diferencia para no presentar un resumen RSS como si fuera el texto completo.

La clasificación primaria/secundaria no se infiere a partir del nombre del medio ni del método de acopio. Actualmente se muestra «Sin determinar» cuando no hay metadatos que permitan sostenerla. Tampoco se asigna un grado global automático de evidencia/veracidad: faltan metadatos validados de fuentes primarias/secundarias e independencia editorial. Los indicadores visibles describen cobertura documental e incertidumbre del corpus y dejan la valoración final al usuario.

## Instalación base

Desde la raíz del proyecto:

```bash
python -m pip install -r requirements.txt
```

Si el entorno no tiene las stopwords de NLTK:

```bash
python -m nltk.downloader stopwords
```

La búsqueda, GUI, CLI, K-means y LSA no requieren dependencias adicionales a las del proyecto.

## Ejecutar VeriNews

### GUI web local

```bash
python -m scripts.interfaz_web
```

Abre `http://127.0.0.1:8000`. También puede iniciarse sin abrir el navegador:

```bash
python -m scripts.interfaz_web --no-browser
```

### CLI

```bash
python -m scripts.verinews
```

La consulta por voz se mantiene disponible desde la CLI, pero su prueba en el equipo del usuario queda pendiente.

## Clasificación temática zero-shot (opcional)

La GUI ofrece un botón para clasificar las primeras ocho publicaciones del expediente. Utiliza el modelo NLI indicado en la práctica de Transformers de la Unidad 4 y las categorías candidatas definidas en `processing/topic_classifier.py`.

No forma parte de los requisitos de instalación base. Para habilitarla:

```bash
python -m pip install -r requirements-clasificacion.txt
```

La primera inferencia descarga los pesos del modelo y puede tardar, especialmente en CPU. La compatibilidad de PyTorch/Transformers depende de la versión de Python y del sistema; la combinación opcional no se validó en el Python 3.14.4 del equipo del usuario. El proyecto base no requiere esta instalación y continúa funcionando si no se habilita el clasificador. En las pruebas de esta entrega no se descargaron ni ejecutaron los pesos reales; se probó la integración con un clasificador simulado y la respuesta de dependencia opcional ausente.

Categorías candidatas predeterminadas: Política y gobierno, Economía, Seguridad y justicia, Sociedad, Salud, Tecnología y ciencia, Cultura y entretenimiento, Deportes, Medio ambiente y Otra temática. Las puntuaciones de mDeBERTa son afinidades relativas a estas categorías, no probabilidades de veracidad ni etiquetas verificadas.

## Recuperación LSA

La opción «LSA · experimental» de la GUI utiliza TruncatedSVD con 100 componentes sobre la matriz TF-IDF y normaliza los vectores latentes. La primera ejecución construye y guarda el índice en `data/unidad4/`.

El buscador predeterminado continúa siendo TF-IDF porque, en el conjunto piloto de evaluación disponible, obtuvo mejores promedios que LSA. LSA se conserva para reproducir y ampliar la comparación.

## Evaluación experimental

### Comparación principal

Ejecute:

```bash
python -m scripts.evaluar_unidad4_completa
```

El comando realiza:

1. Evaluación K-means para varios valores de `k`, comparando TF-IDF original con la representación filtrada. Métrica: Silhouette con distancia coseno.
2. Comparación de recuperación TF-IDF frente a LSA con ocho consultas y 48 publicaciones relevantes revisadas manualmente. Métricas: Precision@5, Recall@5, MRR@10, Precision@10 y Recall@10.

Para comparar también con la búsqueda de la versión anterior (MongoDB `$text` con pesos título=5, resumen=3 y contenido=1), inicie MongoDB con la misma colección e índice y ejecute:

```bash
python -m scripts.evaluar_unidad4_completa --mongodb
```

Este paso es opcional porque requiere la base MongoDB local con el corpus de la fase anterior. Si la colección no está disponible, la comparación MongoDB no se ejecuta y no deben inventarse sus métricas.

Archivos:

- `data/unidad3/evaluacion_kmeans.csv`
- `data/unidad3/evaluacion_kmeans.md`
- `data/unidad4/consultas_relevancia.json`
- `data/unidad4/evaluacion_recuperacion.csv`
- `data/unidad4/evaluacion_recuperacion.md`
- `data/unidad4/evaluacion_busqueda_legacy.csv` y `.md` (solo cuando se ejecute la comparación con MongoDB).

**Resultado del conjunto piloto:** TF-IDF: Precision@5 = 0.8500, Recall@5 = 0.7927, MRR@10 = 1.0000. LSA: Precision@5 = 0.8250, Recall@5 = 0.7614, MRR@10 = 0.9167. Se mantiene TF-IDF como método predeterminado. El conjunto es pequeño y sus etiquetas se revisaron a partir de títulos/resúmenes; no permite generalizar a todos los temas ni a otros corpus. La evaluación ejecutada en el entorno de preparación utilizó Python 3.13.5 y scikit-learn 1.8.0, mientras que `requirements.txt` fija scikit-learn 1.9.1; por ello, estos números son preliminares y se deben reproducir en el entorno final después de instalar los requisitos fijados. El índice LSA guarda la versión de scikit-learn y se reconstruye automáticamente si no coincide.

K-means obtuvo Silhouette bajo (aprox. 0.0197 con k=14). Los grupos son exploratorios y no deben interpretarse como separación fuerte de acontecimientos.

### Evaluar duplicados/casi duplicados

Generar una muestra de pares:

```bash
python -m scripts.preparar_pares_duplicados
```

Abra `data/unidad4/pares_duplicados_para_etiquetar.csv` y complete `duplicado_real` con:

- `1`: duplicado/republicación del mismo contenido.
- `0`: cobertura relacionada, pero contenido periodístico independiente.

Después ejecute:

```bash
python -m scripts.evaluar_duplicados
```

El script calcula precisión, recall, F1 y matriz de confusión. No se reportan métricas hasta contar con revisión humana.

### Evaluar clasificación temática

Generar una muestra reproducible de 100 noticias:

```bash
python -m scripts.preparar_muestra_clasificacion
```

Complete manualmente la columna `categoria_real` de `data/unidad4/noticias_para_etiquetar.csv` con una de las categorías definidas en `processing/topic_classifier.py`. Para evaluar:

```bash
python -m pip install -r requirements-clasificacion.txt
python -m scripts.evaluar_clasificacion
```

Se generan predicciones, accuracy, F1 macro y matriz de confusión. No se presentan métricas mientras la muestra no esté etiquetada por personas.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

Las pruebas no requieren MongoDB ni micrófono. La integración de mDeBERTa se prueba mediante un pipeline simulado para no descargar el modelo en cada ejecución.

## Archivos principales nuevos/modificados

- `processing/investigation.py`: expediente, fuentes, cronología y candidatos similares.
- `processing/lsa_retrieval.py`: recuperación experimental LSA.
- `processing/topic_classifier.py`: clasificación zero-shot opcional.
- `scripts/interfaz_web.py`: API local de investigación y clasificación.
- `web/index.html`: GUI centrada en expedientes de investigación.
- `scripts/evaluar_recuperacion.py`: TF-IDF frente a LSA.
- `scripts/preparar_pares_duplicados.py` / `scripts/evaluar_duplicados.py`: evaluación humana de pares similares.
- `scripts/preparar_muestra_clasificacion.py` / `scripts/evaluar_clasificacion.py`: evaluación de mDeBERTa contra etiquetas humanas.
