#!/usr/bin/env python3
"""
Şematik üreticisi.

    python build.py                # tüm hazır modülleri üret + doğrula
    python build.py --module power # tek modül
    python build.py --no-validate  # doğrulamayı atla
"""

from __future__ import annotations

import argparse
import sys

from createfactory import validate
from createfactory.modules import alloy, complex, farm, mechanism, ore, power, press, storage

MODULES = {
    "power": power,
    "ore": ore,
    "alloy": alloy,
    "mechanism": mechanism,
    "storage": storage,
    "farm": farm,
    "press": press,
    "complex": complex,
}

OUT_DIR = "out"


def build_one(name: str, *, do_validate: bool = True, formats=("schem", "nbt")) -> bool:
    mod = MODULES[name]
    canvas = mod.build()
    paths = []
    if "schem" in formats:
        paths.append(canvas.save(OUT_DIR, mod.MODULE_ID))  # Sponge v2 (WorldEdit)
    if "nbt" in formats:
        paths.append(canvas.save_nbt(OUT_DIR, mod.MODULE_ID))  # structure (Create)

    size = canvas.size
    print(f"\n=== {mod.TITLE}")
    for p in paths:
        print(f"    dosya : {p}")
    print(f"    boyut : {size[0]} x {size[1]} x {size[2]} (X x Y x Z), {len(canvas.blocks())} blok")
    print("    giriş/çıkış noktaları (şematik koordinatı, //paste sonrası min köşeye göre):")
    for p in canvas.normalized_io():
        print(f"      {p.pos!s:>14}  {p.kind:<13} {p.name}")

    ok = True
    if do_validate:
        expected = 3 if name == "power" else None
        report = validate.run(
            canvas.blocks(),
            expected_fluid_networks=expected,
            external_power=(name != "power"),
        )
        print("    doğrulama:")
        print(report.render())
        ok = not report.failed
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", choices=sorted(MODULES), action="append")
    ap.add_argument("--no-validate", action="store_true")
    ap.add_argument(
        "--format",
        choices=["schem", "nbt", "both"],
        default="both",
        help="schem = WorldEdit (Sponge v2), nbt = Create Schematic Table (structure)",
    )
    args = ap.parse_args()

    formats = ("schem", "nbt") if args.format == "both" else (args.format,)
    names = args.module or sorted(MODULES)
    all_ok = True
    for n in names:
        all_ok &= build_one(n, do_validate=not args.no_validate, formats=formats)

    print()
    if not all_ok:
        print("DOĞRULAMA BAŞARISIZ — yukarıdaki hatalara bakın.")
        return 1
    print("Tüm modüller üretildi ve doğrulandı.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
