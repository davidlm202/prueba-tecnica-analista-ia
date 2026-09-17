import sqlite3

from pipeline.bd import RUTA_BD, construir_bd


def main():
    construir_bd()
    conn = sqlite3.connect(RUTA_BD)
    cur = conn.cursor()
    print("=" * 62)
    print("FASE 5 - BASE DE DATOS SQLITE")
    print("=" * 62)
    for tabla in ["leads", "identidades", "extracciones_ia", "scores", "metadatos"]:
        n = cur.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        print(f"  {tabla:<16} {n}")
    print()
    print("TOP 10 PRIORIZADOS (dashboard diario):")
    print(f"  {'lead_id':<9} {'nombre':<24} {'ciudad':<16} {'canal':<15} {'score':>5}  motivos")
    for f in cur.execute("""
        SELECT l.lead_id, l.nombre_cliente, l.ciudad_norm, l.canal_norm,
               s.score, s.motivos, s.origen
        FROM leads l JOIN scores s ON l.lead_id = s.lead_id
        ORDER BY s.score DESC LIMIT 10
    """):
        print(f"  {f[0]:<9} {str(f[1])[:23]:<24} {str(f[2])[:15]:<16} {str(f[3])[:14]:<15} {f[4]:>5}  {f[5]} ({f[6]})")
    conn.close()


if __name__ == "__main__":
    main()