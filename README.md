# Work Finder

Buscador de empleo en la terminal, hecho en Python. Lee tu hoja de vida, trae ofertas
vigentes de portales de empleo, calcula qué tan compatibles son contigo y te ayuda a
llevar el control de tus postulaciones.

Está pensado para perfiles **junior** de ingeniería de sistemas (programación, bases de
datos y análisis de datos) en **Bogotá, Colombia**, con ofertas presenciales, híbridas o
remotas. Todo se puede adaptar a otro perfil editando un par de listas.

```
$ python workfinder.py listar --minimo 50

Tienes 6 ofertas vigentes que cumplen los filtros.

[ 75%] #4 Analista de Datos Junior | Acme
       Junior | Híbrido | Colombia | 2026-11-03
       Tienes: SQL, Power BI, Excel
       Te falta: Python
       https://www.getonbrd.com/jobs/...  (vía Get on Board)

[ 67%] #9 Junior Data Analyst | Globex (postule)
       Junior | Remoto | LATAM | 2026-11-02
       Tienes: SQL, Python
       Te falta: Tableau
       https://remoteok.com/remote-jobs/...  (vía Remote OK)
```

## Qué hace

- **Lee tu CV en PDF** y detecta tus habilidades (SQL, Python, Power BI, Java...) a partir
  de una lista de unas 85 habilidades con sus sinónimos en español e inglés.
- **Busca ofertas** en varias fuentes y se queda solo con las de nivel junior o sin
  experiencia que puedes tomar desde Colombia.
- **Calcula un puntaje de compatibilidad** entre tu CV y cada oferta, y te dice qué
  habilidades tienes y cuáles te faltan.
- **Guarda todo en una base de datos SQLite**, para mostrarte solo las ofertas nuevas en
  cada búsqueda y ocultar las que el portal retiró.
- **Lleva el control de tus postulaciones**: marcas cada oferta como "interesa",
  "postule", "entrevista", etc., con notas, y ves un resumen.

## Tecnologías

