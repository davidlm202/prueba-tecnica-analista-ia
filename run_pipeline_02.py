# -*- coding: utf-8 -*-
"""Fase 2: agrupa leads duplicados y elige representante de cada grupo."""
from pipeline.limpieza import leer_todo, aplanar, normalizar_telefono, normalizar_ciudad, normalizar_canal, normalizar_fecha
from pipeline.duplicados import normalizar_nombre, detectar_duplicados, elegir_maestro

if __name__ == "__main__":
    datos = leer_todo()
    leads = datos["leads"].copy().drop_duplicates(subset="lead_id", keep="first")
    leads["telefono_norm"] = leads["telefono"].map(normalizar_telefono)
    leads["fecha_registro_dt"] = leads["fecha_registro"].map(normalizar_fecha)
    leads["canal_norm"] = leads["canal"].map(normalizar_canal)
    leads["ciudad_norm"] = [normalizar_ciudad(c)[0] for c in leads["ciudad"]]
    leads["nombre_norm"] = leads["nombre_cliente"].map(normalizar_nombre)

    marcas = {"bajaj", "honda", "suzuki", "akt", "hero"}
    leads["solo_marca"] = [aplanar(m) in marcas for m in leads["modelo_interes_texto"]]

    grupo_id = [None] * len(leads)
    es_maestro = [False] * len(leads)
    grupos = detectar_duplicados(leads)
    for g, inds in enumerate(grupos.values()):
        etiqueta = f"GRP-{g + 1:04d}"
        m = elegir_maestro(leads, inds)
        for i in inds:
            grupo_id[i] = etiqueta
            es_maestro[i] = (i == m)
    leads["grupo_id"] = grupo_id
    leads["es_maestro"] = es_maestro

    en_duplicado = sum(len(v) for v in grupos.values() if len(v) > 1)
    cruza = int(leads.groupby("grupo_id")["empresa_id"].nunique().gt(1).sum())

    print("=" * 62)
    print("RESUMEN FASE 2 - DEDUPLICACION E IDENTIDADES")
    print("=" * 62)
    print("Leads unicos:", len(leads), "| Grupos de identidad:", len(grupos))
    print("Leads que comparten identidad con otro:", en_duplicado)
    print("Tamano maximo de grupo:", int(leads.groupby("grupo_id").size().max()))
    print("Grupos cuya identidad cruza 2+ empresas:", cruza)
    print("Leads que declaran SOLO marca (sin modelo):", int(leads["solo_marca"].sum()))
    print()
    print("Ejemplos de duplicados (maestro / miembro):")
    vistos = 0
    for inds in sorted(grupos.values(), key=len, reverse=True):
        if len(inds) > 1:
            for i in inds:
                r = leads.iloc[i]
                tag = "*Maestro" if es_maestro[i] else " Miembro"
                print(f"  {tag} {r['lead_id']} emp={r['empresa_id']} tel={r['telefono_norm']} nom={r['nombre_norm'][:22]:22} canal={r['canal_norm']}")
            print("  ---")
            vistos += 1
            if vistos >= 4:
                break
