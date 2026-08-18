"""
MODÜL 4 — MEKANİZMA (precision mechanism)

Tarif (`sequenced_assembly/precision_mechanism.json`):

    girdi : #c:plates/gold  (create:golden_sheet)
    loops : 5
    sıra  : deploying cogwheel -> deploying large_cogwheel -> deploying iron nugget

Yani toplam **5 x 3 = 15 deploy** işlemi gerekir.

Tasarım: bant döngüsü YOK, tek geçişte 15 deployer.
Döngülü kurulumda biten ürünü ayırmak için filtreli funnel ve dönüş yolu
gerekir; 15 deployer'ı yan yana dizmek hem daha kısa hem hatasız — sıra
kendiliğinden doğru olur (cog, large cog, nugget, cog, ...).

Besleme sorunu ve çözümü:
    15 deployer üç FARKLI item ister. Ortak bir item vault sırası (vault'lar
    aynı eksende bitişikse tek envanter olur) hepsini tutar, ve her deployer'ın
    üstündeki **smart chute** yalnız kendi filtresine uyan itemi çeker
    (SmartChuteBlockEntity: `canAcceptItem` içinde `filtering.test(stack)`).
    Böylece tek giriş noktası 15 istasyonu doğru şekilde besler.

Deployer'lar aşağı bakar ve dönme ekseni X'tir (`axis_along_first=true`,
facing ekseni Y -> X). Aynı eksenli deployer'lar yan yana geldiğinde birbirine
şaft gibi bağlanır, yani 15'i tek hattan döner.
"""

from __future__ import annotations

from .. import blocks as B
from .. import stress as S
from ..canvas import Canvas

MODULE_ID = "04_mechanism"
TITLE = "Modül 4 — Mekanizma: precision mechanism"

RPM = 64
LANE_Z = 2
BELT_Y = 10
DEPLOYER_Y = BELT_Y + 1
CHUTE_Y = BELT_Y + 2
VAULT_Y = BELT_Y + 3
DRIVE_Y = 16

#: tarifteki sıra — 5 tur tekrarlanır
SEQUENCE = ["create:cogwheel", "create:large_cogwheel", "minecraft:iron_nugget"]
LOOPS = 5
STATIONS = len(SEQUENCE) * LOOPS  # 15

X0 = 2  # ilk deployer
X1 = X0 + STATIONS - 1  # 16
BELT_X0, BELT_X1 = X0 - 1, X1 + 2  # 1 .. 18


def _assembly_line(c: Canvas) -> None:
    c.belt_run((BELT_X0, BELT_Y, LANE_Z), "east", BELT_X1 - BELT_X0 + 1)

    for i in range(STATIONS):
        x = X0 + i
        item = SEQUENCE[i % len(SEQUENCE)]
        # facing=down + axis_along_first=true -> dönme ekseni X
        # (yan yana deployer'lar böylece birbirine bağlanır)
        c.set((x, DEPLOYER_Y, LANE_Z), B.deployer("down", axis_along_first=True))
        c.set((x, CHUTE_Y, LANE_Z), B.smart_chute(item))
        c.set((x, VAULT_Y, LANE_Z), B.item_vault("x"))

    # ortak besleme girişi (vault sırası tek envanter)
    c.set((X0 + STATIONS // 2, VAULT_Y + 1, LANE_Z), B.andesite_funnel("up", extracting=False))
    c.io(
        "parça girişi",
        (X0 + STATIONS // 2, VAULT_Y + 1, LANE_Z),
        "item-in",
        "cogwheel + large cogwheel + iron nugget — hepsi AYNI vault'a. "
        "Smart chute'lar her istasyona doğru parçayı çeker.",
    )


def _sheet_input(c: Canvas) -> None:
    """Altın levha girişi: vault -> belt funnel -> bandın başı."""
    c.set((BELT_X0, DEPLOYER_Y, LANE_Z - 1), B.item_vault("x"))
    c.set((BELT_X0, DEPLOYER_Y, LANE_Z), B.andesite_belt_funnel("south", shape="pushing"))
    c.set((BELT_X0, DEPLOYER_Y + 1, LANE_Z - 1), B.andesite_funnel("up", extracting=False))
    c.io(
        "altın levha girişi",
        (BELT_X0, DEPLOYER_Y + 1, LANE_Z - 1),
        "item-in",
        "create:golden_sheet (#c:plates/gold). Zincirin başlangıç maddesi.",
    )


def _output(c: Canvas) -> None:
    c.set((BELT_X1 + 1, BELT_Y, LANE_Z), B.andesite_funnel("west", extracting=False))
    c.set((BELT_X1 + 2, BELT_Y, LANE_Z), B.item_vault("x"))
    c.io(
        "ürün çıkışı",
        (BELT_X1 + 2, BELT_Y, LANE_Z),
        "item-out",
        "precision mechanism (+ tarifin yan ürünleri: golden sheet, andesite "
        "alloy, cogwheel, nugget, shaft, clock...).",
    )


def _drive(c: Canvas) -> None:
    # ana hat
    for x in range(0, BELT_X1 + 1):
        c.set((x, DRIVE_Y, LANE_Z), B.shaft("x"))
    c.io("güç girişi", (0, DRIVE_Y, LANE_Z), "rotation-in", f"{RPM} RPM, eksen X.")

    # deployer hattı (eksen X) -> yukarı
    c.set((X1 + 1, DEPLOYER_Y, LANE_Z), B.shaft("x"))
    c.set((X1 + 2, DEPLOYER_Y, LANE_Z), B.gearbox("z"))  # ±X ve ±Y
    for y in range(DEPLOYER_Y + 1, DRIVE_Y):
        c.set((X1 + 2, y, LANE_Z), B.shaft("y"))
    c.set((X1 + 2, DRIVE_Y, LANE_Z), B.gearbox("z"), overwrite=True)

    # bant kasnağı -> yukarı
    c.set((BELT_X0, BELT_Y, LANE_Z - 1), B.shaft("z"))  # kasnak: bandın hemen yanı
    c.set((BELT_X0, BELT_Y, LANE_Z - 2), B.gearbox("x"))  # ±Y ve ±Z
    for y in range(BELT_Y + 1, DRIVE_Y):
        c.set((BELT_X0, y, LANE_Z - 2), B.shaft("y"))
    c.set((BELT_X0, DRIVE_Y, LANE_Z - 2), B.gearbox("x"))
    c.set((BELT_X0, DRIVE_Y, LANE_Z - 1), B.shaft("z"))
    c.set((BELT_X0, DRIVE_Y, LANE_Z), B.gearbox("y"), overwrite=True)


def _stress_budget() -> S.Budget:
    b = S.Budget("Modül 4 (modül 1'in dalından beslenir @ 64 RPM)")
    b.add_load("Deployer (montaj)", "create:deployer", STATIONS, RPM)
    return b


def build() -> Canvas:
    c = Canvas(MODULE_ID, TITLE)
    _assembly_line(c)
    _sheet_input(c)
    _output(c)
    _drive(c)

    budget = _stress_budget()
    c.manifest.stress = {"used": budget.used}
    c.note(f"{STATIONS} deployer = {LOOPS} tur x {len(SEQUENCE)} adım.")
    c.note(f"Toplam yük: {budget.used:,.0f} SU @ {RPM} RPM.")
    return c


BUDGETS = _stress_budget
