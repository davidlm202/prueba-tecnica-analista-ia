import json
from pathlib import Path

from pipeline.limpieza import leer_todo, _buscar_modelo
from pipeline.scoring import (vector_historico, entrenar_modelo,
                              vector_leads, generar_scores)


def test_auc_mayor_a_55():
    datos = leer_todo()
    y = datos["historico"]["desenlace"].eq("Cerrado")
    _, auc, _, _, _ = entrenar_modelo(vector_historico(datos["historico"]), y)
    assert auc > 0.55


def test_scores_rango_y_motivos():
    datos = leer_todo()
    buscar = _buscar_modelo(datos["catalogo"])
    precios = datos["catalogo"].set_index("sku")["precio_lista"].to_dict()
    extra = json.loads(Path("artifacts/extracciones.json").read_text(encoding="utf-8"))
    n_msg = {c["lead_id"]: len(c["mensajes"]) for c in datos["conversaciones"]}
    leads = datos["leads"].drop_duplicates(subset="lead_id", keep="first")
    Xl, info = vector_leads(leads, extra, precios, buscar, n_msg)
    y = datos["historico"]["desenlace"].eq("Cerrado")
    modelo, *_ = entrenar_modelo(vector_historico(datos["historico"]), y)
    res = generar_scores(modelo, Xl, info)
    assert res["score"].between(0, 100).all()
    assert res["motivos"].str.len().gt(0).all()