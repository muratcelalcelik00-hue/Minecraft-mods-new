"""
MODÜL 5 — DEPOLAMA + SIRALAMA

Modül 2/3/4'ün karışık çıktısını tek bir bant üzerinde tür tür ayırıp
kendi vault sütununa koyar.

Neden brass tunnel değil, filtreli brass funnel?
    Brass tunnel'ın asıl işi PARALEL bantlar arasında dağıtım yapmaktır ve
    çalışması için her yüz başına ayrı filtre + bir de mod (split / forced
    split / round robin / prefer nearest / randomize / synchronize) NBT'si
    ister. Buradaki iş "bir bant, çok hedef" olduğu için filtreli
    **brass belt funnel** hem daha basit hem de tek NBT alanıyla
    (`{Filter:{id:...,count:1}}`) tam olarak istenen davranışı veriyor:
    bandın üstünden yalnız filtresine uyanı çeker, gerisi altından geçer.

Sıralanan türler ve id'leri (hepsi tag dosyalarından/tariflerden doğrulandı):
    create:precision_mechanism, create:brass_ingot, create:andesite_alloy,
    minecraft:iron_ingot, minecraft:copper_ingot, create:zinc_ingot,
    minecraft:iron_nugget, minecraft:redstone, create:experience_nugget
Eşleşmeyen her şey bandın ucundaki taşma vault'una gider.
"""

from __future__ import annotations

from .. import blocks as B
from .. import stress as S
from ..canvas import Canvas

MODULE_ID = "05_storage"
TITLE = "Modül 5 — Depolama + sıralama"

RPM = 64
LANE_Z = 2
BELT_Y = 10
FUNNEL_Y = BELT_Y + 1
VAULT_Z = LANE_Z - 1  # vault sütunları bandın kuzeyinde
VAULT_HEIGHT = 3
DRIVE_Y = 15

#: (filtre item'i, insan-okur ad)
FILTERS = [
    ("create:precision_mechanism", "precision mechanism"),
    ("create:brass_ingot", "brass ingot"),
    ("create:andesite_alloy", "andesite alloy"),
    ("minecraft:iron_ingot", "iron ingot"),
    ("minecraft:copper_ingot", "copper ingot"),
    ("create:zinc_ingot", "zinc ingot"),
    ("minecraft:iron_nugget", "iron nugget"),
    ("minecraft:redstone", "redstone"),
    ("create:experience_nugget", "experience nugget"),
]

IN_X = 0  # girdi (vault'lar birleşmesin diye hatlardan uzakta)
LANE_X0, LANE_STEP = 2, 2
BELT_X0 = IN_X
BELT_X1 = LANE_X0 + LANE_STEP * (len(FILTERS) - 1) + 1  # bant 20 blokta kalsın


def _sorting_line(c: Canvas) -> None:
    c.belt_run((BELT_X0, BELT_Y, LANE_Z), "east", BELT_X1 - BELT_X0 + 1)

    for i, (item, label) in enumerate(FILTERS):
        x = LANE_X0 + LANE_STEP * i
        # funnel bandın ÜSTÜNDE, kuzeyindeki vault sütununa bağlı
        # (attached = pos.relative(facing.getOpposite()) -> facing=south)
        c.set((x, FUNNEL_Y, LANE_Z), B.brass_belt_funnel("south", shape="pulling", filter_item=item))
        for dy in range(VAULT_HEIGHT):
            c.set((x, FUNNEL_Y + dy, VAULT_Z), B.item_vault("x"))
        c.io(f"{label} deposu", (x, FUNNEL_Y, VAULT_Z), "item-out", f"filtre: {item}")


def _input_output(c: Canvas) -> None:
    # girdi: vault -> belt funnel (pushing) -> bandın başı
    c.set((IN_X, FUNNEL_Y, VAULT_Z), B.item_vault("x"))
    c.set((IN_X, FUNNEL_Y, LANE_Z), B.andesite_belt_funnel("south", shape="pushing"))
    c.set((IN_X, FUNNEL_Y + 1, VAULT_Z), B.andesite_funnel("up", extracting=False))
    c.io(
        "karışık girdi",
        (IN_X, FUNNEL_Y + 1, VAULT_Z),
        "item-in",
        "Modül 2/3/4 çıkışları buraya dökülür.",
    )

    # taşma: eşleşmeyen her şey bandın ucundan
    c.set((BELT_X1 + 1, BELT_Y, LANE_Z), B.andesite_funnel("west", extracting=False))
    c.set((BELT_X1 + 2, BELT_Y, LANE_Z), B.item_vault("x"))
    c.io(
        "taşma / sınıflandırılmamış",
        (BELT_X1 + 2, BELT_Y, LANE_Z),
        "item-out",
        "Hiçbir filtreye uymayan itemler. Dolarsa yeni bir filtre hattı ekle.",
    )


def _drive(c: Canvas) -> None:
    # bant kasnağı bandın GÜNEY yanından (kuzeyde vault'lar var)
    c.set((BELT_X0, BELT_Y, LANE_Z + 1), B.shaft("z"))
    c.set((BELT_X0, BELT_Y, LANE_Z + 2), B.gearbox("x"))  # ±Y ve ±Z
    for y in range(BELT_Y + 1, DRIVE_Y):
        c.set((BELT_X0, y, LANE_Z + 2), B.shaft("y"))
    c.set((BELT_X0, DRIVE_Y, LANE_Z + 2), B.gearbox("x"))
    c.set((BELT_X0, DRIVE_Y, LANE_Z + 1), B.shaft("z"))
    c.set((BELT_X0, DRIVE_Y, LANE_Z), B.gearbox("y"), overwrite=True)

    for x in range(BELT_X0 - 2, BELT_X0):
        c.set((x, DRIVE_Y, LANE_Z), B.shaft("x"))
    c.io("güç girişi", (BELT_X0 - 2, DRIVE_Y, LANE_Z), "rotation-in", f"{RPM} RPM, eksen X.")


def build() -> Canvas:
    c = Canvas(MODULE_ID, TITLE)
    _sorting_line(c)
    _input_output(c)
    _drive(c)
    c.note(f"{len(FILTERS)} filtre hattı + taşma. Her hat {VAULT_HEIGHT} vault yüksekliğinde.")
    c.note("Tek tüketici bant; stres yükü ihmal edilebilir.")
    return c


def BUDGETS() -> S.Budget:
    return S.Budget("Modül 5 (yalnız bant döner)")
