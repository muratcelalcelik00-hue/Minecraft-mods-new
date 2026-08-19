"""
MODÜL 6 — TARIM (ağaç / bambu / şeker kamışı)

Üç paralel hat, hepsi **hareketli contraption gerektirmeden** çalışır:

    z=2   meşe ağacı   -> kütük + fidan + elma/çubuk   (kömür, tahta)
    z=6   bambu        -> yakıt, bambu tahtası, kâğıt  (kendi büyür)
    z=10  şeker kamışı -> kâğıt                        (kendi büyür)

Testere geometrisi (Create'in `mechanical_saw/breaker` ponder'ından):
    testere bitkinin **YANINDA**, ona bakar; mili **arkasından** alır.
    (`SawBlock.hasShaftTowards` yatay testerede yalnız `facing.getOpposite()`
     için true döner.)

Toplama: `SawBlockEntity.dropItemFromCutTree` düşen itemi
`breakingPos - sawPos` yönünde iter — yani **testerenin karşı tarafına**.
Bu yüzden toplama bandı bitkinin batısına, testere de doğusuna konuldu.
Bandın iki yanına yükseltilmiş kenar konarak itemlerin hattan çıkması engellenir.

Buğday neden yok: mechanical harvester yalnız **hareketli bir contraption**
üstünde çalışır (bearing/train). Contraption elle "assemble" edilmek zorunda
olduğu için "paste et ve çalışsın" kuralına uymuyor; bu yüzden bu modül
contraption'sız üç hatla sınırlı tutuldu.
"""

from __future__ import annotations

from .. import blocks as B
from .. import stress as S
from ..canvas import Canvas

MODULE_ID = "06_farm"
TITLE = "Modül 6 — Tarım: ağaç, bambu, şeker kamışı"

RPM = 64
SOIL_X = 5
SAW_X = SOIL_X + 1
SAW_SHAFT_X = SAW_X + 1
DRIVE_X = SAW_SHAFT_X + 1  # 8
BELT_X0, BELT_X1 = 0, SOIL_X - 1  # 0..4 (batıya doğru)
GROUND_Y = 0
PLANT_Y = GROUND_Y + 1

LANES = [
    ("mese_agaci", 2, B.DIRT, B.OAK_SAPLING, True),   # fidan ekimi için deployer
    ("bambu", 6, B.DIRT, B.BAMBOO, False),
    ("seker_kamisi", 10, B.SAND, B.SUGAR_CANE, False),
]


def _lane(c: Canvas, name: str, z: int, soil: str, plant: str, needs_replant: bool) -> None:
    c.set((SOIL_X, GROUND_Y, z), soil)
    c.set((SOIL_X, PLANT_Y, z), plant)

    # testere bitkiye bakar, mili arkasında
    c.set((SAW_X, PLANT_Y, z), B.mechanical_saw("west"))
    c.set((SAW_SHAFT_X, PLANT_Y, z), B.shaft("x"))

    # toplama bandı: itemler testereden uzağa (batıya) fırlatılır
    c.belt_run((BELT_X1, GROUND_Y, z), "west", BELT_X1 - BELT_X0 + 1)
    c.set((BELT_X0 - 1, GROUND_Y, z), B.andesite_funnel("east", extracting=False))
    c.set((BELT_X0 - 2, GROUND_Y, z), B.item_vault("x"))
    c.io(f"{name} çıkışı", (BELT_X0 - 2, GROUND_Y, z), "item-out", "")

    # itemler hattan çıkmasın diye kenarlıklar
    # x=4 kenarlıksız bırakılır: bant ve deployer tahrik hatları oradan geçiyor
    for x in range(BELT_X0 - 1, BELT_X1):
        for dz in (-1, 1):
            c.set((x, PLANT_Y, z + dz), B.STONE)

    if needs_replant:
        # fidanı yandan ekiyoruz: deployer'ı gövdenin üstüne koyamayız,
        # yoksa ağaç büyüyemez
        c.set((BELT_X1, PLANT_Y, z), B.deployer("east", axis_along_first=False))
        c.set((BELT_X1, PLANT_Y + 1, z), B.chute("down"))
        c.set((BELT_X1, PLANT_Y + 2, z), B.item_vault("x"))
        c.set((BELT_X1, PLANT_Y + 3, z), B.andesite_funnel("up", extracting=False))
        c.io(
            "fidan girişi",
            (BELT_X1, PLANT_Y + 3, z),
            "item-in",
            "Meşe fidanı. Ağacın kendi yaprakları fidan düşürür; modül 5 ile "
            "buraya geri yönlendirilebilir.",
        )


