# -*- coding: utf-8 -*-
from pipeline.extraer_ia import fallback_determinista, parsear_json


def test_presupuesto():
    d = fallback_determinista("Mi presupuesto es de 9 millones")
    assert d["presupuesto"] == 9000000


def test_fallback_cita_y_modelo():
    d = fallback_determinista("agende la cita para el 2026-09-10 de la AKT TTR 200")
    assert d["fecha_cita"] == "2026-09-10"
    assert d["modelo"] == "Akt Ttr 200"


def test_fallback_credito():
    d = fallback_determinista("puedo dar cuota inicial de 2 millones por mes")
    assert d["cuota_inicial"] == 2000000


def test_parsear_json():
    assert parsear_json('```json\n{"presupuesto": 8000000}\n```') == {"presupuesto": 8000000}