# VeriNews — Fase 2 multifuente y procesamiento de noticias

Esta versión amplía el prototipo inicial a siete medios y agrega procesamiento de lenguaje natural, recuperación textual, agrupamiento temático y una interfaz web de investigación.

## Fuentes configuradas

1. MiMorelia — RSS
2. Aristegui Noticias — RSS
3. López-Dóriga Digital — RSS
4. El Financiero — RSS
5. 24 Horas — RSS
6. La Jornada — descubrimiento desde portada
7. Publimetro México — descubrimiento desde sección Noticias

La presencia de distintos medios no demuestra por sí misma independencia editorial.

## Instalación

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

```bash
python -m pip install -r requirements.txt
python -m nltk.downloader stopwords
```

## Recolección y almacenamiento

```bash
python -m database.create_indexes
python run_acopio.py
python -m scripts.ver_documentos
python -m scripts.resumen_fuentes
python -m scripts.probar_busqueda
python -m scripts.detectar_duplicados
```

El proyecto usa MongoDB local. Consulte `config.py` para la conexión y las fuentes.

## Unidad 3 — Procesamiento de Lenguaje Natural

```bash
python -m scripts.preparar_unidad3
python -m scripts.asistente_voz --texto "noticias de seguridad en Michoacán" --solo-texto
```

La consulta por voz requiere las dependencias de `requirements-voz.txt` y un micrófono configurado.

## Unidad 4 — Investigación de evidencia

La GUI organiza una consulta como expediente: publicaciones relacionadas, cronología, análisis de procedencia, cobertura textual y posibles duplicados/coberturas similares.

```bash
# GUI web local
python -m scripts.interfaz_web

# CLI
python -m scripts.verinews

# Evaluación comparativa principal
python -m scripts.evaluar_unidad4_completa

# Pruebas
python -m unittest discover -s tests -v
```

La clasificación zero-shot con mDeBERTa es opcional:

```bash
python -m pip install -r requirements-clasificacion.txt
```

Consulte [README_UNIDAD4.md](README_UNIDAD4.md) para el flujo de investigación, evaluación, limitaciones y comandos completos.
