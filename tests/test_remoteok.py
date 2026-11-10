"""Pruebas de la fuente Remote OK, sin conectarse a internet."""

import unittest
from unittest.mock import MagicMock, patch

from fuentes import remoteok


def item_falso(id_, titulo="Junior Data Analyst", ubicacion="", tags=("sql", "python")):
    """Una oferta con la misma forma que devuelve https://remoteok.com/api."""
    return {
        "id": id_, "slug": f"oferta-{id_}", "epoch": 1793708562,
        "date": "2026-11-03T10:00:00+00:00", "company": "Acme", "position": titulo,
        "tags": list(tags), "description": "<p>Work with <b>SQL</b> and dashboards</p>",
        "location": ubicacion, "salary_min": 0, "salary_max": 0,
        "url": f"https://remoteok.com/remote-jobs/oferta-{id_}",
    }


class PruebasRemoteOK(unittest.TestCase):
    def test_convierte_al_formato_propio(self):
        o = remoteok.a_oferta(item_falso("1"))
        self.assertEqual(o["id"], "remoteok:1")
        self.assertEqual(o["nivel"], "Junior")
        self.assertEqual(o["modalidad"], "Remoto")
        self.assertEqual(o["publicada"], "2026-11-03")
        self.assertIsNone(o["salario_min"])  # la API pone 0 cuando no hay dato
        self.assertIn("SQL", o["descripcion"])

    def test_detecta_nivel_por_titulo(self):
        self.assertEqual(remoteok.detectar_nivel("Senior Python Developer"), "Senior")
        self.assertEqual(remoteok.detectar_nivel("Jr. Backend Engineer"), "Junior")
        self.assertEqual(remoteok.detectar_nivel("Data Engineering Intern"), "Junior")
        self.assertEqual(remoteok.detectar_nivel("Python Developer"), "Sin dato")

    def test_filtra_nivel_y_ubicacion(self):
        respuesta = [
            {"legal": "aviso legal, no es una oferta"},
            item_falso("1"),                                   # junior, cualquier país
            item_falso("2", ubicacion="LATAM"),                # junior, LATAM
            item_falso("3", ubicacion="USA only"),             # junior, solo EE. UU.
            item_falso("4", titulo="Senior Data Analyst"),     # senior
        ]
        falsa = MagicMock()
        falsa.json.return_value = respuesta
        with patch.object(remoteok.requests, "get", return_value=falsa):
            ofertas = remoteok.buscar_ofertas()
        self.assertEqual([o["id"] for o in ofertas], ["remoteok:1", "remoteok:2"])


if __name__ == "__main__":
    unittest.main()
