import json
from pathlib import Path

from pipeline.limpieza import leer_todo, _buscar_modelo
from pipeline.scoring import (vector_historico, vector_leads, entrenar_modelo,
                              calcular_lift, generar_scores, guardar_scoring)

RAIZ = Path(__file__).resolve().parent
ARTIFACTOS = RAIZ / "artifacts"


def main():
    datos = leer_todo()
    hist = datos["historico"]
    leads = datos["leads"].copy().drop_duplicates(subset="lead_id", keep="first")
    buscar = _buscar_modelo(datos["catalogo"])
    precios = datos["catalogo"].set_index("sku")["precio_lista"].to_dict()
    extracciones = json.loads((ARTIFACTOS / "extracciones.json").read_text(encoding="utf-8"))
    n_mensajes = {}
    for c in datos["conversaciones"]:
        n_mensajes[c["lead_id"]] = max(n_mensajes.get(c["lead_id"], 0), len(c["mensajes"]))

    y = hist["desenlace"].eq("Cerrado")
    modelo, auc, Xte, yte, proba = entrenar_modelo(vector_historico(hist), y)
    lift = calcular_lift(yte, proba)

    Xl, info = vector_leads(leads, extracciones, precios, buscar, n_mensajes)
    resultado = generar_scores(modelo, Xl, info)
    guardar_scoring(resultado, ARTIFACTOS / "scoring.csv")

    print("=" * 62)
    print("FASE 4 - SCORING DE PRIORIZACION")
    print("=" * 62)
    print(f"Historico: {len(hist)} registros | cierres: {int(y.sum())} ({y.mean()*100:.1f}%)")
    print(f"AUC (test): {auc:.3f}")
    print(f"Lift top 20%: {lift:.2f}x")
    print(f"Leads con score: {len(resultado)}")
    print()
    print("TOP 10 LEADS A PRIORIZAR:")
    for _, r in resultado.sort_values("score", ascending=False).head(10).iterrows():
        print(f"  {r['lead_id']}  score={r['score']:3d}  {r['motivos']:<35} origen={r['origen'] or '-'}")


if __name__ == "__main__":
    main()