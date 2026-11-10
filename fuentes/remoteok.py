"""Fuente: Remote OK (https://remoteok.com), ofertas 100 % remotas de todo el mundo.

Usa su API pública: https://remoteok.com/api (devuelve las ofertas más recientes).
Condición de uso de la API: mencionar a Remote OK como fuente y enlazar a la oferta
en su sitio. Por eso cada oferta guarda su enlace de remoteok.com y su fuente.
Las ofertas suelen estar en inglés.
"""

import re

import requests

from cv import normalizar
from fuentes.comun import USER_AGENT, limpiar_html

NOMBRE = "Remote OK"
URL_API = "https://remoteok.com/api"

# Remote OK no tiene un campo de nivel, así que lo deducimos del título.
PALABRAS_JUNIOR = ["junior", "jr", "entry level", "entry-level", "intern", "internship",
                   "trainee", "graduate", "practicante", "aprendiz"]
PALABRAS_SENIOR = ["senior", "sr", "lead", "staff", "principal", "head", "director",
                   "manager", "architect", "vp"]

# Ubicaciones desde las que se puede trabajar estando en Colombia.
# Si la oferta no dice ubicación, asumimos que es para cualquier país.
UBICACIONES_OK = ["worldwide", "anywhere", "global", "remote", "latam", "latin america",
                  "south america", "americas", "colombia", "bogota"]


def pedir_ofertas():
    """Hace la petición a la API y devuelve la lista de ofertas tal cual llega."""
    respuesta = requests.get(URL_API, timeout=20, headers={"User-Agent": USER_AGENT})
    respuesta.raise_for_status()
    # El primer elemento de la lista es un aviso legal, no una oferta: lo saltamos.
    return [item for item in respuesta.json() if item.get("id") and item.get("position")]


def tiene_palabra(texto, palabras):
    """True si alguna de las palabras aparece como palabra completa en el texto."""
    texto = normalizar(texto)
    return any(re.search(r"(?<![a-z0-9])" + re.escape(p) + r"(?![a-z0-9])", texto)
               for p in palabras)


def detectar_nivel(titulo):
    if tiene_palabra(titulo, PALABRAS_SENIOR):
        return "Senior"
    if tiene_palabra(titulo, PALABRAS_JUNIOR):
        return "Junior"
    return "Sin dato"


def a_oferta(item):
    """Convierte una oferta de Remote OK en nuestro formato propio."""
    ubicacion = (item.get("location") or "").strip()
    etiquetas = item.get("tags") or []
    return {
        "id": f"remoteok:{item['id']}",
        "fuente": NOMBRE,
        "titulo": item.get("position", ""),
        "empresa": item.get("company", ""),
        "url": item.get("url", ""),
        "paises": [ubicacion] if ubicacion else ["Cualquier país"],
        "modalidad": "Remoto",
        "nivel": detectar_nivel(item.get("position", "")),
        "publicada": (item.get("date") or "")[:10],  # "2026-11-10T08:00:00+00:00" -> "2026-11-10"
        "salario_min": item.get("salary_min") or None,  # la API pone 0 cuando no hay dato
        "salario_max": item.get("salary_max") or None,
        "descripcion": f"{limpiar_html(item.get('description'))} {' '.join(etiquetas)}".strip(),
    }


def es_relevante(oferta):
    """True si la oferta es junior y se puede tomar desde Colombia."""
    if oferta["nivel"] != "Junior":
        return False
    ubicacion = " ".join(oferta["paises"])
    return ubicacion == "Cualquier país" or tiene_palabra(ubicacion, UBICACIONES_OK)


def buscar_ofertas(consultas=None, solo_relevantes=True):
    """Trae las ofertas recientes. Si hay consultas, deja solo las que mencionan alguna."""
    ofertas = [a_oferta(item) for item in pedir_ofertas()]
    if consultas:
        palabras = [normalizar(c) for c in consultas]
        ofertas = [o for o in ofertas if tiene_palabra(f"{o['titulo']} {o['descripcion']}", palabras)]
    if solo_relevantes:
        ofertas = [o for o in ofertas if es_relevante(o)]
    return ofertas
