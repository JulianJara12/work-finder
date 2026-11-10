"""Funciones que comparten todas las fuentes de ofertas."""

import html
import re

# Nombre con el que nos identificamos ante los portales. Es buena educación decir quién eres.
USER_AGENT = "work-finder/1.0 (proyecto personal de busqueda de empleo)"


def limpiar_html(texto):
    """Quita las etiquetas HTML (<p>, <li>...) y deja solo el texto."""
    sin_etiquetas = re.sub(r"<[^>]+>", " ", texto or "")
    return re.sub(r"\s+", " ", html.unescape(sin_etiquetas)).strip()
