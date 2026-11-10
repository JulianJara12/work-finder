"""Pruebas de la base de datos. Usan una base en memoria, no tocan tu archivo real."""

import os
import sqlite3
import tempfile
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
        db.cambiar_estado(self.conexion, 1, "postule")
        db.guardar_ofertas(self.conexion, [self.oferta])
        guardada = db.listar_ofertas(self.conexion)[0]
        self.assertEqual(guardada["estado"], "postule")
        self.assertEqual(guardada["paises"], ["Colombia"])

    def test_oculta_ofertas_que_ya_no_aparecen(self):
        db.guardar_ofertas(self.conexion, [self.oferta], hoy=date(2026, 11, 1))
        self.assertEqual(len(db.listar_ofertas(self.conexion, hoy=date(2026, 11, 5))), 1)
        self.assertEqual(len(db.listar_ofertas(self.conexion, hoy=date(2026, 11, 20))), 0)

    def test_postuladas_siguen_visibles_aunque_ya_no_aparezcan(self):
        db.guardar_ofertas(self.conexion, [self.oferta], hoy=date(2026, 11, 1))
        db.cambiar_estado(self.conexion, 1, "postule")
        self.assertEqual(len(db.listar_ofertas(self.conexion, hoy=date(2026, 11, 20))), 1)

    def test_descartadas_se_ocultan_salvo_que_las_pidas(self):
        db.guardar_ofertas(self.conexion, [self.oferta])
        self.assertTrue(db.cambiar_estado(self.conexion, 1, "descartada", notas="Muy lejos"))
        self.assertEqual(db.listar_ofertas(self.conexion), [])
        descartadas = db.listar_ofertas(self.conexion, estado="descartada")
        self.assertEqual(descartadas[0]["notas"], "Muy lejos")
        self.assertEqual(db.contar_por_estado(self.conexion), {"descartada": 1})

    def test_numero_inexistente_o_estado_invalido(self):
        self.assertFalse(db.cambiar_estado(self.conexion, 99, "postule"))
        with self.assertRaises(ValueError):
            db.cambiar_estado(self.conexion, 1, "inventado")

    def test_migra_una_base_antigua(self):
        # Creamos un archivo temporal con la tabla antigua (sin las columnas nuevas).
        ruta = os.path.join(tempfile.mkdtemp(), "vieja.db")
        conexion = sqlite3.connect(ruta)
        conexion.executescript(db.ESQUEMA)
        conexion.close()
        conexion = db.conectar(ruta)
        columnas = {f["name"] for f in conexion.execute("PRAGMA table_info(ofertas)")}
        conexion.close()
        self.assertIn("fecha_estado", columnas)
        self.assertIn("notas", columnas)


if __name__ == "__main__":
    unittest.main()
