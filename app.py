import json
from pathlib import Path

import pandas as pd
import streamlit as st

from pipeline.limpieza import (leer_todo, normalizar_canal, normalizar_estado,
                               normalizar_ciudad)
from pipeline.duplicados import detectar_duplicados, normalizar_nombre

RAIZ = Path(__file__).resolve().parent
RUTA_SCORING = RAIZ / "artifacts" / "scoring.csv"
RUTA_EXTRA = RAIZ / "artifacts" / "extracciones.json"

st.set_page_config(page_title="Panel de Priorizacion de Leads - IA", layout="wide")


@st.cache_data(show_spinner=False)
def cargar_datos():
    datos = leer_todo()
    scores = pd.read_csv(RUTA_SCORING, encoding="utf-8")
    extra = json.loads(RUTA_EXTRA.read_text(encoding="utf-8"))
    return datos, scores, extra


def main():
    datos, scores, extra = cargar_datos()
    leads = datos["leads"].copy()

    leads["canal_norm"] = leads["canal"].map(normalizar_canal)
    leads["estado_norm"] = leads["estado_gestion"].map(normalizar_estado)
    ciudad = leads["ciudad"].map(normalizar_ciudad)
    leads["ciudad_norm"] = [c[0] for c in ciudad]
    leads["depto"] = [c[1] for c in ciudad]
    leads["nombre_norm"] = leads["nombre_cliente"].map(normalizar_nombre)

    grupos = {}
    for g, inds in enumerate(detectar_duplicados(leads).values()):
        for i in inds:
            grupos[leads.iloc[i]["lead_id"]] = f"GRP-{g + 1:04d}"
    leads["grupo_id"] = leads["lead_id"].map(grupos)

    df = leads.merge(scores, on="lead_id", how="left")
    n_extra = len(extra)
    n_ia = sum(1 for e in extra.values() if e.get("origen") == "ia")

    st.title("Panel de Priorizacion de Leads - Inteligencia Artificial")
    st.caption("Pipeline: normalizacion -> deduplicacion -> IA Gemini -> scoring -> BD")

    canales = sorted(df["canal_norm"].dropna().unique())
    estados = sorted(df["estado_norm"].dropna().unique())
    empresas = sorted(df["empresa_id"].dropna().unique())
    with st.sidebar:
        st.header("Filtros")
        sel_empresa = st.selectbox("Empresa", ["Todas"] + empresas)
        sel_canal = st.multiselect("Canal", canales, default=[])
        sel_estado = st.multiselect("Estado", estados, default=[])
        top_n = st.slider("Top leads", 10, 50, 30)
        debug = st.checkbox("Mostrar datos en bruto (debug)")

    vista = df
    if sel_empresa != "Todas":
        vista = vista[vista["empresa_id"] == sel_empresa]
    if sel_canal:
        vista = vista[vista["canal_norm"].isin(sel_canal)]
    if sel_estado:
        vista = vista[vista["estado_norm"].isin(sel_estado)]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Leads unicos", f"{len(vista):,}")
    n_grupos = vista["grupo_id"].nunique() if sel_empresa != "Todas" else len(grupos)
    c2.metric("Grupos deduplicados", f"{n_grupos:,}")
    c3.metric("Conversaciones IA", f"{n_extra:,}", f"{n_ia:,} por IA")
    c4.metric("Score promedio", f"{vista['score'].mean():.0f}")

    st.subheader(f"Top {top_n} leads a priorizar por el asesor")
    cols = ["lead_id", "nombre_cliente", "empresa_id", "ciudad_norm", "canal_norm",
            "estado_norm", "grupo_id", "score", "motivos", "origen"]
    st.dataframe(
        vista.sort_values("score", ascending=False).head(top_n)[cols],
        width="stretch", hide_index=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Leads por canal")
        st.bar_chart(vista["canal_norm"].value_counts())
        st.subheader("Distribucion del score")
        hist = vista["score"].value_counts().sort_index()
        st.bar_chart(hist)
    with col_b:
        st.subheader("Leads por estado")
        st.bar_chart(vista["estado_norm"].value_counts())
        st.subheader("Top 10 ciudades")
        st.bar_chart(vista["ciudad_norm"].value_counts().head(10))

    with st.expander("Ver un ejemplo de extraccion IA"):
        cid, info = next(iter(extra.items()))
        st.json({"conversacion_id": cid, **info})

    if debug:
        st.subheader("Datos en bruto")
        st.dataframe(vista.head(500), width="stretch", hide_index=True)


if __name__ == "__main__":
    main()