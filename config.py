MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "verinews"
MONGO_COLLECTION = "noticias"

USER_AGENT = "VeriNewsAcademico/1.0 (proyecto escolar de recuperacion de informacion)"
REQUEST_TIMEOUT = 15
REQUEST_DELAY_SECONDS = 1.0

# Feeds tomados de la práctica RSS de la unidad.
RSS_SOURCES = [
    {
        "nombre": "MiMorelia - Ultimas noticias",
        "url": "https://mimorelia.com/rss/pages/ultimas-noticias.xml",
    },
    {
        "nombre": "MiMorelia - Morelia",
        "url": "https://mimorelia.com/rss/pages/morelia.xml",
    },
    {
        "nombre": "MiMorelia - Ciencia y Tecnologia",
        "url": "https://mimorelia.com/rss/pages/ciencia-y-tecnologia.xml",
    },
]

# Para la demostración no conviene descargar demasiado de golpe.
MAX_ITEMS_PER_FEED = 20
