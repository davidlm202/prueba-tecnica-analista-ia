import sqlite3

from pipeline.bd import RUTA_BD, construir_bd


def _bd():
    construir_bd()
    return sqlite3.connect(RUTA_BD)


def test_conteos():
    conn = _bd()
    cur = conn.cursor()
    assert cur.execute("SELECT COUNT(*) FROM leads").fetchone()[0] == 1501
    assert cur.execute("SELECT COUNT(*) FROM identidades").fetchone()[0] == 1501
    assert cur.execute("SELECT COUNT(*) FROM extracciones_ia").fetchone()[0] == 677
    assert cur.execute("SELECT COUNT(*) FROM scores").fetchone()[0] == 1501
    conn.close()


def test_join_priorizacion():
    conn = _bd()
    filas = conn.execute("""
        SELECT l.lead_id, s.score FROM leads l
        JOIN scores s ON l.lead_id = s.lead_id
        ORDER BY s.score DESC LIMIT 3
    """).fetchall()
    assert len(filas) == 3
    assert all(f[1] >= 0 for f in filas)
    conn.close()