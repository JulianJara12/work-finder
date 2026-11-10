"""Work Finder: tu buscador de empleo en la terminal.

Uso:
    python workfinder.py cv                 # lee datos/cv.pdf
    python workfinder.py cv --ruta otro.pdf # lee otro archivo
    python workfinder.py cv --texto         # muestra también el texto leído del PDF
    python workfinder.py buscar             # trae ofertas junior de Get on Board
    python workfinder.py buscar --todas     # sin filtrar por nivel ni país
"""

import argparse
import sys
from pathlib import Path

import requests

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


def comando_buscar(args):
    consultas = args.consulta or getonbrd.CONSULTAS
    print(f"Buscando en Get on Board: {', '.join(consultas)}...")
    try:
        ofertas = getonbrd.buscar_ofertas(consultas, solo_relevantes=not args.todas)
    except requests.RequestException as error:
        print(f"No pude conectarme con Get on Board: {error}")
        return 1

    ofertas.sort(key=lambda o: o["publicada"], reverse=True)  # las más nuevas primero
    print(f"Encontré {len(ofertas)} ofertas.\n")
    for oferta in ofertas[: args.limite]:
        paises = ", ".join(oferta["paises"]) or "Sin país"
        print(f"* {oferta['titulo']} | {oferta['empresa']}")
        print(f"  {oferta['nivel']} | {oferta['modalidad']} | {paises} | {oferta['publicada']}")
        print(f"  {oferta['url']}\n")
    if len(ofertas) > args.limite:
        print(f"(Mostrando {args.limite} de {len(ofertas)}. Usa --limite para ver más.)")
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

    args = parser.parse_args()
    return args.funcion(args)


if __name__ == "__main__":
    sys.exit(main())
