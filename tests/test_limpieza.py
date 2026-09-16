# -*- coding: utf-8 -*-
"""Pruebas de la Fase 1."""
from pipeline.limpieza import normalizar_telefono, normalizar_fecha, normalizar_canal, normalizar_estado


def test_telefono():
    assert normalizar_telefono("+57 350 2258611") == "3502258611"
    assert normalizar_telefono("573112634024") == "3112634024"
    assert normalizar_telefono("(322) 624-9985") == "3226249985"
    assert normalizar_telefono("310 482 4081") == "3104824081"


def test_fecha():
    assert str(normalizar_fecha("25-08-2026").date()) == "2026-08-25"
    assert str(normalizar_fecha("27/08/2026 22:50").date()) == "2026-08-27"
    assert str(normalizar_fecha("08/18/2026 17:23").date()) == "2026-08-18"
    assert str(normalizar_fecha("03/08/2026 10:30").date()) == "2026-08-03"


def test_canal():
    assert normalizar_canal("WHATSAPP") == "WhatsApp"
    assert normalizar_canal("meta ads") == "Meta Ads"
    assert normalizar_canal("Formulario Web") == "Formulario Web"


def test_estado():
    assert normalizar_estado("SIN GESTION") == "Sin gestion"
    assert normalizar_estado("contactado") == "Contactado"
