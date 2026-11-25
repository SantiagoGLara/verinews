"""Pruebas del expediente y del clasificador opcional."""

import unittest
from unittest.mock import patch

from processing.investigation import construir_expediente
from processing.topic_classifier import clasificar_registros


class PruebasExpediente(unittest.TestCase):
    def test_expediente_contiene_cronologia_fuentes_y_cobertura(self):
        expediente = construir_expediente("huracan simon michoacan", limite=15)
        self.assertGreater(expediente["resumen"]["publicaciones_recuperadas"], 0)
        self.assertGreater(expediente["resumen"]["medios_distintos"], 1)
        self.assertTrue(expediente["cronologia"])
        self.assertTrue(expediente["fuentes"])
        self.assertTrue(expediente["grupos_cobertura"])
        self.assertTrue(all(f["tipo_fuente"] == "Sin determinar" for f in expediente["fuentes"]))
        self.assertTrue(any("independientes" in aviso for aviso in expediente["avisos"]))

    def test_rechaza_consulta_vacia(self):
        with self.assertRaises(ValueError):
            construir_expediente("   ")

    def test_detecta_candidatos_similares_en_un_mismo_evento(self):
        expediente = construir_expediente("centro exterminio nayarit", limite=20)
        self.assertTrue(expediente["pares_similares"])
        self.assertGreaterEqual(expediente["pares_similares"][0]["similitud"], 0.78)
        self.assertEqual(expediente["pares_similares"][0]["tipo"], "similitud_alta")
        self.assertTrue(expediente["grupos_cobertura"])
        self.assertGreaterEqual(expediente["grupos_cobertura"][0]["cantidad"], 2)


class ClasificadorFalso:
    def __call__(self, texto, **kwargs):
        return {"labels": ["Política y gobierno", "Economía"], "scores": [0.82, 0.18]}


class PruebasClasificadorOpcional(unittest.TestCase):
    def test_clasifica_con_pipeline_simulado(self):
        registros = [{"titulo": "Noticia de prueba", "resumen": "Congreso aprueba una reforma"}]
        with patch("processing.topic_classifier.obtener_clasificador", return_value=ClasificadorFalso()):
            resultado = clasificar_registros(registros)
        self.assertEqual(resultado["predicciones"][0]["categoria_sugerida"], "Política y gobierno")
        self.assertGreater(resultado["predicciones"][0]["afinidad_modelo"], 0.8)
        self.assertIn("no son etiquetas verificadas", resultado["nota"])

    def test_limita_clasificacion_a_ocho_registros(self):
        with self.assertRaises(ValueError):
            clasificar_registros([{"titulo": "Noticia"} for _ in range(9)])


if __name__ == "__main__":
    unittest.main()
