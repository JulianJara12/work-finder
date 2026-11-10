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
    estado       TEXT NOT NULL DEFAULT 'nueva'  -- ver ESTADOS más abajo
);
"""

# Columnas que se agregaron después de la primera versión. Si tu base de datos es
# antigua, conectar() las añade sin borrar nada (esto se llama una "migración").
COLUMNAS_NUEVAS = {
    "fecha_estado": "TEXT",  # día en que cambiaste el estado por última vez
    "notas": "TEXT",         # tus apuntes sobre la oferta
}

# Estados posibles de una oferta, en el orden en que suele avanzar una postulación.
ESTADOS = ["nueva", "interesa", "postule", "entrevista", "oferta", "rechazada", "descartada"]
ESTADOS_OCULTOS = {"rechazada", "descartada"}  # no se muestran en "listar" salvo que los pidas


def conectar(ruta=RUTA_DB):
    """Abre (o crea) la base de datos y se asegura de que exista la tabla."""
    if str(ruta) != ":memory:":
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(ruta)
    conexion.row_factory = sqlite3.Row  # permite leer columnas por nombre: fila["titulo"]
    conexion.executescript(ESQUEMA)
    existentes = {fila["name"] for fila in conexion.execute("PRAGMA table_info(ofertas)")}
    for columna, tipo in COLUMNAS_NUEVAS.items():
        if columna not in existentes:
            conexion.execute(f"ALTER TABLE ofertas ADD COLUMN {columna} {tipo}")
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
    la retiraron y deja de mostrarse (pero sigue guardada). Las ofertas en las
    que ya avanzaste (postulé, entrevista...) se muestran siempre.
    Sin `estado`, se ocultan las rechazadas y descartadas.
    """
    desde = ((hoy or date.today()) - timedelta(days=dias_vigencia)).isoformat()
    # "rowid" es un número que SQLite le da a cada fila: lo usamos como número corto (#12).
    consulta = """SELECT rowid AS num, * FROM ofertas
                  WHERE (ultima_vez >= ? OR estado NOT IN ('nueva', 'interesa'))"""
    parametros = [desde]
    if estado:
        consulta += " AND estado = ?"
        parametros.append(estado)
    else:
        consulta += f" AND estado NOT IN ({', '.join('?' for _ in ESTADOS_OCULTOS)})"
        parametros.extend(sorted(ESTADOS_OCULTOS))
    consulta += " ORDER BY publicada DESC"
    filas = conexion.execute(consulta, parametros).fetchall()
    return [fila_a_oferta(f) for f in filas]


def obtener_ofertas(conexion, ids):
    """Devuelve las ofertas con esos ids (los largos, como "getonbrd:...")."""
    if not ids:
        return []
    marcas = ", ".join("?" for _ in ids)
    filas = conexion.execute(f"SELECT rowid AS num, * FROM ofertas WHERE id IN ({marcas})",
                             list(ids)).fetchall()
    return [fila_a_oferta(f) for f in filas]


def obtener_oferta(conexion, num):
    """Devuelve una oferta por su número corto, o None si no existe."""
    fila = conexion.execute("SELECT rowid AS num, * FROM ofertas WHERE rowid = ?", (num,)).fetchone()
    return fila_a_oferta(fila) if fila else None


def cambiar_estado(conexion, num, estado, notas=None, hoy=None):
    """Cambia el estado de una oferta. Devuelve False si el número no existe."""
    if estado not in ESTADOS:
        raise ValueError(f"Estado no válido: {estado}. Usa uno de: {', '.join(ESTADOS)}")
    cursor = conexion.execute(
        "UPDATE ofertas SET estado = ?, fecha_estado = ?, notas = COALESCE(?, notas) WHERE rowid = ?",
        (estado, (hoy or date.today()).isoformat(), notas, num),
    )
    conexion.commit()
    return cursor.rowcount == 1


def contar_por_estado(conexion):
    """Devuelve {estado: cantidad} con todas las ofertas guardadas."""
    filas = conexion.execute("SELECT estado, COUNT(*) AS total FROM ofertas GROUP BY estado")
    return {fila["estado"]: fila["total"] for fila in filas}


def fila_a_oferta(fila):
    """Convierte una fila de la base de datos en el mismo diccionario que usan las fuentes."""
    oferta = dict(fila)
    oferta["paises"] = json.loads(oferta["paises"] or "[]")
    return oferta