- Python 3.10+
- [requests](https://requests.readthedocs.io/) para consultar las APIs de los portales
- [pypdf](https://pypdf.readthedocs.io/) para leer el CV
- SQLite (incluido en Python) para guardar las ofertas
- `argparse` para los comandos de la terminal
- `unittest` para las pruebas automáticas

## Instalación

```bash
git clone https://github.com/JulianJara12/work-finder.git
cd work-finder

python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\activate
# Mac o Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

Luego crea la carpeta `datos` y copia ahí tu hoja de vida con el nombre `cv.pdf`:

```
work-finder/
├── datos/
│   └── cv.pdf      ← tu CV (Git lo ignora, nunca se sube)
└── workfinder.py
```

## Uso

Ejecuta todos los comandos desde la carpeta del proyecto, con el entorno virtual activado.

### 1. Revisa qué habilidades detecta en tu CV

```bash
python workfinder.py cv
python workfinder.py cv --texto        # muestra además el texto leído del PDF
python workfinder.py cv --ruta otro.pdf
```

Si falta alguna habilidad, agrégala en [`habilidades.py`](habilidades.py) (en minúsculas y
sin tildes), por ejemplo: `"Docker": ["docker", "contenedores"],`.

### 2. Busca ofertas nuevas

```bash
python workfinder.py buscar                     # todas las fuentes
python workfinder.py buscar --fuente remoteok   # una sola fuente
python workfinder.py buscar --consulta "power bi" --consulta etl
python workfinder.py buscar --todas             # sin filtrar por nivel ni país
```

Muestra solo las ofertas que no habías visto antes, ordenadas de mayor a menor
compatibilidad.

### 3. Revisa las ofertas guardadas

```bash
python workfinder.py listar
python workfinder.py listar --minimo 50              # 50 % de compatibilidad o más
python workfinder.py listar --modalidad remoto       # remoto, hibrido o presencial
python workfinder.py listar --estado postule         # solo las que ya postulaste
python workfinder.py ver 12                          # detalle completo de la oferta #12
python workfinder.py ver 12 --completa               # sin recortar la descripción
```

### 4. Lleva el control de tus postulaciones

```bash
python workfinder.py marcar 12 postule --nota "Envié CV por correo"
python workfinder.py marcar 7 descartada
python workfinder.py resumen
```

| Estado | Para qué sirve |
|---|---|
| `nueva` | Recién encontrada (estado inicial) |
| `interesa` | Quieres revisarla con calma |
| `postule` | Ya enviaste tu postulación |
| `entrevista` | Te llamaron a entrevista |
| `oferta` | Te hicieron una oferta |
| `rechazada` | No siguió el proceso (se oculta en `listar`) |
| `descartada` | No te interesa (se oculta en `listar`) |

Las ofertas en las que ya avanzaste se siguen mostrando aunque el portal las retire.

## Cómo funciona

### Puntaje de compatibilidad

El programa busca en el título y la descripción de cada oferta las mismas habilidades de
`habilidades.py` y calcula:

```
puntaje = habilidades que pide la oferta y tienes / habilidades que pide la oferta
```

Si una oferta no menciona ninguna habilidad conocida, aparece con `[  ? ]` al final de la
lista. Las coincidencias se buscan como palabras completas, así "Java" no se confunde con
"JavaScript" ni "SQL" con "MySQL".

### Vigencia de las ofertas

Cada búsqueda actualiza la fecha `ultima_vez` de las ofertas que siguen publicadas. Si una
oferta no vuelve a aparecer en 7 días (configurable con `listar --dias`), se asume que la
retiraron y deja de mostrarse, aunque sigue guardada en la base de datos.

### Base de datos

Todo queda en `datos/workfinder.db` (Git lo ignora). Puedes abrirlo con
[DB Browser for SQLite](https://sqlitebrowser.org/) para verlo como tabla o hacer tus
propias consultas SQL. Si en una versión nueva se agregan columnas, `db.py` las añade
automáticamente sin borrar tus datos.

## Fuentes de ofertas

| Fuente | Tipo de ofertas | Cómo se consulta |
|---|---|---|
| [Get on Board](https://www.getonbrd.com) | Empleos tech en Latinoamérica | API pública |
| [Remote OK](https://remoteok.com) | Empleos 100 % remotos de todo el mundo, casi siempre en inglés | API pública |

**Uso responsable:** el proyecto solo usa fuentes que permiten el acceso automatizado. Antes
de agregar un portal se revisan su `robots.txt` y sus términos de uso. Varios portales
colombianos (por ejemplo elempleo.com) prohíben expresamente que un programa lea sus
ofertas, por eso no están incluidos. Remote OK pide citarlo como fuente y enlazar a cada
oferta, y el programa lo hace en cada resultado.

### Agregar una fuente nueva

1. Crea un módulo en `fuentes/` (usa `fuentes/remoteok.py` como ejemplo) con:
   - `NOMBRE`: el nombre del portal.
   - `buscar_ofertas(consultas=None, solo_relevantes=True)`: devuelve una lista de
     diccionarios con los campos `id`, `fuente`, `titulo`, `empresa`, `url`, `paises`,
     `modalidad`, `nivel`, `publicada`, `salario_min`, `salario_max` y `descripcion`.
2. Agrégalo al diccionario `FUENTES` en `workfinder.py`.
3. Escribe sus pruebas en `tests/` con datos falsos, para no depender de internet.

## Estructura del proyecto

```
work-finder/
├── workfinder.py        # programa principal: comandos de la terminal
├── cv.py                # lee el PDF y detecta habilidades
├── habilidades.py       # lista de habilidades y sus sinónimos (edítala a tu gusto)
├── compatibilidad.py    # puntaje de compatibilidad y filtros
├── db.py                # base de datos SQLite
├── fuentes/
│   ├── comun.py         # utilidades compartidas por las fuentes
│   ├── getonbrd.py      # fuente: Get on Board
│   └── remoteok.py      # fuente: Remote OK
├── tests/               # pruebas automáticas (no necesitan internet)
├── datos/               # tu CV y la base de datos (ignorada por Git)
└── requirements.txt
```

## Pruebas

```bash
python -m unittest
```

Las pruebas usan datos falsos con la misma forma que las respuestas reales de los portales,
y una base de datos en memoria, así que no necesitan internet ni tocan tus datos.

## Próximas mejoras

- [ ] Sumar más fuentes que permitan el acceso automatizado (por ejemplo Magneto365, tras
      revisar sus términos).
- [ ] Leer las alertas de empleo que llegan por correo de los portales colombianos.
- [ ] Usar IA para adaptar el CV o la carta de presentación a una oferta concreta.
- [ ] Exportar las postulaciones a Excel o CSV.

## Autor

Proyecto personal de [@JulianJara12](https://github.com/JulianJara12), construido paso a
paso para aprender Python, APIs, bases de datos y pruebas automáticas mientras busco mi
primer empleo en el sector de sistemas.
