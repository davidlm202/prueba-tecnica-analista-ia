import sqlite3
import time

from pipeline.limpieza import leer_todo
from pipeline.bd import RUTA_BD


def etapa_datos():
    datos = leer_todo()
    return {
        "leads": len(datos["leads"]),
        "asesores": len(datos["asesores"]),
        "catalogo": len(datos["catalogo"]),
        "historico": len(datos["historico"]),
        "conversaciones": len(datos["conversaciones"]),
    }


def etapa_extraccion():
    from run_pipeline_03 import main
    main()


def etapa_scoring():
    from run_pipeline_04 import main
    main()


def etapa_bd():
    from run_pipeline_05 import main
    main()


def totales_bd():
    conn = sqlite3.connect(RUTA_BD)
    cur = conn.cursor()
    res = {t: cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
           for t in ["leads", "identidades", "extracciones_ia", "scores"]}
    res["grupos"] = cur.execute("SELECT COUNT(DISTINCT grupo_id) FROM leads").fetchone()[0]
    conn.close()
    return res


def ejecutar_todo():
    print("=" * 62)
    print("PIPELINE COMPLETO (F1 a F5) - INICIO")
    print("=" * 62)
    t_inicio = time.time()

    t = time.time()
    fuentes = etapa_datos()
    print(f"[F1] Fuentes: leads {fuentes['leads']} | conversaciones {fuentes['conversaciones']} | "
          f"catalogo {fuentes['catalogo']} | historico {fuentes['historico']} | asesores {fuentes['asesores']}"
          f"  ({time.time() - t:.1f}s)")

    t = time.time()
    etapa_extraccion()
    print(f"[F3] Extraccion IA  ({time.time() - t:.1f}s)")

    t = time.time()
    etapa_scoring()
    print(f"[F4] Scoring       ({time.time() - t:.1f}s)")

    t = time.time()
    etapa_bd()
    print(f"[F5] Base de datos  (identidades/grupos de F2 incluidas) ({time.time() - t:.1f}s)")

    totales = totales_bd()
    total = time.time() - t_inicio
    print()
    print("=" * 62)
    print("RESUMEN EJECUTIVO")
    print("=" * 62)
    for k, v in totales.items():
        print(f"  {k:<16} {v}")
    print(f"Tiempo total: {total:.1f} segundos")
    return {**totales, "tiempo_total": round(total, 1)}