# Leads Inteligentes — Motos y Motores del Norte S.A.S.

Solución automatizada que convierte los leads crudos de tres canales (WhatsApp, Meta Ads y
Formulario Web) en una lista priorizada de gestión diaria por asesor, enriquecida con IA
desde las conversaciones de WhatsApp.

## Estado
En construcción.

## Estructura del repositorio
- data/entregados/ — datasets sintéticos de la prueba (solo lectura).
- pipeline/ — orquestación: ingesta, normalización, deduplicación, IA, scoring y persistencia.
- app/ — tablero público (Streamlit): "mis leads de hoy" por asesor y empresa.
- db/ — esquema versionado de la base de datos (SQLite).
- analysis/ — calibración y validación del modelo de priorización.
- presentacion/ — láminas de sustentación.
- tests/ — pruebas.
