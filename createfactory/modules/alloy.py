"""
MODÜL 3 — ALAŞIM (andesite alloy + brass)

Tarifler (kaynaktan doğrulandı):

    andesite + iron nugget  --mixing---------->  andesite alloy
    andesite + zinc nugget  --mixing---------->  andesite alloy   (alternatif)
    copper ingot + zinc ingot --mixing(heated)->  2 x brass ingot

İki bağımsız hat:

    A (z=2)  andesite alloy — ısı GEREKMEZ
    B (z=6)  brass          — "heated" ister

`HeatCondition.HEATED` şunu der:
    `level != HeatLevel.NONE && level != HeatLevel.SMOULDERING`
Kamp ateşi / lav / magma yalnız SMOULDERING verir (BasinBlockEntity
.getHeatLevelOf), yani **yetmez**. Pirinç için yakıtlı bir blaze burner şart;
o yüzden B hattında basin'in altında bir burner ve onu besleyen bir deployer var.

Basin geometrisi (doğrulanmış):
  - mixer basin'in tam **2 blok üstünde** (aradaki blok boş)
  - mixer'ın ŞAFTI YOK; yanındaki küçük dişliyle kavrayarak döner
  - basin **doğrudan bant girdisi** kabul eder (DirectBeltInputBehaviour),
    yani bandın ucu basin'e dayanınca funnel gerekmez
  - basin çıkışı: yan komşu BOŞ + onun ALTI bant olmalı; Create çıkış yönünü
    kendi bulur (updateSpoutput), blockstate'i elle ayarlamaya gerek yok
"""

from __future__ import annotations

from .. import blocks as B
from .. import stress as S
from ..canvas import Canvas

MODULE_ID = "03_alloy"
TITLE = "Modül 3 — Alaşım: andesite alloy + brass"

RPM = 64
DRIVE_Y = 15
DRIVE_Z = 4

BASIN_X, BASIN_Y = 4, 10
MIXER_Y = BASIN_Y + 2
LANES = {"andesite_alloy": 2, "brass": 6}

IN_BELT_X0, IN_BELT_X1 = 2, 3  # bandın ucu basin'e dayanır
OUT_BELT_X0, OUT_BELT_X1 = 5, 11
IN_LINE_X, OUT_LINE_X = 2, 5


def _station(c: Canvas, lane_z: int, heated: bool) -> None:
    c.set((BASIN_X, BASIN_Y, lane_z), B.basin())
    c.set((BASIN_X, BASIN_Y + 1, lane_z), B.AIR)  # mixer ile basin arası boş
    c.set((BASIN_X, MIXER_Y, lane_z), B.mechanical_mixer())

    # girdi bandı: ucu basin'e dayanır
    c.belt_run((IN_BELT_X0, BASIN_Y, lane_z), "east", IN_BELT_X1 - IN_BELT_X0 + 1)
    c.set((IN_LINE_X - 1, BASIN_Y + 1, lane_z), B.item_vault("x"))
    c.set((IN_LINE_X, BASIN_Y + 1, lane_z), B.andesite_belt_funnel("east", shape="pushing"))
    c.set((IN_LINE_X - 1, BASIN_Y + 2, lane_z), B.andesite_funnel("up", extracting=False))

    # çıkış: yan komşu boş, altı bant
    c.set((OUT_BELT_X0, BASIN_Y, lane_z), B.AIR)
    c.belt_run((OUT_BELT_X0, BASIN_Y - 1, lane_z), "east", OUT_BELT_X1 - OUT_BELT_X0 + 1)
    c.set((OUT_BELT_X1 + 1, BASIN_Y - 1, lane_z), B.andesite_funnel("west", extracting=False))
    c.set((OUT_BELT_X1 + 2, BASIN_Y - 1, lane_z), B.item_vault("x"))

    if heated:
        c.set((BASIN_X, BASIN_Y - 1, lane_z), B.blaze_burner("kindled", facing="north"))


