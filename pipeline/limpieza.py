# -*- coding: utf-8 -*-
"""Ingesta y normalizacion de los archivos fuente (Fase 1)."""
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd
from rapidfuzz import process

DATA = Path(__file__).resolve().parent.parent / "data" / "entregados"

CIUDADES = {
    "bogot": ("Bogota D.C.", "Cundinamarca"),
    "medell": ("Medellin", "Antioquia"),
    "monter": ("Monteria", "Cordoba"),
    "barranq": ("Barranquilla", "Atlantico"),
    "b/quilla": ("Barranquilla", "Atlantico"),
    "cartag": ("Cartagena", "Bolivar"),
    "santa marta": ("Santa Marta", "Magdalena"),
    "sta marta": ("Santa Marta", "Magdalena"),
    "soacha": ("Soacha", "Cundinamarca"),
    "soledad": ("Soledad", "Atlantico"),
    "itag": ("Itagui", "Antioquia"),
    "bello": ("Bello", "Antioquia"),
    "rionegro": ("Rionegro", "Antioquia"),
    "rio negro": ("Rionegro", "Antioquia"),
    "ri negro": ("Rionegro", "Antioquia"),
}


def aplanar(texto):
    """Minusculas, sin acentos y sin espacios repetidos."""
    t = unicodedata.normalize("NFD", str(texto or ""))
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", t.strip().lower())


def leer_todo():
    """Carga los 5 archivos fuente y devuelve un diccionario."""
    return {
        "leads": pd.read_csv(DATA / "leads.csv", dtype=str, keep_default_na=False),
        "asesores": pd.read_csv(DATA / "asesores.csv", dtype=str, keep_default_na=False),
        "catalogo": pd.read_csv(DATA / "catalogo_motos.csv", dtype=str, keep_default_na=False),
        "historico": pd.read_csv(DATA / "historico_cierres.csv", dtype=str, keep_default_na=False),
        "conversaciones": json.loads((DATA / "conversaciones.json").read_text(encoding="utf-8")),
    }


def normalizar_telefono(tel):
    """Elimina espacios, guiones, parentesis y el prefijo 57."""
    d = re.sub(r"\D", "", tel or "")
    if d.startswith("57"):
        d = d[2:]
    d = d.lstrip("0")
    if len(d) > 10:
        d = d[-10:]
    return d or None


def normalizar_fecha(texto):
    """Parsea los distintos formatos de fecha usados en los archivos."""
    t = str(texto or "").strip()
    if not t:
        return None
    m = re.match(r"^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}(?::\d{2})?)", t)
    if m:
        try:
            return pd.Timestamp(m.group(1) + " " + m.group(2))
        except ValueError:
            return None
    m = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})(?:[ T](\d{2}:\d{2}))?", t)
    if not m:
        return None
    a, b, anio = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if b > 12:  # formato MM/DD (p. ej. 08/18/2026)
        a, b = b, a
    texto_fecha = f"{anio:04d}-{b:02d}-{a:02d}"
    if m.group(4):
        texto_fecha += " " + m.group(4)
    try:
        return pd.Timestamp(texto_fecha)
    except ValueError:
        return None


def normalizar_canal(canal):
    c = aplanar(canal)
    if c.startswith("whats"):
        return "WhatsApp"
    if c.startswith("meta"):
        return "Meta Ads"
    if c.startswith("form"):
        return "Formulario Web"
    return "Desconocido" if not c else str(canal).strip()


def normalizar_estado(estado):
    c = aplanar(estado)
    for canon, claves in [
        ("Cotizacion enviada", ["cotizacion enviada", "cotizaci"]),
        ("No contesta", ["no contesta", "no cont"]),
        ("En proceso", ["en proceso", "proceso"]),
        ("Descartado", ["descartado"]),
        ("Contactado", ["contactado"]),
    ]:
        if any(k in c for k in claves):
            return canon
    return "Sin gestion" if c in ("", "sin gestion") else str(estado).strip()


def normalizar_ciudad(ciudad):
    c = aplanar(ciudad)
    if not c:
        return "", ""
    for patron, canon in CIUDADES.items():
        if patron in c:
            return canon
    return ciudad.strip().title(), "Sin departamento"


def _norm_modelo(t):
    t = aplanar(t)
    t = t.replace("a.k.t", "akt").replace("suzuky", "suzuki").replace("hnda", "honda")
    return re.sub(r"(20\d\d)", " ", t).strip()


def _buscar_modelo(catalogo):
    busqueda = {}
    for _, r in catalogo.iterrows():
        clave = _norm_modelo(r["marca"] + " " + r["linea"])
        busqueda[clave] = str(r["sku"])
    return busqueda


def normalizar_modelo(texto, busqueda):
    t = _norm_modelo(texto)
    if not t:
        return None, 0
    mejor, score, _ = process.extractOne(t, list(busqueda.keys()))
    if score >= 70:
        return busqueda[mejor], int(score)
    return None, 0


def detectar_filas_duplicadas(leads):
    duplicadas = leads[leads.duplicated(subset="lead_id", keep=False)]
    return duplicadas["lead_id"].tolist(), leads.drop_duplicates(subset="lead_id", keep="first")


def cobertura_conversaciones(leads, conversaciones):
    ids = set(leads["lead_id"])
    conv_ids = [c["lead_id"] for c in conversaciones]
    return {
        "leads_whatsapp": int((leads["canal_norm"] == "WhatsApp").sum()),
        "leads_sin_conversacion": len(ids - set(conv_ids)),
        "conversaciones_huerfanas": len([c for c in conversaciones if c["lead_id"] not in ids]),
        "conversaciones_repetidas": len(conv_ids) - len(set(conv_ids)),
    }


