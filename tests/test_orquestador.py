import sqlite3

from pipeline.bd import RUTA_BD
from pipeline.orquestador import ejecutar_todo


def test_pipeline_completo():
    res = ejecutar_todo()
    assert res["leads"] == 1501
    assert res["extracciones_ia"] == 677
    assert res["scores"] == 1501
    assert res["tiempo_total"] >= 0


def test_bd_tiene_tablas():
    conn = sqlite3.connect(RUTA_BD)
    n = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    conn.close()
    assert n >= 5