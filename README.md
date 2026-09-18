# Prueba Técnica — Analista de IA | Priorización de Leads

Pipeline end-to-end para convertir leads crudos en una **lista priorizada para
asesores comerciales**, enriquecida con IA generativa (Gemini), persistida en
SQLite y visualizada en un dashboard interactivo.

> Motos y Motores del Norte S.A.S. | 1501 leads normalizados · 1357 grupos
> deduplicados · 657/677 conversaciones extraídas por IA.
> **Demo en vivo:** https://hjmncfb8wdvbs3fbpmkzu8.streamlit.app/

---

## Arquitectura

```
data/entregados/*.csv,*.json
        │  (leads, histórico, conversaciones, catálogo, asesores)
        ▼
  F1  Normalización          (canal, estado, ciudad, fechas, teléfonos, modelo)
        ▼
  F2  Deduplicación          (identidad por teléfono / nombre+ciudad / email)
        ▼
  F3  Enriquecimiento IA     Gemini (con cache `artifacts/extracciones.json`
                             y respaldo determinista por reglas)
        ▼
  F4  Scoring                Regresión logística sobre histórico de cierres
                             → 1.501 leads puntuados, `artifacts/scoring.csv`
        ▼
  F5  Persistencia           Base SQLite `db/motos.db` (5 tablas)
        ▼
  F6  Orquestador            `python run_pipeline.py` (F1→F5, 3.7 s con cache)
        ▼
  F7  Dashboard Streamlit    `app.py` → KPIs, Top priorizado, gráficos, filtros
```

## Métricas medidas

| Métrica | Valor |
|---|---|
| Leads únicos normalizados | 1.501 |
| Grupos de duplicados (identidades) | 1.357 |
| Conversaciones procesadas | 677 (657 por IA, 20 fallback determinista) |
| AUC del modelo (validación) | **0.600** |
| Lift top 20% | **1.53×** |
| Pipeline completo con cache | **3.7 s** |
| Score máximo del Top | 24 |

## Cómo ejecutar

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

python run_pipeline.py        # F1 → F5 completo
streamlit run app.py          # dashboard en http://localhost:8501
```

> Para extracción IA: copia `.env.example` a `.env` y agrega `GEMINI_API_KEY`.
> Sin clave, el pipeline usa el respaldo determinista y el cache incluido.

## Estructura

```
app.py                  Dashboard Streamlit
run_pipeline.py         Orquestador (F1–F5 en un comando)
run_pipeline_0N.py      Ejecutores por fase
pipeline/               lógica (limpieza, duplicados, extraer_ia, scoring, bd)
db/schema.sql           Esquema SQLite versionado
db/motos.db             Base generada (gitignored)
artifacts/              extracciones IA y scoring (versionados)
data/entregados/        Datasets del reto
tests/                  Suite pytest (16 pruebas)
.github/workflows/      CI: pruebas + corrida diaria automatizada
```

## Fases (commits)

| Fase | Commit | Entregable |
|---|---|---|
| F0 | `33c1bf7` | Andamiaje del repo |
| F1 | `9cfc7c1` | Ingesta y normalización |
| F2 | `6491518` | Deduplicación e identidades |
| F3A | `4413d01` | Extracción con respaldo determinista y cache |
| F3 | `d4c847b` | Enriquecimiento con Gemini (657/677 por IA) |
| F4 | `1c9cf64` | Scoring (AUC 0.60, lift 1.53×) |
| F5 | `e1ff272` | Base SQLite central |
| F6 | `4a2fe4e` | Orquestador + CI con corrida diaria |
| F7 | `fb5a8a6` | Dashboard Streamlit |
| F8 | — | Documentación y despliegue |

## Automatización (sustentamiento)

`GitHub Actions` corre las 16 pruebas en cada push y ejecuta el pipeline completo
todos los días (06:05 hora Bogotá), garantizando la regeneración del SCD sin
intervención manual — el modelo se reentrena y los scores se actualizan.