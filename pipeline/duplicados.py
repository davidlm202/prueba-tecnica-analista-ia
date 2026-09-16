# -*- coding: utf-8 -*-
"""Deteccion y agrupacion de leads duplicados (Fase 2)."""
from pipeline.limpieza import aplanar

TITULOS = ("sr ", "sra ", "dr ", "dra ", "ing ", "lic ")


def normalizar_nombre(nombre):
    n = aplanar(nombre)
    for t in TITULOS:
        n = n.replace(t, " ")
    return " ".join(n.split())


def _find(parent, x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def _union(parent, a, b):
    ra, rb = _find(parent, a), _find(parent, b)
    if ra != rb:
        parent[rb] = ra


def detectar_duplicados(leads):
    """Asigna a cada lead un grupo de identidad (telefono, nombre+ciudad o email)."""
    n = len(leads)
    parent = list(range(n))

    por_tel = {}
    por_nom = {}
    por_mail = {}
    for i, r in leads.iterrows():
        t = r.get("telefono_norm") or ""
        if t and t in por_tel:
            _union(parent, i, por_tel[t])
        elif t:
            por_tel[t] = i

        k = (r.get("nombre_norm") or "", r.get("ciudad_norm") or "")
        if k[0] and k in por_nom:
            _union(parent, i, por_nom[k])
        elif k[0]:
            por_nom[k] = i

        e = aplanar(r.get("email") or "")
        if e and e in por_mail:
            _union(parent, i, por_mail[e])
        elif e:
            por_mail[e] = i

    grupos = {}
    for i in range(n):
        grupos.setdefault(_find(parent, i), []).append(i)
    return grupos


def puntaje_maestro(r):
    pts = 0
    if r.get("telefono_norm"):
        pts += 10
    if aplanar(r.get("email") or ""):
        pts += 15
    if r.get("ciudad_norm"):
        pts += 5
    if str(r.get("modelo_interes_texto") or "").strip():
        pts += 5
    if r.get("canal_norm") == "WhatsApp":
        pts += 5
    return pts


def elegir_maestro(leads, indices):
    return max(indices, key=lambda i: puntaje_maestro(leads.iloc[i]))
