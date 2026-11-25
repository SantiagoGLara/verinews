"""Interfaz web local de VeriNews (sin dependencias web adicionales).

Ejecutar desde la raíz del proyecto:
    python -m scripts.interfaz_web

La interfaz se sirve únicamente en localhost. Reutiliza TF-IDF, añade un flujo
experimental LSA y organiza expedientes con cronología y análisis de procedencia.
"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
import webbrowser

from processing.clustering import cargar_agrupamientos, cargar_corpus, generar_agrupamientos
from processing.investigation import construir_expediente
from scripts.asistente_voz import buscar_noticias

ROOT = Path(__file__).resolve().parents[1]
DATOS = ROOT / "data" / "unidad3"
WEB = ROOT / "web"
ARCHIVO_ESTADISTICAS = DATOS / "estadisticas.json"


def cargar_estadisticas():
    """Carga las estadísticas generadas en la Unidad 3."""
    if not ARCHIVO_ESTADISTICAS.exists():
        raise FileNotFoundError(
            "No existe data/unidad3/estadisticas.json. "
            "Ejecute primero: python -m scripts.preparar_unidad3"
        )
    with ARCHIVO_ESTADISTICAS.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def obtener_agrupamientos(recalcular=False):
    """Reutiliza los grupos vigentes o los genera si no existen/están obsoletos."""
    resultado = None if recalcular else cargar_agrupamientos(DATOS)
    if resultado is None:
        resultado = generar_agrupamientos(DATOS, n_clusters=14)
    return resultado


def resumir_grupos(resultado):
    """Devuelve los metadatos de los grupos sin enviar todas sus noticias."""
    return {
        "generado": resultado.get("generado", ""),
        "documentos": resultado.get("documentos", 0),
        "numero_grupos": resultado.get("numero_grupos", 0),
        "silhouette_coseno": resultado.get("silhouette_coseno", 0),
        "grupos": [
            {
                "grupo": grupo.get("grupo"),
                "cantidad": grupo.get("cantidad", 0),
                "porcentaje": grupo.get("porcentaje", 0),
                "terminos_representativos": grupo.get("terminos_representativos", []),
                "fuentes": grupo.get("fuentes", [])[:4],
                "fecha_inicial": grupo.get("fecha_inicial", ""),
                "fecha_final": grupo.get("fecha_final", ""),
            }
            for grupo in resultado.get("grupos", [])
        ],
    }


def obtener_grupo(numero, resultado=None):
    """Obtiene el detalle de un grupo por su identificador de presentación."""
    resultado = resultado or obtener_agrupamientos()
    for grupo in resultado.get("grupos", []):
        if int(grupo.get("grupo", -1)) == int(numero):
            return grupo
    raise KeyError(f"No existe el grupo {numero}.")


class VeriNewsHandler(BaseHTTPRequestHandler):
    """Manejador HTTP para la GUI y su API JSON local."""

    server_version = "VeriNewsLocal/2.0"

    def log_message(self, formato, *args):
        # Evita llenar la terminal con cada recurso estático de la interfaz.
        if self.path.startswith("/api/"):
            super().log_message(formato, *args)

    def _responder(self, contenido, tipo="application/json; charset=utf-8", estado=200):
        if isinstance(contenido, str):
            contenido = contenido.encode("utf-8")
        self.send_response(estado)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(contenido)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(contenido)

    def _json(self, datos, estado=200):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self._responder(cuerpo, estado=estado)

    def do_GET(self):
        ruta = urlsplit(self.path)
        path = unquote(ruta.path)
        parametros = parse_qs(ruta.query)

        if path == "/" or path == "/index.html":
            archivo = WEB / "index.html"
            if not archivo.exists():
                self._responder("No se encontró web/index.html", "text/plain; charset=utf-8", 500)
                return
            self._responder(archivo.read_bytes(), "text/html; charset=utf-8")
            return

        if path == "/api/salud":
            self._json({"ok": True, "aplicacion": "VeriNews", "version": "Parte 4"})
            return

        if path == "/api/investigar":
            consulta = (parametros.get("q") or [""])[0].strip()
            try:
                limite = int((parametros.get("limite") or ["20"])[0])
            except ValueError:
                limite = 20
            metodo = (parametros.get("metodo") or ["tfidf"])[0].strip().lower()
            if not consulta:
                self._json({"error": "Escriba una afirmación, titular o acontecimiento para investigar."}, 400)
                return
            if metodo not in {"tfidf", "lsa"}:
                self._json({"error": "Método de recuperación no válido."}, 400)
                return
            try:
                expediente = construir_expediente(consulta, limite=limite, metodo=metodo)
                self._json(expediente)
            except Exception as exc:
                self._json({"error": str(exc)}, 500)
            return

        if path == "/api/buscar":
            consulta = (parametros.get("q") or [""])[0].strip()
            try:
                limite = int((parametros.get("limite") or ["8"])[0])
            except ValueError:
                limite = 8
            limite = max(1, min(limite, 20))
            if not consulta:
                self._json({"consulta": "", "resultados": [], "aviso": "Escriba un tema o acontecimiento para buscar."}, 400)
                return
            try:
                resultados, aviso = buscar_noticias(consulta, limite=limite)
                self._json({"consulta": consulta, "resultados": resultados, "aviso": aviso})
            except Exception as exc:
                self._json({"error": str(exc)}, 500)
            return

        if path == "/api/grupos":
            try:
                self._json(resumir_grupos(obtener_agrupamientos()))
            except Exception as exc:
                self._json({"error": str(exc)}, 500)
            return

        if path.startswith("/api/grupos/"):
            identificador = path.rsplit("/", 1)[-1]
            if not identificador.isdigit():
                self._json({"error": "El identificador del grupo debe ser numérico."}, 400)
                return
            try:
                grupo = obtener_grupo(int(identificador))
                self._json(grupo)
            except KeyError as exc:
                self._json({"error": str(exc)}, 404)
            except Exception as exc:
                self._json({"error": str(exc)}, 500)
            return

        if path == "/api/estadisticas":
            try:
                datos = cargar_estadisticas()
                registros, _, _ = cargar_corpus(DATOS)
                con_cuerpo = sum(bool((n.get("contenido") or "").strip()) for n in registros)
                solo_resumen = sum(
                    not (n.get("contenido") or "").strip()
                    and bool((n.get("resumen") or n.get("titulo") or "").strip())
                    for n in registros
                )
                sin_texto = len(registros) - con_cuerpo - solo_resumen
                self._json({
                    "total_noticias": datos.get("total_noticias", 0),
                    "noticias_con_texto": datos.get("noticias_con_texto", 0),
                    "noticias_con_cuerpo": con_cuerpo,
                    "noticias_solo_resumen": solo_resumen,
                    "noticias_sin_texto": sin_texto,
                    "tokens_limpios_total": datos.get("tokens_limpios_total", 0),
                    "vocabulario_total": datos.get("vocabulario_total", 0),
                    "diversidad_lexica_corpus": datos.get("diversidad_lexica_corpus", 0),
                    "por_fuente": sorted(
                        datos.get("por_fuente", []),
                        key=lambda x: x.get("noticias", 0),
                        reverse=True,
                    ),
                    "frecuencias_palabras": datos.get("frecuencias_palabras", [])[:12],
                })
            except Exception as exc:
                self._json({"error": str(exc)}, 500)
            return

        self._json({"error": "Ruta no encontrada."}, 404)

    def do_POST(self):
        path = urlsplit(self.path).path
        if path == "/api/grupos/recalcular":
            try:
                resultado = obtener_agrupamientos(recalcular=True)
                self._json({
                    "ok": True,
                    "mensaje": "Los grupos temáticos se recalcularon correctamente.",
                    **resumir_grupos(resultado),
                })
            except Exception as exc:
                self._json({"error": str(exc)}, 500)
            return

        if path == "/api/clasificar":
            try:
                longitud = int(self.headers.get("Content-Length", "0"))
                if longitud < 1 or longitud > 20000:
                    self._json({"error": "Solicitud vacía o demasiado grande."}, 400)
                    return
                cuerpo = json.loads(self.rfile.read(longitud).decode("utf-8"))
                indices = cuerpo.get("indices", [])
                if not isinstance(indices, list) or not indices or len(indices) > 8:
                    self._json({"error": "Seleccione entre 1 y 8 noticias para clasificar."}, 400)
                    return
                indices = [int(i) for i in indices]
                registros, _, _ = cargar_corpus(DATOS)
                if any(i < 0 or i >= len(registros) for i in indices):
                    self._json({"error": "Uno o más identificadores de noticia no son válidos."}, 400)
                    return
                seleccion = []
                for indice in indices:
                    noticia = dict(registros[indice])
                    noticia["indice_corpus"] = indice
                    seleccion.append(noticia)
                from processing.topic_classifier import clasificar_registros
                resultado = clasificar_registros(seleccion)
                self._json(resultado)
            except RuntimeError as exc:
                self._json({"error": str(exc)}, 503)
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                self._json({"error": str(exc)}, 400)
            except Exception as exc:
                self._json({"error": str(exc)}, 500)
            return

        self._json({"error": "Ruta no encontrada."}, 404)


def main():
    parser = argparse.ArgumentParser(description="Inicia la interfaz web local de VeriNews.")
    parser.add_argument("--host", default="127.0.0.1", help="Dirección de escucha (por defecto: localhost).")
    parser.add_argument("--port", type=int, default=8000, help="Puerto HTTP (por defecto: 8000).")
    parser.add_argument("--no-browser", action="store_true", help="No abrir automáticamente el navegador.")
    args = parser.parse_args()

    if not (WEB / "index.html").exists():
        raise SystemExit("No se encontró web/index.html. Verifique que ejecuta desde el proyecto completo.")

    servidor = ThreadingHTTPServer((args.host, args.port), VeriNewsHandler)
    url = f"http://{args.host}:{args.port}"
    print("=" * 58)
    print("VERINEWS | Interfaz web local")
    print(f"Abre en tu navegador: {url}")
    print("Para detener el servidor, presiona Ctrl+C.")
    print("=" * 58)

    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            print("No fue posible abrir el navegador automáticamente.")

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrando VeriNews...")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
