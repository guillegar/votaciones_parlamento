# Votaciones del Congreso

Web estática con las votaciones nominales del Congreso de los Diputados de los últimos 8 años, con el desglose del voto por grupo parlamentario en cada votación.

## Estado

Fase inicial: solo esqueleto del proyecto. Todavía no hay datos ni código de pipeline.

## Plan

1. **Datos (pipeline en Python):** descargar las votaciones nominales desde los datos abiertos del Congreso, parsear, normalizar y validar. Cada votación debe cuadrar con sus totales oficiales.
2. **Modelo:** base SQLite (o JSON troceado) con votaciones, diputados, grupos y afiliación vigente en cada fecha.
3. **Web estática:** HTML + JS con búsqueda en cliente. Vistas previstas: desglose por votación, cohesión de voto por grupo, matriz de acuerdo entre grupos y ficha por diputado.
4. **Actualización:** job programado tras cada pleno y despliegue en GitHub Pages o Netlify.

## Fuente de datos (verificado)

Las votaciones están en `www.congreso.es`, no en `datos.congreso.es` (ese host devolvió 502 desde el entorno).

- Índice por legislatura: `https://www.congreso.es/opendata/votaciones` (XV hasta X).
- Ficheros por votación: `/webpublica/opendata/votaciones/Leg{N}/Sesion{S}/{AAAAMMDD}/Votacion{NNN}/VOT_{id}.{xml|json|pdf}`.
- ZIP por sesión con todas sus votaciones (en torno a 9 MB; contiene XML, JSON, PDF y PNG).
- XML en ISO-8859-1; JSON en UTF-8 con el mismo contenido.
- Cada votación trae título, expediente, totales (a favor, en contra, abstenciones, no votan) y una fila por diputado con nombre, asiento, grupo y voto.
- Códigos de grupo vistos: `GS`, `GP`, `GVOX`, `GPlu`, `GR`, `GCUP-EC-GC`, `GCs`, `GEH Bildu`, `GMx`, `GV (EAJ-PNV)`. Los códigos cambian entre legislaturas, así que hace falta una tabla de mapeo.
- Valores de voto: `Sí`, `No`, `Abstención`, `No vota`.
- El diputado se identifica por nombre y asiento, sin ID estable. Hay que decidir cómo generar una clave.
- Acceso: el sitio devuelve 403 a clientes con User-Agent por defecto; con un User-Agent de navegador funciona.

## Pendiente de verificar

- Licencia de reutilización de los datos (la página de aviso legal redirige y no se ha podido leer).
- Mapeo de códigos de grupo, siglas y cambios de grupo o fusiones/escisiones a lo largo de las legislaturas.
- Cobertura real de los 8 años: qué legislaturas y sesiones están publicadas.

## Principios

- Presentación neutral: se muestran disciplina de voto y coincidencias, sin etiquetar a nadie.
- Las limitaciones (ausencias, cambios de grupo, votaciones telemáticas) se documentan en la propia web.
