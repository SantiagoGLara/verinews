# VeriNews — Parte 4: agrupamiento temático e interfaces CLI/web

La Parte 4 amplía VeriNews sin reemplazar las funciones de recolección y PLN de las unidades anteriores.

## Alcance implementado

- Se conserva la recuperación TF-IDF + similitud coseno y la consulta por voz de `scripts/asistente_voz.py`.
- Se agrega agrupamiento no supervisado K-means sobre la matriz TF-IDF ya generada en Unidad 3. Cada noticia recibe un grupo temático (asignación/clasificación no supervisada). Para esta tarea se excluyen términos generales o de plantilla editorial que no ayudan a diferenciar temas; la matriz original y el buscador no se modifican.
- Cada grupo muestra términos representativos, cantidad de noticias, fuentes, fechas y publicaciones más cercanas al centroide.
- Se agrega una interfaz CLI unificada para buscar por texto o voz, explorar grupos y consultar estadísticas.
- Se agrega una interfaz web local y adaptable, servida con la biblioteca estándar de Python (sin Flask, Streamlit ni dependencias web adicionales). Permite buscar noticias, abrir sus URLs originales, explorar grupos K-means y consultar fuentes/estadísticas.
- La GUI reutiliza las funciones de búsqueda y agrupamiento existentes; no duplica los modelos ni altera los artefactos de la Unidad 3.
- Se agrega una evaluación experimental que compara distintos valores de `k` con Silhouette Score (distancia coseno).

No se modifica MongoDB ni se sobrescriben los archivos anteriores de Unidad 3. Los nuevos resultados se guardan en `data/unidad3/`.

## Requisitos

Instale las dependencias ya declaradas por el proyecto:

```bash
python -m pip install -r requirements.txt
```

La búsqueda por voz requiere además:

```bash
python -m pip install -r requirements-voz.txt
```

## Preparar datos

Si ya existen `noticias_procesadas.csv`, `matriz_tfidf.npz` y `vocabulario_tfidf.json`, no es necesario volver a procesar el corpus.

Si necesita reconstruirlos desde MongoDB:

```bash
python -m scripts.preparar_unidad3
```

También puede reproducir el procesamiento desde una exportación JSON:

```bash
python -m scripts.preparar_unidad3 --entrada-json data/unidad3/noticias_originales.json
```

## Ejecutar VeriNews

Desde la raíz del proyecto:

```bash
python -m scripts.verinews
```

Opciones del menú:

1. Buscar noticias por texto.
2. Buscar noticias por voz (requiere micrófono e Internet para el reconocimiento de Google).
3. Explorar grupos temáticos.
4. Consultar estadísticas y fuentes.
5. Recalcular los grupos temáticos.

El primer acceso a los grupos genera `data/unidad3/agrupamientos_kmeans.json`. La opción 5 vuelve a calcularlos.

## Interfaz gráfica web local

La interfaz web se ejecuta localmente y se abre en el navegador. No requiere instalar un framework web adicional:

```bash
python -m scripts.interfaz_web
```

Abre `http://127.0.0.1:8000`. Para evitar que se abra el navegador automáticamente:

```bash
python -m scripts.interfaz_web --no-browser
```

También se puede cambiar el puerto:

```bash
python -m scripts.interfaz_web --port 8080
```

La GUI incluye tres apartados:

1. **Buscar noticias:** consulta el buscador TF-IDF existente y muestra fuente, fecha, similitud y enlace a la publicación original.
2. **Grupos temáticos:** muestra los grupos K-means, términos representativos, distribución de fuentes y noticias cercanas al centroide. Permite recalcular los grupos.
3. **Fuentes y estadísticas:** presenta el tamaño del corpus, tokens, diversidad léxica, distribución por medio y términos frecuentes.

Por seguridad y privacidad, el servidor escucha en `127.0.0.1` de forma predeterminada. No se expone a la red local. La interfaz no emite dictámenes de veracidad: la similitud y los grupos son herramientas de exploración.

## Evaluación experimental

Ejecute:

```bash
python -m scripts.evaluar_unidad4
```

El script compara `k = 4, 6, 8, 10, 12, 14`, con `random_state=42`, `n_init=10` y Silhouette Score usando distancia coseno. Compara la matriz TF-IDF original (línea base) con la representación filtrada para el agrupamiento. Los resultados se guardan en `data/unidad3/evaluacion_kmeans.csv` y `data/unidad3/evaluacion_kmeans.md`.

Interpretación de Silhouette:

- Cerca de 1: grupos compactos y separados.
- Cerca de 0: grupos que se solapan.
- Menor que 0: varias noticias pueden estar más cerca de otro grupo que del asignado.

Un valor bajo no debe presentarse como un buen resultado. En ese caso, los grupos sirven para exploración inicial, pero requieren revisión y mejora del corpus/preprocesamiento.

## Consideraciones metodológicas

- K-means es no supervisado: no necesita etiquetas previas y asigna cada noticia a un grupo.
- Los términos representativos se obtienen de los centroides TF-IDF.
- Se filtran únicamente para el agrupamiento los términos generales que sí aparecen en el vocabulario: `no`, `mexic`, `ayer`, `hoy`, `octubr`, `minut`, `primer`, `digital`, `notici`, `public`, `aparec`, `primero`, `suscrib` y `canal`.
- La similitud con el centroide ordena las noticias dentro de cada grupo; no expresa veracidad.
- La matriz TF-IDF de búsqueda se reutiliza para no alterar el buscador previo.
- La clasificación supervisada no se incorpora todavía porque las categorías disponibles son incompletas y heterogéneas. No se deben reportar como etiquetas confiables sin depurarlas y validarlas.
- Agrupar noticias no demuestra que describan exactamente el mismo acontecimiento ni que sean fuentes independientes. La revisión de títulos, fechas, medios y URLs sigue siendo necesaria.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

Las pruebas incluyen las funciones de agrupamiento, la carga de estadísticas y las rutas HTTP principales de la GUI.
