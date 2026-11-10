"""Pruebas del puntaje de compatibilidad."""

import unittest

import compatibilidad


def oferta(titulo, descripcion, modalidad="Híbrido", publicada="2026-11-01"):
    return {"titulo": titulo, "descripcion": descripcion, "modalidad": modalidad,
            "publicada": publicada}


class PruebasCompatibilidad(unittest.TestCase):
    def test_calcula_porcentaje_y_detalle(self):
        o = compatibilidad.evaluar(oferta("Analista de datos", "SQL, Power BI y Python"),
                                   ["SQL", "Python", "Excel"])
        self.assertEqual(o["puntaje"], 67)  # pide 3 (SQL, Power BI, Python) y tienes 2
        self.assertIn("Power BI", o["faltan"])

    def test_sin_habilidades_conocidas_no_tiene_puntaje(self):
        o = compatibilidad.evaluar(oferta("Practicante", "Buena actitud"), ["SQL"])
        self.assertIsNone(o["puntaje"])

    def test_ordena_y_filtra(self):
        ofertas = [
            oferta("A", "SQL", modalidad="Remoto"),            # 100 %
            oferta("B", "SQL y Docker", modalidad="Híbrido"),  # 50 %
            oferta("C", "Buena actitud", modalidad="Remoto"),  # sin puntaje
        ]
        orden = compatibilidad.ordenar_y_filtrar(ofertas, ["SQL"])
        self.assertEqual([o["titulo"] for o in orden], ["A", "B", "C"])
        remotas = compatibilidad.ordenar_y_filtrar(ofertas, ["SQL"], modalidad="remoto")
        self.assertEqual([o["titulo"] for o in remotas], ["A", "C"])
        buenas = compatibilidad.ordenar_y_filtrar(ofertas, ["SQL"], minimo=60)
        self.assertEqual([o["titulo"] for o in buenas], ["A"])


if __name__ == "__main__":
    unittest.main()
