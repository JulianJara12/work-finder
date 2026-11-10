"""Funciones para leer tu CV en PDF y encontrar tus habilidades."""

import re
import unicodedata

from pypdf import PdfReader

from habilidades import HABILIDADES


def leer_texto_pdf(ruta):
    """Devuelve todo el texto de un PDF como un solo string."""
    lector = PdfReader(ruta)
    paginas = [pagina.extract_text() or "" for pagina in lector.pages]
    return "\n".join(paginas)


def normalizar(texto):
    """Pasa el texto a minúsculas y le quita las tildes ("Estadística" -> "estadistica")."""
    texto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(letra for letra in texto if not unicodedata.combining(letra))


def contiene_palabra(texto, palabra):
    """True si `palabra` aparece en `texto` como palabra completa.

    Así "java" no coincide dentro de "javascript" ni "sql" dentro de "mysql".
    """
    patron = r"(?<![a-z0-9])" + re.escape(palabra) + r"(?![a-z0-9])"
    return re.search(patron, texto) is not None


def encontrar_habilidades(texto, habilidades=HABILIDADES):
    """Devuelve la lista de habilidades (nombres bonitos) que aparecen en el texto."""
    texto = normalizar(texto)
    encontradas = []
    for nombre, palabras in habilidades.items():
        if any(contiene_palabra(texto, palabra) for palabra in palabras):
            encontradas.append(nombre)
    return encontradas