def _sugarcane_water(c: Canvas) -> None:
    """Şeker kamışı kumun yanında su ister."""
    z = LANES[2][1]
    c.set((SAW_X, GROUND_Y, z), B.WATER, overwrite=True)  # kumun doğusu
    for pos in ((SAW_X + 1, GROUND_Y, z), (SAW_X, GROUND_Y, z - 1),
                (SAW_X, GROUND_Y, z + 1), (SAW_X, GROUND_Y - 1, z)):
        c.set(pos, B.STONE, overwrite=True)


def _drive(c: Canvas) -> None:
    zs = [z for _, z, _, _, _ in LANES]
    z_lo, z_hi = min(zs) - 1, max(zs) + 1

    # testere hattı: x=8 boyunca Z ekseninde
    for z in range(z_lo, z_hi + 1):
        c.set((DRIVE_X, PLANT_Y, z), B.shaft("z"))
    for z in zs:
        c.set((DRIVE_X, PLANT_Y, z), B.gearbox("y"), overwrite=True)  # ±X testereye, ±Z hatta
    c.io("güç girişi", (DRIVE_X, PLANT_Y, z_lo), "rotation-in", f"{RPM} RPM, eksen Z.")

    # bant kasnakları: x=4, y=0 boyunca Z hattı.
    # Bantların start segmentleri de ±Z yönünde mil kabul ettiği için hat
    # bantların içinden geçebiliyor.
    for z in range(zs[0] + 1, z_hi + 1):
        if z not in zs:
            c.set((BELT_X1, GROUND_Y, z), B.shaft("z"))
    # deployer hattı: x=4, y=1
    for z in range(zs[0] + 1, z_hi + 1):
        if c.get((BELT_X1, PLANT_Y, z)) is None:
            c.set((BELT_X1, PLANT_Y, z), B.shaft("z"))

    # üç hattı birleştir.
    # DİKKAT: `axis=x` bir gearbox yalnız ±Y ve ±Z yüzlerine şaft verir
    # (kendi ekseni hariç), yani aynı blokla hem X hem Y hem Z'ye dallanılamaz.
    # Bu yüzden dönüş iki gearbox ile yapılıyor.
    c.set((BELT_X1, GROUND_Y, z_hi), B.gearbox("x"), overwrite=True)   # ±Y, ±Z
    c.set((BELT_X1, PLANT_Y, z_hi), B.gearbox("x"), overwrite=True)    # ±Y, ±Z
    c.set((BELT_X1, PLANT_Y, z_hi + 1), B.gearbox("y"))                # ±X, ±Z
    for x in range(BELT_X1 + 1, DRIVE_X):
        c.set((x, PLANT_Y, z_hi + 1), B.shaft("x"))
    c.set((DRIVE_X, PLANT_Y, z_hi + 1), B.gearbox("y"))                # ±X, ±Z


def _stress_budget() -> S.Budget:
    b = S.Budget("Modül 6 (modül 1'in dalından beslenir @ 64 RPM)")
    b.add_load("Mechanical saw", "create:mechanical_saw", len(LANES), RPM)
    b.add_load("Deployer (fidan)", "create:deployer", 1, RPM)
    return b


def build() -> Canvas:
    c = Canvas(MODULE_ID, TITLE)
    for name, z, soil, plant, replant in LANES:
        _lane(c, name, z, soil, plant, replant)
    _sugarcane_water(c)
    _drive(c)
    budget = _stress_budget()
    c.manifest.stress = {"used": budget.used}
    c.note(f"Toplam yük: {budget.used:,.0f} SU @ {RPM} RPM.")
    return c


BUDGETS = _stress_budget
