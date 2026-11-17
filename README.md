# Votaciones del Congreso

Web estática con las votaciones nominales del Congreso de los Diputados de los últimos 8 años, con el desglose del voto por grupo parlamentario en cada votación.

## Estado

Fase inicial: solo esqueleto del proyecto. Todavía no hay datos ni código de pipeline.

## Plan

1. **Datos (pipeline en Python):** descargar las votaciones nominales desde los datos abiertos del Congreso, parsear, normalizar y validar. Cada votación debe cuadrar con sus totales oficiales.
2. **Modelo:** base SQLite (o JSON troceado) con votaciones, diputados, grupos y afiliación vigente en cada fecha.
3. **Web estática:** HTML + JS con búsqueda en cliente. Vistas previstas: desglose por votación, cohesión de voto por grupo, matriz de acuerdo entre grupos y ficha por diputado.
4. **Actualización:** job programado tras cada pleno y despliegue en GitHub Pages o Netlify.

## Pendiente de verificar

- Endpoints exactos de las votaciones nominales y su formato (XML/JSON).
- Licencia de reutilización de los datos.
- Mapeo de cambios de grupo, siglas y fusiones/escisiones de grupos a lo largo de las legislaturas.

## Principios

- Presentación neutral: se muestran disciplina de voto y coincidencias, sin etiquetar a nadie.
- Las limitaciones (ausencias, cambios de grupo, votaciones telemáticas) se documentan en la propia web.
