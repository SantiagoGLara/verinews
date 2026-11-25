"""Pruebas de la Parte 4 sin MongoDB ni micrófono."""

import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix, save_npz

from processing.clustering import (
    cargar_corpus, generar_agrupamientos, preparar_matriz_tematica,
)


class PruebasUnidad4(unittest.TestCase):
    def test_agrupamiento_y_exportacion(self):
        # Dos temas claramente separados para probar la integración de K-means.
        textos = [
            [1, 1, 0, 0], [1, 0.9, 0, 0], [0.9, 1, 0, 0],
            [0, 0, 1, 1], [0, 0, 0.9, 1], [0, 0, 1, 0.9],
        ]
        matriz = csr_matrix(np.asarray(textos, dtype=float))
        noticias = [
            {
                "titulo": f"Noticia {i}", "fuente_nombre": "Medio A" if i < 3 else "Medio B",
                "fecha_publicacion": f"2026-10-0{i + 1}",
                "url": f"https://ejemplo.mx/{i}", "resumen": "Resumen de prueba",
            }
            for i in range(6)
        ]

        with tempfile.TemporaryDirectory() as temporal:
            base = Path(temporal)
            with (base / "noticias_procesadas.csv").open("w", encoding="utf-8-sig", newline="") as archivo:
                import csv
                escritor = csv.DictWriter(archivo, fieldnames=list(noticias[0]))
                escritor.writeheader()
                escritor.writerows(noticias)
            save_npz(base / "matriz_tfidf.npz", matriz)
            import json
            with (base / "vocabulario_tfidf.json").open("w", encoding="utf-8") as archivo:
                json.dump({"tema_a": 0, "tema_b": 1, "tema_c": 2, "tema_d": 3}, archivo)

            cargadas, _, _ = cargar_corpus(base)
            self.assertEqual(len(cargadas), 6)
            resultado = generar_agrupamientos(base, n_clusters=2)
            self.assertEqual(resultado["documentos"], 6)
            self.assertEqual(len(resultado["grupos"]), 2)
            self.assertTrue((base / "agrupamientos_kmeans.json").exists())
            self.assertAlmostEqual(sum(g["cantidad"] for g in resultado["grupos"]), 6)

    def test_filtra_terminos_generales_sin_modificar_matriz_original(self):
        matriz = csr_matrix(np.asarray([[1, 1, 0], [0, 1, 1]], dtype=float))
        filtrada, terminos, excluidos = preparar_matriz_tematica(
            matriz, ["no", "huracan", "simon"]
        )
        self.assertEqual(filtrada.shape, (2, 2))
        self.assertEqual(terminos, ["huracan", "simon"])
        self.assertEqual(excluidos, ["no"])
        self.assertEqual(matriz.shape, (2, 3))

    def test_detecta_desfase_entre_csv_y_matriz(self):
        with tempfile.TemporaryDirectory() as temporal:
            base = Path(temporal)
            with (base / "noticias_procesadas.csv").open("w", encoding="utf-8-sig", newline="") as archivo:
                archivo.write("titulo\nUna noticia\n")
            save_npz(base / "matriz_tfidf.npz", csr_matrix([[1, 0], [0, 1]]))
            import json
            with (base / "vocabulario_tfidf.json").open("w", encoding="utf-8") as archivo:
                json.dump({"uno": 0, "dos": 1}, archivo)
            with self.assertRaises(ValueError):
                cargar_corpus(base)


if __name__ == "__main__":
    unittest.main()
