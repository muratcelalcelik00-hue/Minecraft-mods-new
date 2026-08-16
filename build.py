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
from createfactory.modules import power

MODULES = {
    "power": power,
}

OUT_DIR = "out"


def build_one(name: str, *, do_validate: bool = True) -> bool:
    mod = MODULES[name]
    canvas = mod.build()
    path = canvas.save(OUT_DIR, mod.MODULE_ID)

    size = canvas.size
    print(f"\n=== {mod.TITLE}")
    print(f"    dosya : {path}")
    print(f"    boyut : {size[0]} x {size[1]} x {size[2]} (X x Y x Z), {len(canvas.blocks())} blok")
    print("    giriş/çıkış noktaları (şematik koordinatı, //paste sonrası min köşeye göre):")
    for p in canvas.normalized_io():
        print(f"      {p.pos!s:>14}  {p.kind:<13} {p.name}")

    ok = True
    if do_validate:
        report = validate.run(canvas.blocks())
        print("    doğrulama:")
        print(report.render())
        ok = not report.failed
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", choices=sorted(MODULES), action="append")
    ap.add_argument("--no-validate", action="store_true")
    args = ap.parse_args()

    names = args.module or sorted(MODULES)
    all_ok = True
    for n in names:
        all_ok &= build_one(n, do_validate=not args.no_validate)

    print()
    if not all_ok:
        print("DOĞRULAMA BAŞARISIZ — yukarıdaki hatalara bakın.")
        return 1
    print("Tüm modüller üretildi ve doğrulandı.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
