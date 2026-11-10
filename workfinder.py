"""Work Finder: tu buscador de empleo en la terminal.

Uso:
    python workfinder.py cv                 # lee datos/cv.pdf
    python workfinder.py cv --ruta otro.pdf # lee otro archivo
    python workfinder.py cv --texto         # muestra también el texto leído del PDF
    python workfinder.py buscar             # trae ofertas junior de todas las fuentes
    python workfinder.py buscar --fuente remoteok
    python workfinder.py buscar --todas     # sin filtrar por nivel ni país
    python workfinder.py listar             # muestra las ofertas guardadas, mejores primero
    python workfinder.py listar --minimo 50 --modalidad remoto
    python workfinder.py listar --estado postule
    python workfinder.py ver 12             # detalle completo de la oferta #12
    python workfinder.py marcar 12 postule  # cambia el estado de la oferta #12
    python workfinder.py resumen            # cuántas ofertas tienes en cada estado
"""

import argparse
import sys
from pathlib import Path

import requests

import compatibilidad
import db
from cv import encontrar_habilidades, leer_texto_pdf
from fuentes import getonbrd, remoteok

# Todas las fuentes de ofertas. Para sumar un portal nuevo, crea su módulo en fuentes/
# con NOMBRE y buscar_ofertas(consultas, solo_relevantes) y agrégalo aquí.
FUENTES = {"getonbrd": getonbrd, "remoteok": remoteok}

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
        estado = f" ({oferta['estado']})" if oferta.get("estado", "nueva") != "nueva" else ""
        print(f"{etiqueta} #{oferta.get('num', '?')} {oferta['titulo']} | {oferta['empresa']}{estado}")
        print(f"       {oferta['nivel']} | {oferta['modalidad']} | {paises} | {oferta['publicada']}")
        if oferta.get("coinciden"):
            print(f"       Tienes: {', '.join(oferta['coinciden'])}")
        if oferta.get("faltan"):
            print(f"       Te falta: {', '.join(oferta['faltan'])}")
        print(f"       {oferta['url']}  (vía {oferta['fuente']})\n")
    if len(ofertas) > limite:
        print(f"(Mostrando {limite} de {len(ofertas)}. Usa --limite para ver más.)")


def comando_buscar(args):
    elegidas = [args.fuente] if args.fuente else list(FUENTES)
    ofertas = []
    for clave in elegidas:
        fuente = FUENTES[clave]
        print(f"Buscando en {fuente.NOMBRE}...")
        try:
            encontradas = fuente.buscar_ofertas(args.consulta, solo_relevantes=not args.todas)
        except requests.RequestException as error:
            # Si un portal falla, seguimos con los demás en vez de detener todo.
            print(f"  No pude conectarme con {fuente.NOMBRE}: {error}")
            continue
        print(f"  {len(encontradas)} ofertas")
        ofertas.extend(encontradas)
    print()

    conexion = db.conectar()
    ids_nuevas = db.guardar_ofertas(conexion, ofertas)
    nuevas = db.obtener_ofertas(conexion, ids_nuevas)  # releídas para tener su número corto
    conexion.close()

    print(f"Encontré {len(ofertas)} ofertas; {len(ids_nuevas)} son nuevas.\n")
    if not nuevas:
        print("No hay ofertas nuevas desde tu última búsqueda. Usa 'listar' para ver todas.")
        return 0
    nuevas = compatibilidad.ordenar_y_filtrar(nuevas, cargar_habilidades_cv())
    imprimir_ofertas(nuevas, args.limite)
    return 0


def comando_listar(args):
    conexion = db.conectar()
    ofertas = db.listar_ofertas(conexion, dias_vigencia=args.dias, estado=args.estado)
    conexion.close()

    ofertas = compatibilidad.ordenar_y_filtrar(
        ofertas, cargar_habilidades_cv(), minimo=args.minimo, modalidad=args.modalidad)
    print(f"Tienes {len(ofertas)} ofertas vigentes que cumplen los filtros.\n")
    imprimir_ofertas(ofertas, args.limite)
    return 0


