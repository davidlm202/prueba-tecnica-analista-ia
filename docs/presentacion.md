# Presentación Gamma — Guion (8 láminas)

## L1 Portada
Pipeline de Priorización de Leads con IA — Prueba técnica Analista de IA.
Motos y Motores del Norte S.A.S. — [Nombre del candidato] — Septiembre 2026.

## L2 El reto
Convierto 1.501 leads crudos en una lista priorizada para los asesores:
normalización de datos sucios, deduplicación, enriquecimiento con IA
generativa, scoring predictivo de conversión y dashboard en vivo.

## L3 Arquitectura
Flujo: datos → normalización → deduplicación → Gemini (con cache) →
regresión logística → SQLite → dashboard. Un solo comando `python run_pipeline.py`
ejecuta todo en 3.7 segundos (con cache) y se regenera solo cada mañana vía CI.

## L4 Normalización y deduplicación
Teléfonos, fechas, canales, estados, ciudades y modelos homologados.
Deduplicación por 3 reglas → 1.357 grupos de identidad sobre 1.501 leads.

## L5 IA con Gemini
677 conversaciones enriquecidas: 657 por Gemini (97%) y 20 con respaldo
determinista → el pipeline nunca falla. Cache total en el repo: cero llamadas
a API en la demo, clonación lista en segundos.

## L6 Scoring predictivo
Regresión logística entrenada sobre 2.200 registros históricos (197 cierres).
AUC 0.600 y Lift de 1.53× en el top 20%: los priorizados convierten ~1.5 veces
más que el promedio.

## L7 Base de datos y dashboard
SQLite central (leads, identidades, extracciones IA, scores, metadatos).
Dashboard Streamlit: KPIs, Top de priorizados con motivos, gráficos por canal,
estado y ciudad, con filtros para el asesor.

## L8 Sustentamiento y cierre
CI diario (06:05 Bogotá) reelabora scores automáticamente; prueba: un clon
corre en minutos. 16 pruebas automatizadas, 9 fases versionadas (F0–F8).