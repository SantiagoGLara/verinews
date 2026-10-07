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
