from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from pipeline.limpieza import normalizar_canal, normalizar_fecha, normalizar_modelo

ARTIFACTOS = Path(__file__).resolve().parent.parent / "artifacts"


def _a_num(v, defecto=10000000.0):
    t = str(v).replace(".", "").replace(",", "").strip()
    try:
        return float(t) if t else defecto
    except ValueError:
        return defecto


def _binario(S):
    return S.astype(str).str.strip().str.upper().eq("SI").astype(int)


def vector_historico(h):
    df = pd.DataFrame(index=h.index)
    df["horas"] = pd.to_numeric(h["horas_al_primer_contacto"], errors="coerce").fillna(24).clip(0, 720)
    df["contactos"] = pd.to_numeric(h["numero_contactos"], errors="coerce").fillna(3)
    df["precio_lista"] = h["precio_lista"].map(_a_num)
    canal = h["canal"].map(normalizar_canal)
    df["canal_whatsapp"] = canal.eq("WhatsApp").astype(int)
    df["canal_meta"] = canal.eq("Meta Ads").astype(int)
    df["canal_form"] = canal.eq("Formulario Web").astype(int)
    df["pidio_cita"] = _binario(h["pidio_cita"])
    df["manifesto_cuota"] = _binario(h["manifesto_cuota_inicial"])
    df["pago_credito"] = h["forma_pago_declarada"].astype(str).str.strip().str.lower().eq("credito").astype(int)
    return df


def vector_leads(leads, extracciones, precios, buscar, n_mensajes,
                 mediana_horas=24.0, mediana_contactos=3.0):
    por_lead = {}
    for conv in extracciones.values():
        por_lead.setdefault(conv["lead_id"], conv)
    filas = []
    for _, r in leads.iterrows():
        conv = por_lead.get(r["lead_id"])
        if conv:
            d = conv["datos"]
            pidio = int(d.get("fecha_cita") not in (None, ""))
            cuota = int(d.get("cuota_inicial") not in (None, ""))
            credito = int(d.get("cuota_mensual") not in (None, ""))
        else:
            pidio = cuota = credito = 0
        reg = normalizar_fecha(r["fecha_registro"])
        pri = normalizar_fecha(r["fecha_primer_contacto"])
        horas = mediana_horas
        if reg is not None and pri is not None:
            horas = (pri - reg).total_seconds() / 3600
        sku, _ = normalizar_modelo(r["modelo_interes_texto"], buscar) if buscar else (None, 0)
        canal = normalizar_canal(r["canal"])
        n = n_mensajes.get(r["lead_id"], 0)
        contactos = (n // 2) if n else mediana_contactos
        filas.append({
            "lead_id": r["lead_id"],
            "origen": (conv or {}).get("origen", ""),
            "horas": max(0.0, horas),
            "contactos": float(max(1, contactos)),
            "precio_lista": _a_num(precios.get(sku, 10000000)),
            "canal_whatsapp": int(canal == "WhatsApp"),
            "canal_meta": int(canal == "Meta Ads"),
            "canal_form": int(canal == "Formulario Web"),
            "pidio_cita": pidio,
            "manifesto_cuota": cuota,
            "pago_credito": credito,
        })
    info = pd.DataFrame(filas)
    X = info[["horas", "contactos", "precio_lista", "canal_whatsapp", "canal_meta",
              "canal_form", "pidio_cita", "manifesto_cuota", "pago_credito"]]
    return X, info


def entrenar_modelo(X, y):
    modelo = LogisticRegression(max_iter=2000, random_state=42)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    modelo.fit(Xtr, ytr)
    proba = modelo.predict_proba(Xte)[:, 1]
    auc = float(roc_auc_score(yte, proba))
    return modelo, auc, Xte, yte, proba


def calcular_lift(y, proba, pct=0.2):
    n = max(1, int(len(y) * pct))
    idx = np.argsort(proba)[::-1][:n]
    base = float(np.mean(np.asarray(y)))
    top = float(np.mean(np.asarray(y)[idx]))
    return top / base if base > 0 else 0.0


def motivos_lead(row):
    motivos = []
    if row["pidio_cita"]:
        motivos.append("pidio_cita")
    if row["manifesto_cuota"]:
        motivos.append("cuota_inicial")
    if row["pago_credito"]:
        motivos.append("credito")
    if row["horas"] <= 8:
        motivos.append("contacto_rapido")
    if row["canal_whatsapp"]:
        motivos.append("canal_whatsapp")
    return "+".join(motivos) if motivos else "seguimiento"


def generar_scores(modelo, X_leads, info):
    proba = modelo.predict_proba(X_leads)[:, 1]
    info = info.copy()
    info["score"] = np.round(proba * 100).astype(int)
    info["motivos"] = info.apply(motivos_lead, axis=1)
    return info


def guardar_scoring(info, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    info[["lead_id", "origen", "score", "motivos", "horas", "contactos", "precio_lista",
          "pidio_cita", "manifesto_cuota", "pago_credito"]].to_csv(ruta, index=False, encoding="utf-8")