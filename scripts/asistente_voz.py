"""Asistente de voz para consultar noticias de VeriNews usando TF-IDF.

Ejemplos desde la raíz del proyecto:
    python -m scripts.asistente_voz
    python -m scripts.asistente_voz --texto "noticias de seguridad en Michoacán" --solo-texto
"""

import argparse
import csv
from pathlib import Path

import joblib
from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity

from processing.preprocessor import obtener_stopwords, preprocesar_texto

ROOT = Path(__file__).resolve().parents[1]
DATOS = ROOT / "data" / "unidad3"


def reconocer_voz():
    try:
        import speech_recognition as sr
    except ImportError as exc:
        raise RuntimeError("Falta SpeechRecognition. Instale las dependencias de requirements.txt.") from exc

    reconocedor = sr.Recognizer()
    try:
        with sr.Microphone(device_index=10) as microfono:
            print("Ajustando el micrófono al ruido ambiental...")
            reconocedor.adjust_for_ambient_noise(microfono, duration=0.6)
            print("Hable ahora: diga qué tipo de noticia desea buscar.")
            audio = reconocedor.listen(microfono, timeout=8, phrase_time_limit=15)
        texto = reconocedor.recognize_google(audio, language="es-MX")
        print("Consulta reconocida:", texto)
        return texto
    except Exception as exc:
        try:
            import speech_recognition as sr
            if isinstance(exc, sr.UnknownValueError):
                raise RuntimeError("No se entendió el audio. Intente hablar más claro y cerca del micrófono.") from exc
            if isinstance(exc, sr.RequestError):
                raise RuntimeError("Falló el servicio de reconocimiento. Verifique su conexión a Internet.") from exc
            if isinstance(exc, sr.WaitTimeoutError):
                raise RuntimeError("No se detectó voz dentro del tiempo de espera.") from exc
        except ImportError:
            pass
        if "pyaudio" in str(exc).lower() or "microphone" in str(exc).lower():
            raise RuntimeError("No se pudo abrir el micrófono. Instale PyAudio y revise los permisos de audio.") from exc
        raise


def buscar_noticias(consulta, limite=3):
    ruta_vectorizador = DATOS / "vectorizador_tfidf.joblib"
    ruta_matriz = DATOS / "matriz_tfidf.npz"
    ruta_csv = DATOS / "noticias_procesadas.csv"
    for ruta in (ruta_vectorizador, ruta_matriz, ruta_csv):
        if not ruta.exists():
            raise FileNotFoundError(
                f"No existe {ruta.name}. Ejecute primero: python -m scripts.preparar_unidad3"
            )

    vectorizador = joblib.load(ruta_vectorizador)
    matriz = load_npz(ruta_matriz)
    with ruta_csv.open("r", encoding="utf-8-sig", newline="") as archivo:
        noticias = list(csv.DictReader(archivo))

    stopwords_es = obtener_stopwords()
    procesado = preprocesar_texto(consulta, stopwords_es)
    texto_consulta = procesado["texto_stem"]
    if not texto_consulta.strip():
        return [], "La consulta no contiene términos suficientes después del preprocesamiento."

    vector_consulta = vectorizador.transform([texto_consulta])
    if vector_consulta.nnz == 0:
        return [], "No encontré términos de la consulta dentro del vocabulario indexado."

    puntajes = cosine_similarity(vector_consulta, matriz).ravel()
    indices = puntajes.argsort()[::-1][:limite]
    resultados = []
    for indice in indices:
        puntaje = float(puntajes[indice])
        if puntaje <= 0:
            continue
        noticia = noticias[int(indice)]
        resultados.append({
            "titulo": noticia.get("titulo") or "Sin título",
            "fuente": noticia.get("fuente_nombre") or "Fuente desconocida",
            "fecha": noticia.get("fecha_publicacion") or "",
            "url": noticia.get("url") or "",
            "resumen": noticia.get("resumen") or "",
            "contenido": noticia.get("contenido") or "",
            "similitud": round(puntaje, 4),
        })

    if not resultados:
        return [], "No encontré noticias con similitud léxica positiva. Pruebe otra consulta."
    return resultados, ""


def sintetizar(texto):
    try:
        import pyttsx3
        motor = pyttsx3.init()
        motor.setProperty("rate", 165)
        voces = motor.getProperty("voices")
        for voz in voces:
            etiqueta = f"{getattr(voz, 'id', '')} {getattr(voz, 'name', '')}".lower()
            if any(palabra in etiqueta for palabra in ("spanish", "español", "espanol", "mex", "es_")):
                motor.setProperty("voice", voz.id)
                break
        motor.say(texto)
        motor.runAndWait()
        motor.stop()
    except Exception as exc:
        print("Aviso: no fue posible sintetizar voz en este sistema:", exc)


def main():
    parser = argparse.ArgumentParser(description="Consulta noticias VeriNews por voz y similitud TF-IDF.")
    parser.add_argument("--texto", help="Consulta escrita; si se omite, se usa el micrófono.")
    parser.add_argument("--solo-texto", action="store_true", help="No reproduce audio; útil para pruebas.")
    parser.add_argument("--limite", type=int, default=3, help="Cantidad máxima de noticias a mostrar.")
    args = parser.parse_args()

    consulta = args.texto.strip() if args.texto else reconocer_voz()
    resultados, aviso = buscar_noticias(consulta, limite=max(1, args.limite))
    if aviso:
        print(aviso)
        if not args.solo_texto:
            sintetizar(aviso)
        return

    print("\nResultados ordenados por similitud coseno:")
    for numero, resultado in enumerate(resultados, start=1):
        print(f"\n{numero}. {resultado['titulo']}")
        print(f"   Fuente: {resultado['fuente']} | Similitud: {resultado['similitud']}")
        if resultado["fecha"]:
            print(f"   Fecha: {resultado['fecha']}")
        print(f"   URL: {resultado['url']}")
        resumen = resultado["resumen"] or resultado["contenido"]
        if resumen:
            print("   Extracto:", resumen[:280].strip())

    primero = resultados[0]
    resumen_voz = (primero["resumen"] or primero["contenido"] or "").strip()
    respuesta = f"Encontré {len(resultados)} noticias similares. La más relacionada es: {primero['titulo']}, de {primero['fuente']}."
    if resumen_voz:
        respuesta += " Extracto: " + resumen_voz[:350]
    if not args.solo_texto:
        sintetizar(respuesta)


if __name__ == "__main__":
    main()
