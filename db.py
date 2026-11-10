"""Base de datos SQLite donde se guardan las ofertas entre una búsqueda y otra.

Todo queda en un solo archivo: datos/workfinder.db (Git lo ignora).
Puedes abrirlo con "DB Browser for SQLite" para verlo como tabla.
"""

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

RUTA_DB = Path("datos") / "workfinder.db"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS ofertas (
    id           TEXT PRIMARY KEY,   -- ej. "getonbrd:analista-datos-acme"
    fuente       TEXT NOT NULL,
    titulo       TEXT NOT NULL,
    empresa      TEXT,
    url          TEXT,
    paises       TEXT,               -- lista guardada como JSON: ["Colombia"]
    modalidad    TEXT,
    nivel        TEXT,
    publicada    TEXT,               -- fecha AAAA-MM-DD
    salario_min  INTEGER,
    salario_max  INTEGER,
    descripcion  TEXT,
    primera_vez  TEXT NOT NULL,      -- día en que la encontramos por primera vez
    ultima_vez   TEXT NOT NULL,      -- último día en que seguía publicada
    estado       TEXT NOT NULL DEFAULT 'nueva'  -- nueva, postulé, descartada...
);
"""


def conectar(ruta=RUTA_DB):
    """Abre (o crea) la base de datos y se asegura de que exista la tabla."""
    if str(ruta) != ":memory:":
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(ruta)
    conexion.row_factory = sqlite3.Row  # permite leer columnas por nombre: fila["titulo"]
    conexion.executescript(ESQUEMA)
    return conexion


def guardar_ofertas(conexion, ofertas, hoy=None):
    """Guarda las ofertas. Devuelve el conjunto de ids de las que eran nuevas.

    Si una oferta ya existía, solo actualiza sus datos y la fecha "ultima_vez",
    sin tocar su estado (así no pierdes lo que marcaste).
    """
    hoy = (hoy or date.today()).isoformat()
    nuevas = set()
    for o in ofertas:
        existe = conexion.execute("SELECT 1 FROM ofertas WHERE id = ?", (o["id"],)).fetchone()
        if existe:
            conexion.execute(
                """UPDATE ofertas SET titulo = ?, empresa = ?, url = ?, paises = ?, modalidad = ?,
                       nivel = ?, publicada = ?, salario_min = ?, salario_max = ?,
                       descripcion = ?, ultima_vez = ?
                   WHERE id = ?""",
                (o["titulo"], o["empresa"], o["url"], json.dumps(o["paises"]), o["modalidad"],
                 o["nivel"], o["publicada"], o["salario_min"], o["salario_max"],
                 o["descripcion"], hoy, o["id"]),
            )
        else:
            conexion.execute(
                """INSERT INTO ofertas (id, fuente, titulo, empresa, url, paises, modalidad, nivel,
                       publicada, salario_min, salario_max, descripcion, primera_vez, ultima_vez)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (o["id"], o["fuente"], o["titulo"], o["empresa"], o["url"], json.dumps(o["paises"]),
                 o["modalidad"], o["nivel"], o["publicada"], o["salario_min"], o["salario_max"],
                 o["descripcion"], hoy, hoy),
            )
            nuevas.add(o["id"])
    conexion.commit()
    return nuevas


def listar_ofertas(conexion, dias_vigencia=7, estado=None, hoy=None):
    """Devuelve las ofertas vistas en los últimos `dias_vigencia` días.

    Si una oferta no aparece en las búsquedas durante una semana, asumimos que
    la retiraron y deja de mostrarse (pero sigue guardada).
    """
    desde = ((hoy or date.today()) - timedelta(days=dias_vigencia)).isoformat()
    consulta = "SELECT * FROM ofertas WHERE ultima_vez >= ?"
    parametros = [desde]
    if estado:
        consulta += " AND estado = ?"
        parametros.append(estado)
    consulta += " ORDER BY publicada DESC"
    filas = conexion.execute(consulta, parametros).fetchall()
    return [fila_a_oferta(f) for f in filas]


def fila_a_oferta(fila):
    """Convierte una fila de la base de datos en el mismo diccionario que usan las fuentes."""
    oferta = dict(fila)
    oferta["paises"] = json.loads(oferta["paises"] or "[]")
    return oferta
