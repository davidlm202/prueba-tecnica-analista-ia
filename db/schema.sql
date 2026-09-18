-- Esquema versionado de la base de datos (SQLite) - Fase 5.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS leads (
    lead_id        TEXT PRIMARY KEY,
    nombre_cliente TEXT,
    telefono_norm  TEXT,
    email          TEXT,
    ciudad_norm    TEXT,
    departamento   TEXT,
    empresa_id     TEXT,
    punto_venta_id TEXT,
    canal_norm     TEXT,
    estado_norm    TEXT,
    fecha_registro TEXT,
    horas_al_contacto REAL,
    sku_matcheado  TEXT,
    score_match    INTEGER,
    precio_lista   INTEGER,
    grupo_id       TEXT,
    es_maestro     INTEGER,
    nombre_norm    TEXT
);

CREATE TABLE IF NOT EXISTS identidades (
    grupo_id   TEXT NOT NULL,
    lead_id    TEXT NOT NULL,
    es_maestro INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS extracciones_ia (
    conversacion_id TEXT PRIMARY KEY,
    lead_id         TEXT NOT NULL,
    origen          TEXT,
    presupuesto     INTEGER,
    modelo          TEXT,
    cilindraje      INTEGER,
    fecha_cita      TEXT,
    cuota_inicial   INTEGER,
    cuota_mensual   INTEGER,
    uso             TEXT,
    negociable      INTEGER
);

CREATE TABLE IF NOT EXISTS scores (
    lead_id      TEXT PRIMARY KEY,
    score        INTEGER,
    motivos      TEXT,
    horas        REAL,
    contactos    REAL,
    precio_lista INTEGER,
    pidio_cita   INTEGER,
    manifesto_cuota INTEGER,
    pago_credito INTEGER,
    origen       TEXT
);

CREATE TABLE IF NOT EXISTS metadatos (
    clave TEXT PRIMARY KEY,
    valor TEXT
);