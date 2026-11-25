"""Pruebas unitarias de las funciones de soporte de la interfaz web."""

import unittest

from scripts.interfaz_web import (
    cargar_estadisticas,
    obtener_agrupamientos,
    obtener_grupo,
    resumir_grupos,
)


class PruebasInterfazWeb(unittest.TestCase):
    def test_cargar_estadisticas_conserva_corpus(self):
        datos = cargar_estadisticas()
        self.assertGreater(datos.get("total_noticias", 0), 0)
        self.assertTrue(datos.get("por_fuente"))

    def test_resumen_grupos_no_incluye_todas_las_noticias(self):
        resultado = obtener_agrupamientos()
        resumen = resumir_grupos(resultado)
        self.assertEqual(resumen["documentos"], resultado["documentos"])
        self.assertEqual(len(resumen["grupos"]), resultado["numero_grupos"])
        self.assertNotIn("noticias", resumen["grupos"][0])

    def test_obtener_detalle_grupo(self):
        resultado = obtener_agrupamientos()
        numero = resultado["grupos"][0]["grupo"]
        grupo = obtener_grupo(numero, resultado)
        self.assertEqual(grupo["grupo"], numero)
        self.assertTrue(grupo["noticias"])

    def test_grupo_inexistente_lanza_error(self):
        with self.assertRaises(KeyError):
            obtener_grupo(999, {"grupos": []})


class PruebasHTTPInterfaz(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import threading
        from http.server import ThreadingHTTPServer
        from scripts.interfaz_web import VeriNewsHandler

        cls.servidor = ThreadingHTTPServer(("127.0.0.1", 0), VeriNewsHandler)
        cls.hilo = threading.Thread(target=cls.servidor.serve_forever, daemon=True)
        cls.hilo.start()
        cls.base = f"http://127.0.0.1:{cls.servidor.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()
        cls.hilo.join(timeout=2)

    def _get_json(self, ruta):
        import json
        from urllib.request import urlopen

        with urlopen(self.base + ruta, timeout=10) as respuesta:
            return respuesta.status, json.loads(respuesta.read().decode("utf-8"))

    def test_inicio_entrega_interfaz_html(self):
        from urllib.request import urlopen

        with urlopen(self.base + "/", timeout=10) as respuesta:
            html = respuesta.read().decode("utf-8")
            self.assertEqual(respuesta.status, 200)
            self.assertIn("VeriNews", html)
            self.assertIn("Grupos temáticos", html)

    def test_api_estadisticas(self):
        estado, datos = self._get_json("/api/estadisticas")
        self.assertEqual(estado, 200)
        self.assertGreater(datos["total_noticias"], 0)
        self.assertGreater(datos["noticias_con_cuerpo"], 0)
        self.assertGreater(datos["noticias_solo_resumen"], 0)
        self.assertEqual(datos["total_noticias"], datos["noticias_con_cuerpo"] + datos["noticias_solo_resumen"] + datos["noticias_sin_texto"])
        self.assertEqual(len(datos["por_fuente"]), 7)

    def test_api_grupos_y_detalle(self):
        estado, datos = self._get_json("/api/grupos")
        self.assertEqual(estado, 200)
        self.assertEqual(datos["numero_grupos"], 14)
        estado_detalle, detalle = self._get_json("/api/grupos/1")
        self.assertEqual(estado_detalle, 200)
        self.assertTrue(detalle["noticias"])

    def test_api_busqueda_reutiliza_tfidf(self):
        estado, datos = self._get_json("/api/buscar?q=huracan%20simon&limite=5")
        self.assertEqual(estado, 200)
        self.assertEqual(datos["consulta"], "huracan simon")
        self.assertTrue(datos["resultados"])
        self.assertIn("similitud", datos["resultados"][0])

    def test_api_investigar_construye_expediente(self):
        estado, datos = self._get_json("/api/investigar?q=huracan%20simon%20michoacan&limite=20")
        self.assertEqual(estado, 200)
        self.assertEqual(datos["metodo_recuperacion"], "tfidf")
        self.assertGreater(datos["resumen"]["publicaciones_recuperadas"], 0)
        self.assertGreater(datos["resumen"]["medios_distintos"], 1)
        self.assertTrue(datos["cronologia"])
        self.assertTrue(datos["fuentes"])
        self.assertIn("grupos_cobertura", datos)
        self.assertIn("tipo_fuente", datos["fuentes"][0])
        self.assertIn("indice_corpus", datos["resultados"][0])

    def test_api_investigar_rechaza_metodo_invalido(self):
        from urllib.error import HTTPError
        import json
        with self.assertRaises(HTTPError) as contexto:
            from urllib.request import urlopen
            urlopen(self.base + "/api/investigar?q=huracan&metodo=incorrecto", timeout=10)
        self.assertEqual(contexto.exception.code, 400)
        datos = json.loads(contexto.exception.read().decode("utf-8"))
        self.assertIn("Método", datos["error"])

    def test_api_clasificar_valida_cantidad_de_indices(self):
        import json
        from urllib.request import Request, urlopen
        solicitud = Request(
            self.base + "/api/clasificar",
            data=json.dumps({"indices": []}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        from urllib.error import HTTPError
        with self.assertRaises(HTTPError) as contexto:
            urlopen(solicitud, timeout=10)
        self.assertEqual(contexto.exception.code, 400)

    def test_api_investigar_lsa_experimental(self):
        estado, datos = self._get_json("/api/investigar?q=huracan%20simon%20michoacan&limite=10&metodo=lsa")
        self.assertEqual(estado, 200)
        self.assertEqual(datos["metodo_recuperacion"], "lsa")
        self.assertTrue(datos["resultados"])

    def test_api_clasificar_informa_dependencia_opcional(self):
        import importlib.util
        if importlib.util.find_spec("transformers") is not None:
            self.skipTest("Transformers está instalado; no se descarga el modelo en pruebas automáticas.")
        import json
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError
        solicitud = Request(
            self.base + "/api/clasificar",
            data=json.dumps({"indices": [0]}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as contexto:
            urlopen(solicitud, timeout=10)
        self.assertEqual(contexto.exception.code, 503)
        datos = json.loads(contexto.exception.read().decode("utf-8"))
        self.assertIn("requirements-clasificacion", datos["error"])


if __name__ == "__main__":
    unittest.main()
