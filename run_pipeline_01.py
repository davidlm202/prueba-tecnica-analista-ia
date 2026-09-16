# -*- coding: utf-8 -*-
"""Fase 1: ejecuta la ingesta + normalizacion y muestra el resumen."""
from pipeline.limpieza import (
    leer_todo, normalizar_telefono, normalizar_fecha, normalizar_canal,
    normalizar_estado, normalizar_ciudad, _buscar_modelo, normalizar_modelo,
    detectar_filas_duplicadas, cobertura_conversaciones,
)

if __name__ == "__main__":
    datos = leer_todo()
    leads = datos["leads"].copy()

    dups_ids, leads = detectar_filas_duplicadas(leads)

    buscar = _buscar_modelo(datos["catalogo"])
    leads["telefono_norm"] = leads["telefono"].map(normalizar_telefono)
    leads["fecha_registro_dt"] = leads["fecha_registro"].map(normalizar_fecha)
    leads["fecha_primer_contacto_dt"] = leads["fecha_primer_contacto"].map(normalizar_fecha)
    leads["canal_norm"] = leads["canal"].map(normalizar_canal)
    leads["estado_norm"] = leads["estado_gestion"].map(normalizar_estado)

    ciudad = leads["ciudad"].map(normalizar_ciudad)
    leads["ciudad_norm"] = [c[0] for c in ciudad]
    leads["departamento"] = [c[1] for c in ciudad]

    m = leads["modelo_interes_texto"].map(lambda t: normalizar_modelo(t, buscar))
    leads["sku_matcheado"] = [x[0] for x in m]
    leads["score_match"] = [x[1] for x in m]

    sin_match = leads[(leads["sku_matcheado"].isna()) & (leads["modelo_interes_texto"].str.strip() != "")]

    print("=" * 62)
    print("RESUMEN FASE 1 - INGESTA Y NORMALIZACION")
    print("=" * 62)
    print("Leads leidos:", len(datos["leads"]), "| Asesores:", len(datos["asesores"]),
          "| Catalogo:", len(datos["catalogo"]), "| Historico:", len(datos["historico"]),
          "| Conversaciones:", len(datos["conversaciones"]))
    print("Filas repetidas por lead_id:", dups_ids)
    print()
    print("Canales normalizados:")
    print(leads["canal_norm"].value_counts().to_string())
    print()
    print("Estados normalizados:")
    print(leads["estado_norm"].value_counts().to_string())
    print()
    print("Telefonos vacios tras normalizar:", int(leads["telefono_norm"].isna().sum()))
    print("Fechas de registro NO parseadas:", int(leads["fecha_registro_dt"].isna().sum()))
    print("Ciudades vacias:", int((leads["ciudad_norm"] == "").sum()))
    print("Modelos declarados sin match:", len(sin_match), "| ej:", sin_match["modelo_interes_texto"].head(8).tolist())
    print()
    print("Cobertura conversaciones:", cobertura_conversaciones(leads, datos["conversaciones"]))
    print("Telefonos con duplicados (par de filas):", int(leads["telefono_norm"].duplicated(keep=False).sum()))
    print()
    print("15 SKU de ejemplo (primera pasada):")
    print(leads[["lead_id", "modelo_interes_texto", "sku_matcheado", "score_match", "ciudad_norm", "departamento"]].head(15).to_string(index=False))
