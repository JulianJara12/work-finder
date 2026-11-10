"""Work Finder: tu buscador de empleo en la terminal.

Uso:
    python workfinder.py cv                 # lee datos/cv.pdf
    python workfinder.py cv --ruta otro.pdf # lee otro archivo
    python workfinder.py cv --texto         # muestra también el texto leído del PDF
    python workfinder.py buscar             # trae ofertas junior de Get on Board
    python workfinder.py buscar --todas     # sin filtrar por nivel ni país
    python workfinder.py listar             # muestra las ofertas guardadas, mejores primero
    python workfinder.py listar --minimo 50 --modalidad remoto
"""

import argparse
import sys
from pathlib import Path

import requests

import compatibilidad
import db
from cv import encontrar_habilidades, leer_texto_pdf
from fuentes import getonbrd

RUTA_CV = Path("datos") / "cv.pdf"


def comando_cv(args):
    ruta = Path(args.ruta)
    if not ruta.exists():
        print(f"No encontré el archivo {ruta}. Copia tu CV en esa ruta o usa --ruta.")
        return 1

    texto = leer_texto_pdf(ruta)
    if not texto.strip():
        print("El PDF no tiene texto que se pueda leer (¿es una imagen escaneada?).")
        return 1

    if args.texto:
        print("----- Texto leído del PDF -----")
        print(texto)
        print("-------------------------------")

    habilidades = encontrar_habilidades(texto)
    print(f"Leí {len(texto)} caracteres de {ruta}.")
    print(f"Encontré {len(habilidades)} habilidades:")
    for habilidad in habilidades:
        print(f"  - {habilidad}")
    return 0


def cargar_habilidades_cv(ruta=RUTA_CV):
    """Lee las habilidades de tu CV. Si no hay CV, devuelve una lista vacía y avisa."""
    if not Path(ruta).exists():
        print(f"(No encontré {ruta}: las ofertas se muestran sin puntaje de compatibilidad.)\n")
        return []
    return encontrar_habilidades(leer_texto_pdf(ruta))


def imprimir_ofertas(ofertas, limite):
    """Muestra una lista de ofertas en la terminal."""
    for oferta in ofertas[:limite]:
        paises = ", ".join(oferta["paises"]) or "Sin país"
        puntaje = oferta.get("puntaje")
        etiqueta = f"[{puntaje:3d}%]" if puntaje is not None else "[  ? ]"
        print(f"{etiqueta} {oferta['titulo']} | {oferta['empresa']}")
        print(f"       {oferta['nivel']} | {oferta['modalidad']} | {paises} | {oferta['publicada']}")
        if oferta.get("coinciden"):
            print(f"       Tienes: {', '.join(oferta['coinciden'])}")
        if oferta.get("faltan"):
            print(f"       Te falta: {', '.join(oferta['faltan'])}")
        print(f"       {oferta['url']}\n")
    if len(ofertas) > limite:
        print(f"(Mostrando {limite} de {len(ofertas)}. Usa --limite para ver más.)")


def comando_buscar(args):
    consultas = args.consulta or getonbrd.CONSULTAS
    print(f"Buscando en Get on Board: {', '.join(consultas)}...")
    try:
        ofertas = getonbrd.buscar_ofertas(consultas, solo_relevantes=not args.todas)
    except requests.RequestException as error:
        print(f"No pude conectarme con Get on Board: {error}")
        return 1

    conexion = db.conectar()
    ids_nuevas = db.guardar_ofertas(conexion, ofertas)
    conexion.close()

    print(f"Encontré {len(ofertas)} ofertas; {len(ids_nuevas)} son nuevas.\n")
    nuevas = [o for o in ofertas if o["id"] in ids_nuevas]
    if not nuevas:
        print("No hay ofertas nuevas desde tu última búsqueda. Usa 'listar' para ver todas.")
        return 0
    nuevas = compatibilidad.ordenar_y_filtrar(nuevas, cargar_habilidades_cv())
    imprimir_ofertas(nuevas, args.limite)
    return 0


def comando_listar(args):
    conexion = db.conectar()
    ofertas = db.listar_ofertas(conexion, dias_vigencia=args.dias)
    conexion.close()

    ofertas = compatibilidad.ordenar_y_filtrar(
        ofertas, cargar_habilidades_cv(), minimo=args.minimo, modalidad=args.modalidad)
    print(f"Tienes {len(ofertas)} ofertas vigentes que cumplen los filtros.\n")
    imprimir_ofertas(ofertas, args.limite)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Tu buscador de empleo en la terminal.")
    subcomandos = parser.add_subparsers(dest="comando", required=True)

    parser_cv = subcomandos.add_parser("cv", help="Lee tu CV y muestra tus habilidades")
    parser_cv.add_argument("--ruta", default=str(RUTA_CV), help="Ruta al PDF de tu CV")
    parser_cv.add_argument("--texto", action="store_true",
                           help="Muestra el texto que se pudo leer del PDF")
    parser_cv.set_defaults(funcion=comando_cv)

    parser_buscar = subcomandos.add_parser("buscar", help="Busca ofertas en Get on Board")
    parser_buscar.add_argument("--consulta", action="append",
                               help="Palabra a buscar (puedes repetirla varias veces)")
    parser_buscar.add_argument("--todas", action="store_true",
                               help="No filtrar por nivel junior ni por país")
    parser_buscar.add_argument("--limite", type=int, default=20,
                               help="Cuántas ofertas mostrar (por defecto 20)")
    parser_buscar.set_defaults(funcion=comando_buscar)

    parser_listar = subcomandos.add_parser("listar", help="Muestra las ofertas guardadas")
    parser_listar.add_argument("--dias", type=int, default=7,
                               help="Solo ofertas vistas en los últimos N días (por defecto 7)")
    parser_listar.add_argument("--limite", type=int, default=50,
                               help="Cuántas ofertas mostrar (por defecto 50)")
    parser_listar.add_argument("--minimo", type=int, default=0,
                               help="Solo ofertas con al menos este %% de compatibilidad")
    parser_listar.add_argument("--modalidad", choices=sorted(compatibilidad.MODALIDADES_FILTRO),
                               help="Filtra por remoto, hibrido o presencial")
    parser_listar.set_defaults(funcion=comando_listar)

    args = parser.parse_args()
    return args.funcion(args)


if __name__ == "__main__":
    sys.exit(main())
