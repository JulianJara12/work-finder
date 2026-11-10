"""Pruebas de la base de datos. Usan una base en memoria, no tocan tu archivo real."""

import unittest
from datetime import date

import db
from fuentes import getonbrd
from tests.test_getonbrd import item_falso


class PruebasBaseDeDatos(unittest.TestCase):
    def setUp(self):
        self.conexion = db.conectar(":memory:")  # base temporal que desaparece al terminar
        self.oferta = getonbrd.a_oferta(item_falso("analista-acme"))

    def tearDown(self):
        self.conexion.close()

    def test_guarda_y_no_duplica(self):
        self.assertEqual(db.guardar_ofertas(self.conexion, [self.oferta]), {"getonbrd:analista-acme"})
        self.assertEqual(db.guardar_ofertas(self.conexion, [self.oferta]), set())
        self.assertEqual(len(db.listar_ofertas(self.conexion)), 1)

    def test_conserva_el_estado_al_actualizar(self):
        db.guardar_ofertas(self.conexion, [self.oferta])
        self.conexion.execute("UPDATE ofertas SET estado = 'postulé'")
        db.guardar_ofertas(self.conexion, [self.oferta])
        guardada = db.listar_ofertas(self.conexion)[0]
        self.assertEqual(guardada["estado"], "postulé")
        self.assertEqual(guardada["paises"], ["Colombia"])

    def test_oculta_ofertas_que_ya_no_aparecen(self):
        db.guardar_ofertas(self.conexion, [self.oferta], hoy=date(2026, 11, 1))
        self.assertEqual(len(db.listar_ofertas(self.conexion, hoy=date(2026, 11, 5))), 1)
        self.assertEqual(len(db.listar_ofertas(self.conexion, hoy=date(2026, 11, 20))), 0)


if __name__ == "__main__":
    unittest.main()
