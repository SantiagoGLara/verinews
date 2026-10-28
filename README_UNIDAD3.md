# VeriNews — Entregable Unidad 3: Procesamiento de Lenguaje Natural

Este módulo amplía el proyecto multifuente VeriNews para trabajar con las noticias ya recuperadas en `verinews.noticias` de MongoDB. Genera exportaciones interoperables, preprocesamiento, estadísticas, n-gramas, vectorización BoW/TF-IDF y una interfaz de consulta por voz.

## 1. Requisitos

- Python 3.10 o posterior.
- MongoDB en ejecución en `mongodb://localhost:27017/`.
- Micrófono para reconocimiento de voz y una voz instalada en el sistema para síntesis.
- Internet para el reconocimiento STT con `recognize_google`; la síntesis `pyttsx3` funciona localmente, aunque depende de las voces instaladas.

Desde la carpeta raíz `verinews_fase2_multifuente`:

```bash
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

Instale las dependencias:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m nltk.downloader stopwords
```

Para activar la entrada por micrófono, instale además el extra de audio:

```bash
python -m pip install -r requirements-voz.txt
```

Si la instalación de PyAudio falla en Windows, instálelo de acuerdo con la versión de Python y los requisitos del sistema. La parte de procesamiento y vectorización puede ejecutarse sin micrófono; el asistente también admite consultas escritas con `--texto`.

## 2. Ejecutar el pipeline de Unidad 3

Asegúrese de que MongoDB esté iniciado y de que ya existan noticias recolectadas. Después ejecute:

```bash
python -m scripts.preparar_unidad3
```

Los archivos se guardan en `data/unidad3/`. El programa no modifica ni reemplaza los documentos originales de MongoDB.

### Usar un JSON exportado en lugar de MongoDB

Si desea reproducir el procesamiento desde una copia JSON:

```bash
python -m scripts.preparar_unidad3 --entrada-json data/unidad3/noticias_originales.json
```

Puede limitar el tamaño del vocabulario:

```bash
python -m scripts.preparar_unidad3 --max-features 5000
```

## 3. Archivos que genera

| Archivo | Contenido |
|---|---|
| `noticias_originales.json` | Documentos anidados originales exportados de MongoDB. |
| `noticias_procesadas.json` | Noticias con metadatos y campos de preprocesamiento. |
| `noticias_procesadas.csv` | Versión tabular compatible con hojas de cálculo y análisis. |
| `noticias.sqlite` | Base relacional SQLite con noticias, frecuencias y n-gramas. |
| `frecuencias_palabras.csv` | Hasta 30 términos más frecuentes. |
| `frecuencias_ngrama.csv` | Bigramas y trigramas frecuentes. |
| `estadisticas_fuentes.csv` | Noticias y tokens limpios por medio. |
| `estadisticas.json` | Métricas generales y estadísticas del corpus. |
| `grafica_frecuencias.png` | Gráfica de las 20 palabras más frecuentes. |
| `matriz_bow.npz` | Matriz dispersa de conteos de palabras. |
| `matriz_tfidf.npz` | Matriz dispersa TF-IDF con unigramas y bigramas. |
| `vectorizador_bow.joblib`, `vectorizador_tfidf.joblib` | Vectorizadores entrenados para transformar nuevos textos. |
| `vocabulario_bow.json`, `vocabulario_tfidf.json` | Término y posición de cada característica. |
| `vectorizacion_info.json` | Dimensiones, densidad y número de elementos no nulos. |
| `reporte_resultados.md` | Informe generado con los resultados reales de la ejecución. |

## 4. Preprocesamiento aplicado

1. Se concatenan título, resumen y contenido.
2. Se normalizan HTML, URLs, espacios y mayúsculas; se conservan los acentos españoles.
3. NLTK tokeniza el texto.
4. Se eliminan puntuación, números y tokens no alfabéticos.
5. Se eliminan stopwords en español; se conservan negaciones como «no», «nunca» y «sin».
6. SnowballStemmer reduce variantes morfológicas a una raíz aproximada.

El programa conserva por separado el texto original, los tokens alfabéticos, los tokens limpios y las raíces derivadas. Esto permite comparar el antes y el después sin perder la fuente original.

## 5. Estadísticas

Se calculan total de tokens limpios, vocabulario distinto, diversidad léxica, frecuencias de palabras, bigramas, trigramas y estadísticas por fuente. Las frecuencias se obtienen con `nltk.FreqDist` y los n-gramas con `nltk.util.ngrams`.

## 6. Vectorización y estructura de datos

- **BoW:** `CountVectorizer` representa cada noticia mediante conteos de términos.
- **TF-IDF:** `TfidfVectorizer` asigna pesos a unigramas y bigramas según su frecuencia en la noticia y su distribución en el corpus.
- Las matrices son `scipy.sparse` y se guardan en formato `.npz` para evitar almacenar ceros innecesarios.
- Las filas respetan el mismo orden de `noticias_procesadas.csv`; cada columna representa una característica del vocabulario.
- El asistente convierte una consulta a un vector TF-IDF y calcula similitud coseno para ordenar noticias candidatas.

## 7. Reconocimiento y síntesis de voz

Inicie el asistente interactivo:

```bash
python -m scripts.asistente_voz
```

El sistema escucha una consulta en español, la transcribe con SpeechRecognition/Google (`es-MX`), busca noticias similares y lee el primer resultado con `pyttsx3`.

Prueba sin micrófono ni reproducción de audio:

```bash
python -m scripts.asistente_voz --texto "noticias de seguridad en Michoacán" --solo-texto
```

El reconocimiento de Google necesita Internet. `pyttsx3` sintetiza usando voces instaladas localmente; el idioma y la calidad de la voz dependen del equipo.

## 8. Comprobar la base SQLite

Puede abrir `data/unidad3/noticias.sqlite` con DB Browser for SQLite o ejecutar:

```python
import sqlite3
conexion = sqlite3.connect("data/unidad3/noticias.sqlite")
print(conexion.execute("SELECT fuente, COUNT(*) FROM noticias GROUP BY fuente").fetchall())
print(conexion.execute("SELECT termino, frecuencia FROM frecuencias_palabras ORDER BY frecuencia DESC LIMIT 10").fetchall())
conexion.close()
```

## 9. Alcances y limitaciones

- La calidad de los resultados depende del texto realmente recuperado; noticias con scraping fallido pueden tener solamente título y resumen.
- El stemming produce raíces útiles para agrupar variantes, pero no garantiza palabras válidas en español.
- La similitud coseno expresa cercanía entre vectores léxicos, no veracidad ni probabilidad de que una noticia responda correctamente.
- Las estadísticas finales se generan en el equipo donde está la base MongoDB; no se incluyen conteos inventados en este paquete.
