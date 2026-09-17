import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from pipeline.extraer_ia import cargar_config, extraer_info_conversacion, cargar_cache, guardar_cache

RAIZ = Path(__file__).resolve().parent
RUTA_CONV = RAIZ / "data" / "entregados" / "conversaciones.json"
TRABAJADORES = 3
GUARDAR_CADA = 25


def texto_conversacion(conv):
    partes = [f"{m.get('emisor', '')}: {m.get('texto', '')}" for m in conv.get("mensajes", [])]
    return "\n".join(partes)


def main():
    cfg = cargar_config()
    conversaciones = json.loads(RUTA_CONV.read_text(encoding="utf-8"))
    cache = cargar_cache()
    total = len(conversaciones)
    print(f"Config: LLM_PROVIDER={cfg.get('LLM_PROVIDER')}")
    print(f"Conversaciones: {total} | cache previa: {len(cache)}")

    pendientes = [c for c in conversaciones
                  if c.get("conversacion_id") not in cache and texto_conversacion(c).strip()]
    hechas = total - len(pendientes)
    contadores = {"ia": 0, "fallback": 0}
    lock = threading.Lock()
    progreso = {"n": 0}

    def procesar(conv):
        datos, origen = extraer_info_conversacion(texto_conversacion(conv), cfg)
        return conv.get("conversacion_id"), conv.get("lead_id"), datos, origen

    print(f"A extraer: {len(pendientes)} conversaciones con {TRABAJADORES} trabajadores...")
    with ThreadPoolExecutor(max_workers=TRABAJADORES) as pool:
        futuros = [pool.submit(procesar, c) for c in pendientes]
        for futuro in as_completed(futuros):
            ident, lead_id, datos, origen = futuro.result()
            cache[ident] = {"lead_id": lead_id, "datos": datos, "origen": origen}
            with lock:
                contadores[origen] += 1
                progreso["n"] += 1
                n = progreso["n"]
            if n % GUARDAR_CADA == 0:
                guardar_cache(cache)
                print(f"  ... {hechas + n}/{total} | IA: {contadores['ia']} | fallback: {contadores['fallback']}")

    guardar_cache(cache)
    print(f"Extraidas por IA: {contadores['ia']} | fallback: {contadores['fallback']} | cache: {len(cache)}")


if __name__ == "__main__":
    main()