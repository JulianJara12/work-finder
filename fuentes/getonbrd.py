"""Fuente: Get on Board (https://www.getonbrd.com), portal de empleos tech en Latinoamérica.

Usa su API pública (no necesita clave). Documentación: https://api-doc.getonbrd.com/
"""

import html
import re
from datetime import datetime, timezone

import requests

URL_BUSQUEDA = "https://www.getonbrd.com/api/v0/search/jobs"

# Palabras con las que buscamos. Cada una es una búsqueda distinta en el portal.
CONSULTAS = ["junior", "datos", "sql", "python", "desarrollador", "analista", "base de datos"]

SENIORITIES = {1: "Sin experiencia", 2: "Junior", 3: "Semi Senior", 4: "Senior", 5: "Experto"}
NIVELES_ACEPTADOS = {"Sin experiencia", "Junior"}

MODALIDADES = {
    "fully_remote": "Remoto",
    "remote_local": "Remoto (solo en el país)",
    "hybrid": "Híbrido",
    "no_remote": "Presencial",
}


def pedir_pagina(consulta, pagina=1, por_pagina=50):
    """Hace UNA petición a la API y devuelve la respuesta como diccionario."""
    parametros = {
        "query": consulta,
        "page": pagina,
        "per_page": por_pagina,
        "expand": '["company"]',  # para que incluya el nombre de la empresa
    }
    respuesta = requests.get(URL_BUSQUEDA, params=parametros, timeout=20)
    respuesta.raise_for_status()  # lanza un error si el servidor respondió mal (404, 500...)
    return respuesta.json()


def limpiar_html(texto):
    """Quita las etiquetas HTML (<p>, <li>...) y deja solo el texto."""
    sin_etiquetas = re.sub(r"<[^>]+>", " ", texto or "")
    return re.sub(r"\s+", " ", html.unescape(sin_etiquetas)).strip()


def a_oferta(item):
    """Convierte un trabajo tal como lo entrega la API en nuestro formato propio.

    Así, cuando sumemos otros portales, todas las ofertas tendrán los mismos campos.
    """
    a = item["attributes"]
    empresa = a.get("company", {}).get("data", {}).get("attributes", {}).get("name", "")
    id_seniority = a.get("seniority", {}).get("data", {}).get("id")
    publicada = a.get("published_at")

    descripcion = " ".join(
        limpiar_html(a.get(campo)) for campo in ("description", "functions", "desirable", "projects")
    )

    return {
        "id": f"getonbrd:{item['id']}",
        "fuente": "Get on Board",
        "titulo": a.get("title", ""),
        "empresa": empresa,
        "url": item.get("links", {}).get("public_url", ""),
        "paises": a.get("countries") or [],
        "modalidad": MODALIDADES.get(a.get("remote_modality"), "Sin dato"),
        "nivel": SENIORITIES.get(int(id_seniority), "Sin dato") if id_seniority else "Sin dato",
        "publicada": (datetime.fromtimestamp(publicada, tz=timezone.utc).date().isoformat()
                      if publicada else ""),
        "salario_min": a.get("min_salary"),
        "salario_max": a.get("max_salary"),
        "descripcion": descripcion.strip(),
    }


def es_relevante(oferta, pais="Colombia"):
    """True si la oferta es para tu nivel y la puedes tomar desde Colombia."""
    if oferta["nivel"] not in NIVELES_ACEPTADOS:
        return False
    return pais in oferta["paises"] or oferta["modalidad"] == "Remoto"


def buscar_ofertas(consultas=CONSULTAS, paginas=2, solo_relevantes=True):
    """Busca con cada consulta, junta los resultados y quita los repetidos."""
    ofertas = {}  # usamos el id como clave para no repetir ofertas
    for consulta in consultas:
        for pagina in range(1, paginas + 1):
            respuesta = pedir_pagina(consulta, pagina)
            for item in respuesta.get("data", []):
                oferta = a_oferta(item)
                ofertas[oferta["id"]] = oferta
            if pagina >= respuesta.get("meta", {}).get("total_pages", 1):
                break  # no hay más páginas para esta consulta

    resultado = list(ofertas.values())
    if solo_relevantes:
        resultado = [o for o in resultado if es_relevante(o)]
    return resultado
