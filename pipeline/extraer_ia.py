"""Enriquecimiento de conversaciones con IA (Fase 3): proveedor configurable, fallback deterministico y cache."""
import re
import json
from pathlib import Path

import httpx

RAIZ = Path(__file__).resolve().parent.parent
RUTA_CACHE = RAIZ / "artifacts" / "extracciones.json"

CAMPOS = ["presupuesto", "modelo", "cilindraje", "fecha_cita",
          "cuota_inicial", "cuota_mensual", "uso", "negociable"]

PROMPT = """Eres un analizador de chats de una concesionaria de motos.
Extrae de esta conversacion solo estos datos en JSON valido (sin markdown):
- presupuesto: cuanto quiere gastar el cliente (numero en pesos, sin simbolos) o null
- modelo: modelo de moto mencionado (marca + nombre) o null
- cilindraje: cilindrada en cc (numero) o null
- fecha_cita: fecha agendada (YYYY-MM-DD) o null
- cuota_inicial: cuota inicial en pesos (numero) o null
- cuota_mensual: cuota mensual en pesos (numero) o null
- uso: "particular", "trabajo", "app" o "negocio" o null
- negociable: true/false o null
Responde SOLO con el JSON.
CONVERSACION:
{conversacion}"""


def cargar_config():
    """Lee .env sin dependencias externas. Devuelve dict con las llaves."""
    cfg = {"LLM_PROVIDER": "NINGUNO"}
    ruta_env = RAIZ / ".env"
    if ruta_env.exists():
        for linea in ruta_env.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, v = linea.split("=", 1)
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


def convertir_numero(valor):
    """9 millones / 9.000.000 / '200' -> 9000000 / 9000000 / 200"""
    if valor is None:
        return None
    t = str(valor).lower().replace(" ", "")
    if "millon" in t:
        num = re.sub(r"[^\d.,]", "", t.split("millon")[0])
        num = num.replace(".", "").replace(",", "")
        try:
            return int(num) * 1000000
        except ValueError:
            return None
    t = t.replace("$", "").replace("pesos", "").strip()
    if not re.search(r"\d", t):
        return None
    t = re.sub(r"[^\d.,]", "", t)
    t = t.replace(".", "").replace(",", "")
    try:
        return int(t)
    except ValueError:
        return None


def monto_cercano(texto, claves, radio=80):
    """Primer monto despues de alguna clave. '2 millones' -> 2000000."""
    t = texto.lower()
    idx = len(t)
    for c in claves:
        i = t.find(c)
        if i != -1 and i < idx:
            idx = i
    if idx == len(t):
        return None
    m = re.search(r"(\d[\d.,]*)\s*(millones?)?", t[idx:idx + radio])
    if not m:
        return None
    val = int(m.group(1).replace(".", "").replace(",", ""))
    if m.group(2):
        val *= 1000000
    return val


def fallback_determinista(texto):
    """Reglas simples cuando no hay API disponible. Uso rapido sin IA."""
    datos = {c: None for c in CAMPOS}
    t = texto.lower()

    datos["presupuesto"] = monto_cercano(
        texto, ["presupuesto", "cuento con", "tengo pensado", "tengo en mente", "tengo disponible"])

    m = re.search(r"\b((?:[A-Z]{2,}[A-Za-z0-9]*|[A-Z][a-z]+)"
                  r"(?:\s+(?:[A-Z]{2,}[A-Za-z0-9]*|[A-Z][a-z]+)){1,2})", texto)
    if m:
        modelo = m.group(1)
        resto = re.match(r"\s+(\d+)", texto[m.end():m.end() + 6])
        if resto:
            modelo += " " + resto.group(1)
        datos["modelo"] = modelo.title()

    m = re.search(r"(\d{3})\s*cc", t)
    if m:
        datos["cilindraje"] = int(m.group(1))

    m = re.search(r"\b(cita|agend\w*|program\w*|visita)\b[\s\S]{0,50}?(\d{4}-\d{2}-\d{2})", t)
    if m:
        datos["fecha_cita"] = m.group(2)

    datos["cuota_inicial"] = monto_cercano(texto, ["cuota inicial", "cuota de entrada", "de inicial"])
    datos["cuota_mensual"] = monto_cercano(texto, ["cuota mensual", "cuota de", "mensualidad"])

    if re.search(r"\b(app|uber|didi|rappi|mensajer[oa])\b", t):
        datos["uso"] = "app"
    elif re.search(r"\b(trabajo|negocio|trabajando)\b", t):
        datos["uso"] = "trabajo"

    if re.search(r"\bnegocian?d?o\b", t) or re.search(r"se\s+puede.+precio", t):
        datos["negociable"] = True
    return datos

def parsear_json(texto):
    """Limpia marca ```json y devuelve dict, o None."""
    t = texto.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t).rstrip("`").strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    inicio, fin = t.find("{"), t.rfind("}")
    if inicio == -1 or fin == -1:
        return None
    try:
        return json.loads(t[inicio:fin + 1])
    except json.JSONDecodeError:
        return None


def llamar_gemini(texto, cfg):
    from google import genai
    cliente = genai.Client(api_key=cfg.get("GEMINI_API_KEY"))
    resp = cliente.models.generate_content(
        model=cfg.get("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=PROMPT.format(conversacion=texto[:4000]),
    )
    return resp.text


def llamar_compatible(texto, cfg):
    """GROQ / CEREBRAS / OPENROUTER: mismas rutas estilo OpenAI."""
    clave = cfg.get("GROQ_API_KEY") or cfg.get("CEREBRAS_API_KEY") or cfg.get("OPENROUTER_API_KEY")
    modelo = "llama-3.3-70b-versatile"
    url = "https://api.groq.com/openai/v1/chat/completions"
    if cfg.get("CEREBRAS_API_KEY"):
        url = "https://api.cerebras.ai/v1/chat/completions"
        modelo = cfg.get("CEREBRAS_MODEL", "llama3.1-8b")
    elif cfg.get("OPENROUTER_API_KEY"):
        url = "https://openrouter.ai/api/v1/chat/completions"
        modelo = cfg.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")
    r = httpx.post(url, headers={"Authorization": f"Bearer {clave}"},
                   json={"model": modelo, "messages": [{"role": "user", "content": PROMPT.format(conversacion=texto[:4000])}],
                         "temperature": 0}, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def extraer_info_conversacion(texto, cfg):
    """Devuelve (datos, origen) con 'origen' en ia | fallback. Nunca lanza excepcion."""
    proveedor = cfg.get("LLM_PROVIDER", "NINGUNO").upper()
    try:
        if proveedor == "GEMINI":
            datos = parsear_json(llamar_gemini(texto, cfg))
        elif proveedor in ("GROQ", "CEREBRAS", "OPENROUTER"):
            datos = parsear_json(llamar_compatible(texto, cfg))
        else:
            data_opts = {"presupuesto": 0}
            return fallback_determinista(texto), "fallback"
        if datos:
            for c in CAMPOS:
                valores = {str(k).lower().strip(): v for k, v in datos.items()}
            return {c: valores.get(c) for c in CAMPOS}, "ia"
    except Exception:
        pass
    return fallback_determinista(texto), "fallback"


def cargar_cache():
    if RUTA_CACHE.exists():
        return json.loads(RUTA_CACHE.read_text(encoding="utf-8"))
    return {}


def guardar_cache(datos):
    RUTA_CACHE.parent.mkdir(parents=True, exist_ok=True)
    RUTA_CACHE.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")