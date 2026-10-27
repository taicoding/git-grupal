from __future__ import annotations

import csv
from pathlib import Path


def load_company_names(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, skipinitialspace=True)
        if not reader.fieldnames or "EMPRESA" not in reader.fieldnames:
            raise ValueError(
                "El CSV debe contener una columna llamada EMPRESA. "
                f"Columnas encontradas: {reader.fieldnames}"
            )
        return list(
            dict.fromkeys(
                row["EMPRESA"].strip().upper()
                for row in reader
                if row.get("EMPRESA") and row["EMPRESA"].strip()
            )
        )
