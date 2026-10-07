# VeriNews - Fase 2

## Objetivo

Construir el corpus inicial mediante el flujo:

RSS -> scraping HTML -> normalización -> análisis básico -> MongoDB -> índices.

## Requisitos

- Python 3.10 o superior.
- MongoDB Community Server.
- Acceso a Internet.

## 1. Crear entorno virtual

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

## 2. Instalar dependencias

```bash
python -m pip install -r requirements.txt
```

## 3. Comprobar MongoDB

```bash
mongosh "mongodb://localhost:27017/"
```

Para salir:

```text
exit
```

## 4. Crear índices

Desde la carpeta raíz del proyecto:

```bash
python -m database.create_indexes
```

## 5. Ejecutar el acopio

```bash
python run_acopio.py
```

## 6. Ver documentos

```bash
python -m scripts.ver_documentos
```

## 7. Probar búsqueda

```bash
python -m scripts.probar_busqueda
```

## Consultas útiles en mongosh

```javascript
use verinews
db.noticias.countDocuments()
db.noticias.find().limit(3)
db.noticias.getIndexes()
```

Búsqueda textual:

```javascript
db.noticias.find(
  { $text: { $search: "inteligencia artificial" } },
  {
    titulo: 1,
    fuente_rss: 1,
    score: { $meta: "textScore" }
  }
).sort({
  score: { $meta: "textScore" }
})
```

## Qué demuestra esta fase

- acopio automatizado;
- RSS;
- scraping;
- normalización;
- análisis básico;
- almacenamiento MongoDB;
- control de duplicados por URL;
- índices;
- recuperación textual con score.

## Fuentes iniciales

Los tres feeds iniciales son los que aparecen en la práctica RSS de la unidad.
Más adelante conviene incorporar medios independientes.
