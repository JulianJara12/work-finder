"""Pruebas de la fuente Get on Board, sin conectarse a internet.

Ejecútalas con:  python -m unittest
"""

import unittest
from unittest.mock import patch

from fuentes import getonbrd


def item_falso(slug, seniority=2, paises=("Colombia",), modalidad="hybrid"):
    """Un trabajo con la misma forma que devuelve la API real."""
    return {
        "id": slug,
        "type": "job",
        "attributes": {
            "title": "Analista de Datos Junior",
            "description": "<p>Buscamos persona con <strong>SQL</strong> y Power&nbsp;BI</p>",
            "functions": "<ul><li>Crear dashboards</li></ul>",
            "desirable": "",
            "projects": "",
            "remote_modality": modalidad,
            "countries": list(paises),
            "min_salary": None,
            "max_salary": None,
            "published_at": 1793708562,
            "seniority": {"data": {"id": seniority, "type": "seniority"}},
            "company": {"data": {"id": "acme", "type": "company",
                                 "attributes": {"name": "Acme"}}},
        },
        "links": {"public_url": f"https://www.getonbrd.com/jobs/{slug}"},
    }


class PruebasGetOnBoard(unittest.TestCase):
    def test_convierte_al_formato_propio(self):
        oferta = getonbrd.a_oferta(item_falso("analista-acme"))
        self.assertEqual(oferta["id"], "getonbrd:analista-acme")
        self.assertEqual(oferta["empresa"], "Acme")
        self.assertEqual(oferta["nivel"], "Junior")
        self.assertEqual(oferta["modalidad"], "Híbrido")
        self.assertIn("SQL y Power BI", oferta["descripcion"])
        self.assertNotIn("<p>", oferta["descripcion"])

    def test_filtra_por_nivel_y_pais(self):
        junior_colombia = getonbrd.a_oferta(item_falso("a"))
        senior = getonbrd.a_oferta(item_falso("b", seniority=4))
        chile_presencial = getonbrd.a_oferta(item_falso("c", paises=["Chile"], modalidad="no_remote"))
        remoto_chile = getonbrd.a_oferta(item_falso("d", paises=["Chile"], modalidad="fully_remote"))
        self.assertTrue(getonbrd.es_relevante(junior_colombia))
        self.assertFalse(getonbrd.es_relevante(senior))
        self.assertFalse(getonbrd.es_relevante(chile_presencial))
        self.assertTrue(getonbrd.es_relevante(remoto_chile))

    def test_quita_repetidos_entre_consultas(self):
        respuesta = {"data": [item_falso("a"), item_falso("b")], "meta": {"total_pages": 1}}
        with patch.object(getonbrd, "pedir_pagina", return_value=respuesta):
            ofertas = getonbrd.buscar_ofertas(["sql", "python"])
        self.assertEqual(len(ofertas), 2)


if __name__ == "__main__":
    unittest.main()
