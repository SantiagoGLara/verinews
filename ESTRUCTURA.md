proyecto -> VeriNews: recolector de noticias y pipeline PLN; Python, MongoDB, NLTK y scikit-learn.
./ -> Código y documentación del proyecto; datos generados en data/unidad3/.
collectors/ -> Descubrimiento RSS/listados, control robots.txt y scraping.
  collectors/__init__.py -> Paquete de recolectores.
  collectors/source_collector.py -> Coordina la recolección por fuente.
  collectors/rss_collector.py -> Lee y normaliza entradas RSS.
  collectors/article_scraper.py -> Descarga y extrae metadatos y texto.
  collectors/robots.py -> Comprueba permisos según robots.txt.
config.py -> MongoDB, fuentes, límites y parámetros HTTP.
database/ -> Acceso a MongoDB, exportación e índices.
  database/mongo.py -> Conexión, persistencia e índices MongoDB.
  database/create_indexes.py -> Entrada para crear índices.
  database/exporters.py -> Exporta documentos a JSON, CSV y SQLite.
processing/ -> Normalización, análisis y PLN.
  processing/clustering.py -> Agrupamiento temático K-means sobre la matriz TF-IDF.
  processing/normalizer.py -> Limpia HTML y normaliza texto/notas RSS.
  processing/analyzer.py -> Extrae palabras clave, conteos y hash.
  processing/preprocessor.py -> Tokeniza, filtra stopwords y aplica stemming.
  processing/unit3_statistics.py -> Calcula frecuencias, n-gramas y métricas.
  processing/vectorization.py -> Genera matrices BoW y TF-IDF.
scripts/ -> Herramientas CLI de consulta, inspección y procesamiento.
  scripts/preparar_unidad3.py -> Exporta, procesa, calcula estadísticas y vectoriza.
  scripts/asistente_voz.py -> Busca noticias por similitud TF-IDF y consulta de voz/texto.
  scripts/verinews.py -> Interfaz CLI unificada para búsqueda, voz, grupos y estadísticas.
  scripts/evaluar_unidad4.py -> Evalúa K-means con Silhouette Score para distintos valores de k.
  scripts/probar_busqueda.py -> Busca noticias con el índice de texto MongoDB.
  scripts/detectar_duplicados.py -> Agrupa duplicados exactos por hash.
  scripts/resumen_fuentes.py -> Resume documentos y texto suficiente por fuente.
  scripts/ver_documentos.py -> Muestra documentos recientes de MongoDB.
  scripts/ver_fuentes.py -> Lista fuentes y métodos almacenados.
tests/ -> Pruebas unitarias sin conexión a MongoDB ni micrófono.
  tests/test_unit3.py -> Prueba preprocesamiento, estadísticas y exportaciones/vectorización.
  tests/test_unit4.py -> Prueba el agrupamiento y validación de archivos de entrada.
data/ -> Salidas del pipeline; excluidas del control de versiones.
  data/unidad3/ -> Exportaciones, estadísticas, SQLite y matrices vectoriales.
run_acopio.py -> Entrada principal: recolecta noticias, analiza y guarda en MongoDB.
requirements.txt -> Dependencias principales de recolección y PLN.
requirements-voz.txt -> Dependencia adicional de audio para el asistente.
README.md -> Instalación, acopio, MongoDB y comandos generales.
README_UNIDAD3.md -> Pipeline PLN, salidas, búsqueda por voz y uso.
ENTREGABLE_UNIDAD3.md -> Documentación del entregable de PLN.
EVIDENCIAS.md -> Evidencias del proyecto.
FUENTES.md -> Fuentes de noticias documentadas.
rutas/ -> No hay rutas HTTP; las entradas son CLI: run_acopio.py y scripts/.
comandos/ -> Crear entorno: python -m venv venv; activar: source venv/bin/activate (Linux/macOS).
comandos/ -> Instalar: python -m pip install -r requirements.txt; stopwords: python -m nltk.downloader stopwords.
comandos/ -> Audio opcional: python -m pip install -r requirements-voz.txt.
comandos/ -> Índices: python -m database.create_indexes; recolectar: python run_acopio.py.
comandos/ -> PLN: python -m scripts.preparar_unidad3; probar: python -m unittest discover -s tests.
