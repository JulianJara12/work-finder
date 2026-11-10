"""Calcula qué tanto encaja una oferta con las habilidades de tu CV."""

from cv import encontrar_habilidades

MODALIDADES_FILTRO = {
    "remoto": {"Remoto", "Remoto (solo en el país)"},
    "hibrido": {"Híbrido"},
    "presencial": {"Presencial"},
}


def evaluar(oferta, habilidades_cv):
    """Agrega a la oferta su puntaje de compatibilidad (0 a 100) y el detalle.

    puntaje = habilidades que pide la oferta y tú tienes / habilidades que pide la oferta
    Si la oferta no menciona ninguna habilidad conocida, el puntaje queda en None.
    """
    pedidas = encontrar_habilidades(f"{oferta['titulo']} {oferta['descripcion']}")
    tienes = [h for h in pedidas if h in habilidades_cv]
    te_faltan = [h for h in pedidas if h not in habilidades_cv]

    oferta["habilidades_pedidas"] = pedidas
    oferta["coinciden"] = tienes
    oferta["faltan"] = te_faltan
    oferta["puntaje"] = round(100 * len(tienes) / len(pedidas)) if pedidas else None
    return oferta


def ordenar_y_filtrar(ofertas, habilidades_cv, minimo=0, modalidad=None):
    """Evalúa todas las ofertas, aplica los filtros y las ordena de mejor a peor."""
    evaluadas = [evaluar(o, habilidades_cv) for o in ofertas]

    if modalidad:
        permitidas = MODALIDADES_FILTRO[modalidad]
        evaluadas = [o for o in evaluadas if o["modalidad"] in permitidas]
    if minimo:
        evaluadas = [o for o in evaluadas if (o["puntaje"] or 0) >= minimo]

    # Primero por puntaje (las sin puntaje al final) y, si empatan, la más reciente primero.
    evaluadas.sort(key=lambda o: (o["puntaje"] if o["puntaje"] is not None else -1,
                                  o["publicada"]), reverse=True)
    return evaluadas
