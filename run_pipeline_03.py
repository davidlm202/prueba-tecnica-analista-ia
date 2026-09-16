"""Fase 3: enriquecer conversaciones con IA (con fallback y cache)."""
import json
from pathlib import Path

from pipeline.extraer_ia import (CAMPOS, cargar_config, extraer_info_conversacion,
                                 cargar_cache, guardar_cache)

RAIZ = Path(__file__).resolve().parent
RUTA_CONV = RAIZ / "data" / "entregados" / "conversaciones.json"


def texto_conversacion(conv):
    partes = [f"{m.get('emisor','')}: {m.get('texto','')}" for m in conv.get("mensajes", [])]
    return "\n".join(partes)


def main():
    cfg = cargar_config()
    conversaciones = json.loads(RUTA_CONV.read_text(encoding="utf-8"))
    cache = cargar_cache()
    print(f"Config: LLM_PROVIDER={cfg.get('LLM_PROVIDER')}")
    print(f"Conversaciones: {len(conversaciones)} | cache previa: {len(cache)}")

    contadores = {"ia": 0, "fallback": 0, "cache": 0}
    for conv in conversaciones:
        ident = conv.get("conversacion_id")
        if not ident or ident in cache:
            contadores["cache"] += 1
            continue
        texto = texto_conversacion(conv)
        if not texto.strip():
            continue
        datos, origen = extraer_info_conversacion(texto, cfg)
        cache[ident] = {"lead_id": conv.get("lead_id"), "datos": datos, "origen": origen}
        contadores[origen] += 1

    guardar_cache(cache)
    print(f"Extraidas por IA: {contadores['ia']} | fallback: {contadores['fallback']} | cache: {contadores['cache']}")
    print(f"Total en cache final: {len(cache)}")


if __name__ == "__main__":
    main()