# -*- coding: utf-8 -*-
import pandas as pd
from pipeline.duplicados import normalizar_nombre, detectar_duplicados


def test_nombre():
    assert normalizar_nombre("  Maria Fernanda  Valencia ") == "maria fernanda valencia"
    assert normalizar_nombre("HECTOR GIRALDO RESTREPO") == "hector giraldo restrepo"


def test_detectar():
    leads = pd.DataFrame({
        "lead_id": ["LD-1", "LD-2", "LD-3", "LD-4"],
        "telefono_norm": ["3502258611", "3502258611", "3200000000", None],
        "nombre_norm": ["ana lopez", "ana lopez", "juan perez", "carlos gomez"],
        "ciudad_norm": ["Bogota D.C.", "", "Medellin", ""],
        "email": ["", "", "", "carlos@mail.com"],
    })
    grupos = detectar_duplicados(leads)
    tam = [len(v) for v in grupos.values()]
    assert max(tam) == 2
