"""Pruebas rápidas sin conexión a MongoDB ni acceso al micrófono."""

import tempfile
import unittest
from pathlib import Path

from processing.preprocessor import obtener_stopwords, preprocesar_texto
from processing.unit3_statistics import calcular_estadisticas
from processing.vectorization import vectorizar
from database.exporters import construir_registro, exportar_sqlite


class PruebasUnidad3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stopwords_es = obtener_stopwords()
        cls.documentos = [
            {
                "_id": "prueba-1", "url": "https://ejemplo.mx/1",
                "titulo": "Gobierno anuncia medidas de seguridad en Morelia",
                "resumen": "Autoridades informan nuevas medidas.",
                "contenido": "La seguridad pública será prioridad. No se descartan operativos.",
                "fuente": {"nombre": "Medio A", "tipo_acopio": "rss", "dominio": "ejemplo.mx"},
                "acopio": {"metodo": "rss+scraping", "status_http": 200},
            },
            {
                "_id": "prueba-2", "url": "https://ejemplo.mx/2",
                "titulo": "Autoridades investigan hechos violentos",
                "resumen": "La fiscalía inició investigaciones.",
                "contenido": "Las autoridades investigan hechos de violencia en Michoacán.",
                "fuente": {"nombre": "Medio B", "tipo_acopio": "rss", "dominio": "ejemplo.mx"},
                "acopio": {"metodo": "rss+scraping", "status_http": 200},
            },
        ]

    def test_preprocesamiento_elimina_numeros_y_conserva_negacion(self):
        resultado = preprocesar_texto("NOTICIA 2026: No hay 3 medidas; seguridad pública.", self.stopwords_es)
        self.assertNotIn("2026", resultado["tokens_limpios"])
        self.assertNotIn("3", resultado["tokens_limpios"])
        self.assertIn("no", resultado["tokens_limpios"])
        self.assertIn("seguridad", resultado["tokens_limpios"])

    def test_estadisticas_y_vectorizacion(self):
        registros = []
        for doc in self.documentos:
            texto = " ".join(doc.get(k, "") for k in ("titulo", "resumen", "contenido"))
            registros.append(construir_registro(doc, preprocesar_texto(texto, self.stopwords_es)))
        estadisticas = calcular_estadisticas(registros, limite=30)
        self.assertEqual(estadisticas["total_noticias"], 2)
        self.assertGreater(estadisticas["tokens_limpios_total"], 0)
        with tempfile.TemporaryDirectory() as temporal:
            info = vectorizar(registros, temporal, max_features=1000)
            self.assertEqual(info["forma_matriz_tfidf"][0], 2)
            exportar_sqlite(registros, estadisticas["frecuencias_palabras"],
                            estadisticas["frecuencias_bigramas"] + estadisticas["frecuencias_trigramas"],
                            Path(temporal) / "noticias.sqlite")
            self.assertTrue((Path(temporal) / "matriz_tfidf.npz").exists())
            self.assertTrue((Path(temporal) / "noticias.sqlite").exists())


if __name__ == "__main__":
    unittest.main()
