import json
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

from pipeline.limpieza import (leer_todo, normalizar_telefono, normalizar_fecha,
                               normalizar_canal, normalizar_estado, normalizar_ciudad,
                               _buscar_modelo, normalizar_modelo)
from pipeline.duplicados import normalizar_nombre, detectar_duplicados, elegir_maestro

RAIZ = Path(__file__).resolve().parent.parent
RUTA_BD = RAIZ / "db" / "motos.db"
RUTA_SCHEMA = RAIZ / "db" / "schema.sql"
RUTA_SCORING = RAIZ / "artifacts" / "scoring.csv"
RUTA_EXTRA = RAIZ / "artifacts" / "extracciones.json"


def preparar_leads():
    datos = leer_todo()
    leads = datos["leads"].copy().drop_duplicates(subset="lead_id", keep="first")
    buscar = _buscar_modelo(datos["catalogo"])
    precios_map = dict(zip(datos["catalogo"]["sku"], datos["catalogo"]["precio_lista"]))

    leads["telefono_norm"] = leads["telefono"].map(normalizar_telefono)
    leads["fecha_registro_dt"] = leads["fecha_registro"].map(normalizar_fecha)
    leads["fecha_primer_contacto_dt"] = leads["fecha_primer_contacto"].map(normalizar_fecha)
    leads["canal_norm"] = leads["canal"].map(normalizar_canal)
    leads["estado_norm"] = leads["estado_gestion"].map(normalizar_estado)
    ciudad = leads["ciudad"].map(normalizar_ciudad)
    leads["ciudad_norm"] = [c[0] for c in ciudad]
    leads["departamento"] = [c[1] for c in ciudad]
    leads["nombre_norm"] = leads["nombre_cliente"].map(normalizar_nombre)

    horas = []
    for reg, pri in zip(leads["fecha_registro_dt"], leads["fecha_primer_contacto_dt"]):
        if reg is not None and pri is not None:
            horas.append(round(max(0.0, (pri - reg).total_seconds() / 3600), 2))
        else:
            horas.append(None)
    leads["horas_al_contacto"] = horas

    m = leads["modelo_interes_texto"].map(lambda t: normalizar_modelo(t, buscar))
    leads["sku_matcheado"] = [x[0] for x in m]
    leads["score_match"] = [x[1] for x in m]

    def _precio(sku):
        v = str(precios_map.get(sku, "")).replace(".", "").replace(",", "")
        return int(v) if v.isdigit() else 0
    leads["precio_lista"] = leads["sku_matcheado"].map(_precio)

    grupo_id = [None] * len(leads)
    es_maestro = [False] * len(leads)
    identidades = []
    for g, inds in enumerate(detectar_duplicados(leads).values()):
        etiqueta = f"GRP-{g + 1:04d}"
        m_row = elegir_maestro(leads, inds)
        for i in inds:
            grupo_id[i] = etiqueta
            es_maestro[i] = (i == m_row)
            identidades.append((etiqueta, leads.iloc[i]["lead_id"], int(i == m_row)))
    leads["grupo_id"] = grupo_id
    leads["es_maestro"] = [int(e) for e in es_maestro]
    return leads, identidades


def poblar_bd(conn):
    leads, identidades = preparar_leads()
    cols = ["lead_id", "nombre_cliente", "telefono_norm", "email", "ciudad_norm",
            "departamento", "canal_norm", "estado_norm", "fecha_registro",
            "horas_al_contacto", "sku_matcheado", "score_match", "precio_lista",
            "grupo_id", "es_maestro", "nombre_norm"]
    leads[cols].to_sql("leads", conn, if_exists="replace", index=False)

    pd.DataFrame(identidades, columns=["grupo_id", "lead_id", "es_maestro"]).to_sql(
        "identidades", conn, if_exists="replace", index=False)

    extra = json.loads(RUTA_EXTRA.read_text(encoding="utf-8"))
    filas_ext = []
    for cid, info in extra.items():
        d = info.get("datos") or {}
        filas_ext.append({
            "conversacion_id": cid, "lead_id": info.get("lead_id"),
            "origen": info.get("origen"), "presupuesto": d.get("presupuesto"),
            "modelo": d.get("modelo"), "cilindraje": d.get("cilindraje"),
            "fecha_cita": d.get("fecha_cita"), "cuota_inicial": d.get("cuota_inicial"),
            "cuota_mensual": d.get("cuota_mensual"), "uso": d.get("uso"),
            "negociable": int(bool(d.get("negociable"))) if d.get("negociable") is not None else None,
        })
    pd.DataFrame(filas_ext).to_sql("extracciones_ia", conn, if_exists="replace", index=False)

    scores = pd.read_csv(RUTA_SCORING)
    scores.to_sql("scores", conn, if_exists="replace", index=False)

    meta = {
        "corrida": datetime.now().isoformat(timespec="seconds"),
        "total_leads": int(len(leads)),
        "total_grupos": int(len(set(g for g, _, _ in identidades))),
        "total_extracciones_ia": int(len(filas_ext)),
        "con_origen_ia": int(sum(1 for r in filas_ext if r["origen"] == "ia")),
        "total_scores": int(len(scores)),
    }
    pd.DataFrame([{"clave": k, "valor": str(v)} for k, v in meta.items()]).to_sql(
        "metadatos", conn, if_exists="replace", index=False)

    conn.executescript("""
    CREATE INDEX IF NOT EXISTS idx_leads_grupo ON leads(grupo_id);
    CREATE INDEX IF NOT EXISTS idx_extracciones_lead ON extracciones_ia(lead_id);
    """)


def construir_bd(ruta=RUTA_BD):
    ruta.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(ruta)
    conn.executescript(RUTA_SCHEMA.read_text(encoding="utf-8"))
    poblar_bd(conn)
    conn.commit()
    conn.close()