def comando_ver(args):
    conexion = db.conectar()
    oferta = db.obtener_oferta(conexion, args.num)
    conexion.close()
    if not oferta:
        print(f"No existe la oferta #{args.num}. Usa 'listar' para ver los números.")
        return 1

    compatibilidad.evaluar(oferta, cargar_habilidades_cv())
    imprimir_ofertas([oferta], 1)
    print(f"Estado: {oferta['estado']}" + (f" (desde {oferta['fecha_estado']})"
                                           if oferta["fecha_estado"] else ""))
    if oferta["notas"]:
        print(f"Notas: {oferta['notas']}")
    if oferta["salario_min"] or oferta["salario_max"]:
        print(f"Salario: {oferta['salario_min'] or '?'} - {oferta['salario_max'] or '?'} USD")
    print(f"Fuente: {oferta['fuente']} | Vista por primera vez: {oferta['primera_vez']}\n")
    descripcion = oferta["descripcion"] or "(sin descripción)"
    print(descripcion if args.completa or len(descripcion) <= 1500
          else descripcion[:1500] + "... (usa --completa para leer todo)")
    return 0


def comando_marcar(args):
    conexion = db.conectar()
    ok = db.cambiar_estado(conexion, args.num, args.estado, notas=args.nota)
    oferta = db.obtener_oferta(conexion, args.num) if ok else None
    conexion.close()
    if not ok:
        print(f"No existe la oferta #{args.num}. Usa 'listar' para ver los números.")
        return 1
    print(f"Listo: #{args.num} {oferta['titulo']} ({oferta['empresa']}) ahora está en '{args.estado}'.")
    return 0


def comando_resumen(args):
    conexion = db.conectar()
    conteo = db.contar_por_estado(conexion)
    conexion.close()
    print(f"Tienes {sum(conteo.values())} ofertas guardadas:\n")
    for estado in db.ESTADOS:
        print(f"  {estado:<11} {conteo.get(estado, 0):>4}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Tu buscador de empleo en la terminal.")
    subcomandos = parser.add_subparsers(dest="comando", required=True)

    parser_cv = subcomandos.add_parser("cv", help="Lee tu CV y muestra tus habilidades")
    parser_cv.add_argument("--ruta", default=str(RUTA_CV), help="Ruta al PDF de tu CV")
    parser_cv.add_argument("--texto", action="store_true",
                           help="Muestra el texto que se pudo leer del PDF")
    parser_cv.set_defaults(funcion=comando_cv)

    parser_buscar = subcomandos.add_parser("buscar", help="Busca ofertas en todas las fuentes")
    parser_buscar.add_argument("--consulta", action="append",
                               help="Palabra a buscar (puedes repetirla varias veces)")
    parser_buscar.add_argument("--todas", action="store_true",
                               help="No filtrar por nivel junior ni por país")
    parser_buscar.add_argument("--limite", type=int, default=20,
                               help="Cuántas ofertas mostrar (por defecto 20)")
    parser_buscar.add_argument("--fuente", choices=sorted(FUENTES),
                               help="Busca solo en esa fuente")
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
    parser_listar.add_argument("--estado", choices=db.ESTADOS,
                               help="Solo ofertas en ese estado (incluye rechazadas y descartadas)")
    parser_listar.set_defaults(funcion=comando_listar)

    parser_ver = subcomandos.add_parser("ver", help="Muestra el detalle de una oferta")
    parser_ver.add_argument("num", type=int, help="Número de la oferta (el que sale con #)")
    parser_ver.add_argument("--completa", action="store_true", help="Muestra toda la descripción")
    parser_ver.set_defaults(funcion=comando_ver)

    parser_marcar = subcomandos.add_parser("marcar", help="Cambia el estado de una oferta")
    parser_marcar.add_argument("num", type=int, help="Número de la oferta (el que sale con #)")
    parser_marcar.add_argument("estado", choices=db.ESTADOS, help="Nuevo estado")
    parser_marcar.add_argument("--nota", help='Un apunte, ej. --nota "Envié CV por correo"')
    parser_marcar.set_defaults(funcion=comando_marcar)

    parser_resumen = subcomandos.add_parser("resumen", help="Cuántas ofertas hay en cada estado")
    parser_resumen.set_defaults(funcion=comando_resumen)

    args = parser.parse_args()
    return args.funcion(args)


if __name__ == "__main__":
    sys.exit(main())