def _belt_drive_lines(c: Canvas) -> None:
    """Bantların kasnaklarını tek bir Z hattından sürer.

    Bir bandın start/end segmenti ±(dik yatay eksen) yönünde şaft kabul eder;
    yani hattın üstünden geçen bant, iki yanındaki şaftları 1:1 birbirine
    bağlar ve hat kesintiye uğramaz.
    """
    # girdi bantları (y=10) — bantlar z=2 ve z=6'da hattın parçası olur
    for z in (0, 1, 3, 4, 5, 7):
        c.set((IN_LINE_X, BASIN_Y, z), B.shaft("z"))
    c.set((IN_LINE_X, BASIN_Y, 0), B.gearbox("x"), overwrite=True)
    for y in range(BASIN_Y + 1, DRIVE_Y):
        c.set((IN_LINE_X, y, 0), B.shaft("y"))
    c.set((IN_LINE_X, DRIVE_Y, 0), B.gearbox("x"))
    for z in range(1, DRIVE_Z):
        c.set((IN_LINE_X, DRIVE_Y, z), B.shaft("z"))
    c.set((IN_LINE_X, DRIVE_Y, DRIVE_Z), B.gearbox("y"), overwrite=True)

    # çıkış bantları (y=9)
    for z in (0, 1, 3, 4, 5):
        c.set((OUT_LINE_X, BASIN_Y - 1, z), B.shaft("z"))
    c.set((OUT_LINE_X, BASIN_Y - 1, 0), B.gearbox("x"), overwrite=True)
    for y in range(BASIN_Y, DRIVE_Y):
        c.set((OUT_LINE_X, y, 0), B.shaft("y"))
    c.set((OUT_LINE_X, DRIVE_Y, 0), B.gearbox("x"))
    for z in range(1, DRIVE_Z):
        c.set((OUT_LINE_X, DRIVE_Y, z), B.shaft("z"))
    c.set((OUT_LINE_X, DRIVE_Y, DRIVE_Z), B.gearbox("y"), overwrite=True)


def _mixer_drive(c: Canvas) -> None:
    """Mixer'lar şaft kabul etmez; Y eksenli dişli zinciriyle sürülür."""
    for z in range(LANES["andesite_alloy"], LANES["brass"] + 1):
        c.set((5, MIXER_Y, z), B.cog("y"))
    c.set((6, MIXER_Y, DRIVE_Z), B.cog("y"))  # zinciri süren dişli
    for y in range(MIXER_Y + 1, DRIVE_Y):
        c.set((6, y, DRIVE_Z), B.shaft("y"))
    c.set((6, DRIVE_Y, DRIVE_Z), B.gearbox("z"), overwrite=True)


def _burner_feed(c: Canvas) -> None:
    """Pirinç basin'inin altındaki blaze burner'ı besleyen deployer."""
    z = LANES["brass"] - 1
    c.set((BASIN_X, BASIN_Y - 1, z), B.deployer("south", axis_along_first=True))
    c.set((BASIN_X, BASIN_Y, z), B.chute("down"))
    c.set((BASIN_X, BASIN_Y + 1, z), B.item_vault("x"))
    c.set((BASIN_X, BASIN_Y + 2, z), B.andesite_funnel("up", extracting=False))
    c.io(
        "eritme yakıtı (pirinç)",
        (BASIN_X, BASIN_Y + 2, z),
        "item-in",
        "Kömür / odun kömürü. Blaze burner sönerse pirinç durur, andesite alloy devam eder.",
    )

    # deployer dönme ekseni X -> ±X yüzlerinden sürülür
    for x in (BASIN_X - 1, BASIN_X - 2):
        c.set((x, BASIN_Y - 1, z), B.shaft("x"))
    c.set((1, BASIN_Y - 1, z), B.gearbox("z"))
    for y in range(BASIN_Y, DRIVE_Y):
        c.set((1, y, z), B.shaft("y"))
    c.set((1, DRIVE_Y, z), B.gearbox("x"))
    for zz in range(DRIVE_Z + 1, z):
        c.set((1, DRIVE_Y, zz), B.shaft("z"))
    c.set((1, DRIVE_Y, DRIVE_Z), B.gearbox("y"), overwrite=True)


def _drive_line(c: Canvas) -> None:
    for x in range(0, 7):
        c.set((x, DRIVE_Y, DRIVE_Z), B.shaft("x"))
    c.io("güç girişi", (0, DRIVE_Y, DRIVE_Z), "rotation-in", f"{RPM} RPM, eksen X.")


def _stress_budget() -> S.Budget:
    b = S.Budget("Modül 3 (modül 1'in dalından beslenir @ 64 RPM)")
    b.add_load("Mechanical mixer", "create:mechanical_mixer", 2, RPM)
    b.add_load("Deployer (yakıt)", "create:deployer", 1, RPM)
    return b


def build() -> Canvas:
    c = Canvas(MODULE_ID, TITLE)
    _drive_line(c)
    for name, z in LANES.items():
        _station(c, z, heated=(name == "brass"))
        c.io(
            f"{name} girişi",
            (IN_LINE_X - 1, BASIN_Y + 2, z),
            "item-in",
            "andesite + iron/zinc nugget" if name == "andesite_alloy" else "copper ingot + zinc ingot",
        )
        c.io(f"{name} çıkışı", (OUT_BELT_X1 + 2, BASIN_Y - 1, z), "item-out", "")
    _belt_drive_lines(c)
    _mixer_drive(c)
    _burner_feed(c)

    budget = _stress_budget()
    c.manifest.stress = {"used": budget.used}
    c.note(f"Toplam yük: {budget.used:,.0f} SU @ {RPM} RPM.")
    return c


BUDGETS = _stress_budget
