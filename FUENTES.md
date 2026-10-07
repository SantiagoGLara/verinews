# Fuentes de la Fase 2

## RSS

- MiMorelia
- Aristegui Noticias
- López-Dóriga Digital
- El Financiero
- 24 Horas

## Página índice + scraping

- La Jornada
- Publimetro México

## Razón del diseño

RSS reduce el trabajo de descubrimiento porque ya entrega entradas estructuradas con título, enlace y normalmente fecha. El scraping se usa para intentar obtener el texto completo del artículo.

Las páginas índice se usan como un crawler muy limitado: solo se siguen patrones de URL de noticias, se limita la cantidad de enlaces y se consulta `robots.txt` antes de continuar.

Si el scraping de un artículo falla, el sistema conserva los datos recuperados por RSS o por la página índice y registra el error dentro de `acopio.error_scraping`.
