# VeriNews - Fase 2 multifuente

Esta versión amplía el prototipo inicial a **siete medios independientes**.

## Fuentes configuradas

1. MiMorelia - RSS
2. Aristegui Noticias - RSS
3. López-Dóriga Digital - RSS
4. El Financiero - RSS
5. 24 Horas - RSS
6. La Jornada - descubrimiento desde portada
7. Publimetro México - descubrimiento desde sección Noticias

El sistema usa RSS cuando hay un feed utilizable. En La Jornada y Publimetro se usa una página índice muy limitada para descubrir URLs de artículos y después realizar scraping del artículo.

## Flujo

`fuente -> descubrimiento -> robots.txt -> descarga -> scraping -> normalización -> análisis -> MongoDB -> índices`

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
```

## MongoDB

```bash
mongosh "mongodb://localhost:27017/"
```

## Crear índices

```bash
python -m database.create_indexes
```

## Ejecutar acopio

```bash
python run_acopio.py
```

Con 20 entradas máximas por fuente, una ejecución puede revisar hasta aproximadamente 140 noticias, dependiendo de cuántas entradas entregue cada fuente y de las políticas de cada sitio.

## Revisar documentos

```bash
python -m scripts.ver_documentos
```

## Resumen por fuente

```bash
python -m scripts.resumen_fuentes
```

## Buscar por texto

```bash
python -m scripts.probar_busqueda
```

## Detectar duplicados exactos

```bash
python -m scripts.detectar_duplicados
```

## Consultas en mongosh

```javascript
use verinews
db.noticias.countDocuments()
db.noticias.getIndexes()
db.noticias.findOne()
```

Cantidad por fuente:

```javascript
db.noticias.aggregate([
  {
    $group: {
      _id: "$fuente.nombre",
      cantidad: { $sum: 1 }
    }
  },
  { $sort: { cantidad: -1 } }
])
```

## Qué enseñar en la revisión

- Código de los recolectores.
- Ejecución de `run_acopio.py`.
- Varias fuentes distintas.
- Documento de MongoDB con `acopio` y `analisis`.
- `db.noticias.getIndexes()`.
- Búsqueda con score.
- Segunda ejecución sin duplicar URLs.
- Resumen de documentos por fuente.
- Detección de duplicados exactos por hash.
