#!/usr/bin/env python3
"""Parsea los JSON de las votaciones descargadas y los carga en SQLite.

Entrada:  data/raw/zip/Leg{N}/Sesion{S}/{AAAAMMDD}/*.zip (cada ZIP tiene un JSON por votación)
Salida:   data/processed/votaciones.sqlite
          - votaciones: una fila por votación, con totales oficiales
          - votos:      una fila por diputado y votación
          - validacion: votaciones cuyo recuento no cuadra con los totales oficiales

Uso: python3 scripts/parsear_votaciones.py
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
import zipfile
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ZIP_DIR = RAIZ / "data" / "raw" / "zip"
SALIDA = RAIZ / "data" / "processed" / "votaciones.sqlite"

# Valores de voto tal como aparecen en el JSON (con acentos ya decodificados).
VOTO_SI, VOTO_NO, VOTO_ABS, VOTO_NOVOTA = "Sí", "No", "Abstención", "No vota"

ESQUEMA = """
DROP TABLE IF EXISTS votos;
DROP TABLE IF EXISTS votaciones;
DROP TABLE IF EXISTS validacion;
CREATE TABLE votaciones (
    id INTEGER PRIMARY KEY,
    legislatura TEXT NOT NULL,
    sesion INTEGER,
    numero INTEGER,
    fecha TEXT,
    titulo TEXT,
    texto_expediente TEXT,
    subgrupo TEXT,
    texto_subgrupo TEXT,
    asentimiento TEXT,
    presentes INTEGER,
    a_favor INTEGER,
    en_contra INTEGER,
    abstenciones INTEGER,
    no_votan INTEGER,
    archivo TEXT
);
CREATE TABLE votos (
    votacion_id INTEGER NOT NULL REFERENCES votaciones(id),
    asiento TEXT,
    diputado TEXT,
    grupo TEXT,
    voto TEXT
);
CREATE TABLE validacion (
    votacion_id INTEGER NOT NULL REFERENCES votaciones(id),
    campo TEXT NOT NULL,
    oficial INTEGER,
    recuento INTEGER,
    PRIMARY KEY (votacion_id, campo)
);
CREATE INDEX idx_votos_votacion ON votos(votacion_id);
CREATE INDEX idx_votos_grupo ON votos(grupo);
"""


def legislatura_de(ruta_zip: Path) -> str:
    m = re.search(r"Leg(\d+)", str(ruta_zip))
    return f"Leg{m.group(1)}" if m else "desconocida"


def entero(valor) -> int | None:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def main() -> int:
    if not ZIP_DIR.exists():
        print(f"No existe {ZIP_DIR}; ejecuta antes scripts/descargar_votaciones.py", file=sys.stderr)
        return 1
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    if SALIDA.exists():
        SALIDA.unlink()

    con = sqlite3.connect(SALIDA)
    con.executescript(ESQUEMA)

    zips = sorted(ZIP_DIR.rglob("*.zip"))
    n_vot = n_votos = 0
    descartes = []
    no_cuadran = []

    for ruta in zips:
        try:
            zf = zipfile.ZipFile(ruta)
        except zipfile.BadZipFile:
            descartes.append(str(ruta))
            continue
        with zf:
            for nombre in zf.namelist():
                if not nombre.endswith(".json"):
                    continue
                datos = json.loads(zf.read(nombre).decode("utf-8"))
                info = datos["informacion"]
                tot = datos["totales"]
                filas = datos["votaciones"]

                cur = con.execute(
                    """INSERT INTO votaciones (legislatura, sesion, numero, fecha, titulo, texto_expediente,
                       subgrupo, texto_subgrupo, asentimiento, presentes, a_favor, en_contra,
                       abstenciones, no_votan, archivo) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        legislatura_de(ruta),
                        entero(info.get("sesion")),
                        entero(info.get("numeroVotacion")),
                        info.get("fecha"),
                        info.get("titulo"),
                        info.get("textoExpediente"),
                        info.get("tituloSubGrupo"),
                        info.get("textoSubGrupo"),
                        tot.get("asentimiento"),
                        entero(tot.get("presentes")),
                        entero(tot.get("afavor")),
                        entero(tot.get("enContra")),
                        entero(tot.get("abstenciones")),
                        entero(tot.get("noVotan")),
                        str(ruta.relative_to(RAIZ)),
                    ),
                )
                vid = cur.lastrowid
                n_vot += 1

                conteo = Counter(f["voto"] for f in filas)
                con.executemany(
                    "INSERT INTO votos (votacion_id, asiento, diputado, grupo, voto) VALUES (?,?,?,?,?)",
                    [(vid, f.get("asiento"), f.get("diputado"), f.get("grupo"), f.get("voto")) for f in filas],
                )
                n_votos += len(filas)

                # Comprobación contra los totales oficiales.
                controles = [
                    ("a_favor", entero(tot.get("afavor")), conteo[VOTO_SI]),
                    ("en_contra", entero(tot.get("enContra")), conteo[VOTO_NO]),
                    ("abstenciones", entero(tot.get("abstenciones")), conteo[VOTO_ABS]),
                    ("no_votan", entero(tot.get("noVotan")), conteo[VOTO_NOVOTA]),
                ]
                for campo, oficial, recuento in controles:
                    if oficial != recuento:
                        con.execute(
                            "INSERT INTO validacion (votacion_id, campo, oficial, recuento) VALUES (?,?,?,?)",
                            (vid, campo, oficial, recuento),
                        )
                        no_cuadran.append((info.get("fecha"), info.get("numeroVotacion"), campo, oficial, recuento))

    con.commit()
    con.close()

    print(f"ZIP leídos: {len(zips)}  (corruptos: {len(descartes)})")
    print(f"Votaciones: {n_vot}  Registros de voto: {n_votos}")
    print(f"Votaciones que no cuadran con los totales oficiales: {len(no_cuadran)}")
    for fila in no_cuadran[:15]:
        print("  ", fila)
    print(f"Base de datos: {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
