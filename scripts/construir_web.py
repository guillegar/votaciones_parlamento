#!/usr/bin/env python3
"""Genera los datos de la web a partir de data/processed/votaciones.sqlite.

Salida: web/datos/votaciones.json
Una entrada por votación, con el recuento de cada grupo (sí, no, abstención,
no vota). Se agrega por grupo para que el fichero sea manejable en el navegador;
el detalle por diputado se queda en la base de datos.

Uso: python3 scripts/construir_web.py
"""

from __future__ import annotations

import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BD = RAIZ / "data" / "processed" / "votaciones.sqlite"
SALIDA = RAIZ / "web" / "datos" / "votaciones.json"

CLAVES = {"Sí": "si", "No": "no", "Abstención": "abs", "No vota": "nv"}


def main() -> int:
    if not BD.exists():
        print(f"No existe {BD}; ejecuta antes scripts/parsear_votaciones.py", file=sys.stderr)
        return 1
    con = sqlite3.connect(BD)

    votaciones = {}
    for vid, leg, sesion, numero, fecha, titulo, expediente, a_favor, en_contra, abst, nv in con.execute(
        """SELECT id, legislatura, sesion, numero, fecha, titulo, texto_expediente,
                  a_favor, en_contra, abstenciones, no_votan FROM votaciones"""
    ):
        votaciones[vid] = {
            "id": vid,
            "legislatura": leg,
            "sesion": sesion,
            "numero": numero,
            "fecha": fecha,
            "titulo": titulo,
            "expediente": expediente,
            "totales": {"si": a_favor, "no": en_contra, "abs": abst, "nv": nv},
            "grupos": defaultdict(lambda: {"si": 0, "no": 0, "abs": 0, "nv": 0}),
        }

    for vid, grupo, voto in con.execute("SELECT votacion_id, grupo, voto FROM votos"):
        clave = CLAVES.get(voto)
        if clave is None:
            continue
        grupo = grupo or "(sin grupo)"
        votaciones[vid]["grupos"][grupo][clave] += 1

    salida = []
    for v in votaciones.values():
        v["grupos"] = dict(v["grupos"])
        salida.append(v)
    salida.sort(key=lambda v: (v["legislatura"], v["sesion"] or 0, v["numero"] or 0))

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump({"votaciones": salida}, f, ensure_ascii=False, separators=(",", ":"))

    print(f"Votaciones exportadas: {len(salida)}")
    print(f"Tamaño: {SALIDA.stat().st_size / 1e6:.1f} MB -> {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
