#!/usr/bin/env python3
"""Descarga las votaciones nominales del Congreso de los Diputados.

Fuente: https://www.congreso.es/opendata/votaciones
Para cada legislatura se leen los días con votación y, por cada día, se
descarga el ZIP de la sesión (que contiene XML, JSON, PDF y PNG por votación).

Es reanudable: si un ZIP ya existe y es válido, se omite.
Solo usa la biblioteca estándar de Python.

Uso:
    python3 scripts/descargar_votaciones.py                # X a XV (2012-hoy)
    python3 scripts/descargar_votaciones.py --legislaturas XIV XV
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

BASE = "https://www.congreso.es"
INDEX = BASE + "/es/opendata/votaciones"
# El sitio responde 403 a User-Agent por defecto; se identifica el proyecto.
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) votaciones-congreso/0.1"
LEGISLATURAS = ["X", "XI", "XII", "XIII", "XIV", "XV"]
PAUSA_S = 0.7  # pausa entre peticiones para no saturar el servidor
REINTENTOS = 4

RAIZ = Path(__file__).resolve().parent.parent / "data" / "raw"
RE_DIAS = re.compile(r"var diasVotaciones = \[([^\]]*)\]")
RE_ZIP = re.compile(r"webpublica/opendata/votaciones/Leg\d+/Sesion\d+/\d{8}/VOT_\d+\.zip")

log = logging.getLogger("descarga")


def get(url: str) -> bytes:
    """GET con reintentos y backoff exponencial."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for intento in range(1, REINTENTOS + 1):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            espera = 2**intento
            log.warning("Error en %s (intento %d/%d): %s; reintento en %ds",
                        url, intento, REINTENTOS, e, espera)
            time.sleep(espera)
    raise RuntimeError(f"No se pudo descargar {url}")


def url_legislatura(leg: str, fecha: str | None = None) -> str:
    q = {
        "p_p_id": "votaciones",
        "p_p_lifecycle": "0",
        "p_p_state": "normal",
        "p_p_mode": "view",
        "targetLegislatura": leg,
    }
    if fecha:  # fecha en formato DD/MM/AAAA, como usa el propio sitio
        q["targetDate"] = fecha
    return INDEX + "?" + urllib.parse.urlencode(q, safe="/")


def dias_con_votacion(leg: str) -> list[dt.date]:
    """Lee del índice de la legislatura los días con votaciones (AAAAMMDD)."""
    html = get(url_legislatura(leg)).decode("utf-8", errors="replace")
    m = RE_DIAS.search(html)
    if not m:
        raise RuntimeError(f"No se encontró el calendario de votaciones de {leg}")
    dias = sorted(set(re.findall(r"\d{8}", m.group(1))))
    return [dt.datetime.strptime(d, "%Y%m%d").date() for d in dias]


def zips_del_dia(leg: str, dia: dt.date) -> list[str]:
    fecha = dia.strftime("%d/%m/%Y")
    html = get(url_legislatura(leg, fecha)).decode("utf-8", errors="replace")
    return sorted(set(RE_ZIP.findall(html)))


def zip_valido(ruta: Path) -> bool:
    try:
        with zipfile.ZipFile(ruta) as z:
            return z.testzip() is None
    except (zipfile.BadZipFile, OSError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--legislaturas", nargs="+", default=LEGISLATURAS, choices=LEGISLATURAS)
    args = parser.parse_args()

    RAIZ.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(RAIZ / "descarga.log", encoding="utf-8")],
    )

    total_zip = 0
    descargados = 0
    fallos = []
    for leg in args.legislaturas:
        dias = dias_con_votacion(leg)
        log.info("Legislatura %s: %d días con votaciones", leg, len(dias))
        time.sleep(PAUSA_S)
        for dia in dias:
            try:
                rutas_zip = zips_del_dia(leg, dia)
            except RuntimeError as e:
                log.error("Día %s (%s): %s", dia, leg, e)
                fallos.append(f"{leg} {dia}")
                continue
            time.sleep(PAUSA_S)
            if not rutas_zip:
                log.warning("Sin ZIP para %s en %s", dia, leg)
                fallos.append(f"{leg} {dia} (sin zip)")
                continue
            for ruta_rel in rutas_zip:
                total_zip += 1
                destino = RAIZ / "zip" / Path(ruta_rel).name
                # Ruta relativa: Leg10/Sesion004/20120111/VOT_xxx.zip
                if destino.exists() and zip_valido(destino):
                    continue
                destino.parent.mkdir(parents=True, exist_ok=True)
                try:
                    datos = get(BASE + "/" + ruta_rel)
                except RuntimeError as e:
                    log.error("%s", e)
                    fallos.append(ruta_rel)
                    continue
                tmp = destino.with_suffix(".part")
                tmp.write_bytes(datos)
                if not zip_valido(tmp):
                    log.error("ZIP corrupto: %s", ruta_rel)
                    tmp.unlink(missing_ok=True)
                    fallos.append(ruta_rel)
                    continue
                tmp.replace(destino)
                descargados += 1
                log.info("OK %s (%d KB)", ruta_rel, len(datos) // 1024)
                time.sleep(PAUSA_S)

    log.info("Fin: %d ZIP referenciados, %d descargados ahora, %d incidencias", total_zip, descargados, len(fallos))
    if fallos:
        (RAIZ / "incidencias.txt").write_text("\n".join(fallos) + "\n", encoding="utf-8")
        log.info("Incidencias guardadas en %s", RAIZ / "incidencias.txt")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
