"""
MODÜL 7 — YARDIMCI ÜRETİM (pres hattı)

Fabrikanın kalan girdi açığını kapatır:

    #c:ingots/gold  --pressing-->  create:golden_sheet   (modül 4'ün girdisi)
    #c:ingots/iron  --pressing-->  create:iron_sheet

Pres geometrisi (Create'in `mechanical_press/pressing` ponder sahnesi):

    bant   [2,1,2]
    boşluk [2,2,2]        <- boş kalmalı
    pres   [2,3,2] facing=north
    tahrik [2,3,3] cogwheel axis=z   (presin ekseni facing ekseni)

`MechanicalPressBlock.hasShaftTowards` = `face.getAxis() == facing ekseni`,
yani pres milini **iki yanından** da alır. Bu sayede aynı eksende dizilen
presler tek bir şaft hattının parçası olur — iki hattı tek milden sürüyoruz.
"""

from __future__ import annotations

from .. import blocks as B
from .. import stress as S
from ..canvas import Canvas

MODULE_ID = "07_press"
TITLE = "Modül 7 — Yardımcı üretim: pres hattı"

RPM = 64
BELT_Y = 10
PRESS_Y = BELT_Y + 2  # ponder: bant / boşluk / pres
DRIVE_Y = 15
DRIVE_Z = 4
PRESS_X = 4
BELT_X0, BELT_X1 = 1, 8

LANES = [("golden_sheet", 2, "altın külçe → golden sheet (modül 4'ün girdisi)"),
         ("iron_sheet", 6, "demir külçe → iron sheet")]


def _lane(c: Canvas, name: str, z: int, note: str) -> None:
    c.belt_run((BELT_X0, BELT_Y, z), "east", BELT_X1 - BELT_X0 + 1)
    c.set((PRESS_X, BELT_Y + 1, z), B.AIR)  # pres ile bant arası boş
    c.set((PRESS_X, PRESS_Y, z), B.mechanical_press("north"))

    # girdi
    c.set((BELT_X0 - 1, BELT_Y + 1, z), B.item_vault("x"))
    c.set((BELT_X0, BELT_Y + 1, z), B.andesite_belt_funnel("east", shape="pushing"))
    c.set((BELT_X0 - 1, BELT_Y + 2, z), B.andesite_funnel("up", extracting=False))
    c.io(f"{name} girişi", (BELT_X0 - 1, BELT_Y + 2, z), "item-in", note)

    # çıkış
    c.set((BELT_X1 + 1, BELT_Y, z), B.andesite_funnel("west", extracting=False))
    c.set((BELT_X1 + 2, BELT_Y, z), B.item_vault("x"))
    c.io(f"{name} çıkışı", (BELT_X1 + 2, BELT_Y, z), "item-out", "")


def _drive(c: Canvas) -> None:
    zs = [z for _, z, _ in LANES]
    z_end = zs[-1] + 1

    # pres hattı: presler kendi eksenlerinde mil geçirdiği için aradaki
    # şaftlarla tek hat oluyor
    for z in range(zs[0] + 1, z_end + 1):
        if z not in zs:
            c.set((PRESS_X, PRESS_Y, z), B.shaft("z"))
    c.set((PRESS_X, PRESS_Y, z_end + 1), B.gearbox("x"))  # ±Y, ±Z
    for y in range(PRESS_Y + 1, DRIVE_Y):
        c.set((PRESS_X, y, z_end + 1), B.shaft("y"))
    c.set((PRESS_X, DRIVE_Y, z_end + 1), B.gearbox("x"))
    for z in range(DRIVE_Z + 1, z_end + 1):
        c.set((PRESS_X, DRIVE_Y, z), B.shaft("z"))
    c.set((PRESS_X, DRIVE_Y, DRIVE_Z), B.gearbox("y"), overwrite=True)

    # bant kasnak hattı: bantların start segmentleri hattın parçası
    for z in range(zs[0] + 1, z_end + 1):
        if z not in zs:
            c.set((BELT_X0, BELT_Y, z), B.shaft("z"))
    c.set((BELT_X0, BELT_Y, z_end + 1), B.gearbox("x"))
    for y in range(BELT_Y + 1, DRIVE_Y):
        c.set((BELT_X0, y, z_end + 1), B.shaft("y"))
    c.set((BELT_X0, DRIVE_Y, z_end + 1), B.gearbox("x"))
    for z in range(DRIVE_Z + 1, z_end + 1):
        c.set((BELT_X0, DRIVE_Y, z), B.shaft("z"))
    c.set((BELT_X0, DRIVE_Y, DRIVE_Z), B.gearbox("y"), overwrite=True)

    for x in range(0, PRESS_X + 1):
        if c.get((x, DRIVE_Y, DRIVE_Z)) is None:
            c.set((x, DRIVE_Y, DRIVE_Z), B.shaft("x"))
    c.io("güç girişi", (0, DRIVE_Y, DRIVE_Z), "rotation-in", f"{RPM} RPM, eksen X.")


def _stress_budget() -> S.Budget:
    b = S.Budget("Modül 7 (modül 1'in dalından beslenir @ 64 RPM)")
    b.add_load("Mechanical press", "create:mechanical_press", len(LANES), RPM)
    return b


def build() -> Canvas:
    c = Canvas(MODULE_ID, TITLE)
    for name, z, note in LANES:
        _lane(c, name, z, note)
    _drive(c)
    budget = _stress_budget()
    c.manifest.stress = {"used": budget.used}
    c.note(f"Toplam yük: {budget.used:,.0f} SU @ {RPM} RPM.")
    return c


BUDGETS = _stress_budget
