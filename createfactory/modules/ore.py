"""
MODÜL 2 — CEVHER İŞLEME (crushing → washing → bulk smelting)

Zincir (tarifler kaynaktan doğrulandı):

    raw iron  --crushing(400t)-->  crushed raw iron  + %75 experience nugget
    crushed   --splashing------->  9 iron nugget     + %75 redstone
    crushed   --blasting-------->  ingot   (yıkanmayan parça eritilir)

Tek bant üzerinde SERİ dizilim: bant önce yıkama, sonra eritme istasyonundan
geçer. Yıkanan parça nugget'a döner ve eritme bölgesinden etkilenmeden geçer;
yıkanmayan parça eritilerek külçe olur. Böylece bandın ucuna hep metal gelir.

Fan geometrisi — AirCurrent.getFlowLimit'ten çıkan ZORUNLULUK:
    Fan YUKARI bakıp bandın altına konamaz. Bandın çarpışma kutusu tam blok
    olmadığı için akım bandın alt yüzeyinde biter ve bandın ÜSTÜNDEKİ eşyaya
    ulaşmaz. Bu yüzden fan yukarıdan aşağı bakar, katalizör fan ile bant
    arasındadır:

        y+3  encased_fan (facing=down)
        y+2  katalizör    (waterlogged demir parmaklık | yanan blaze burner)
        y+1  HAVA
        y    bant + üstündeki eşyalar

    Katalizör seçimi (AllFanProcessingTypes.isValidAt):
      - yıkama : su akışkanı -> waterlogged iron_bars; `create:fan_transparent`
                 tag'inde olduğu için akımı KESMEZ
      - eritme : lav akışkanı VEYA yanan blaze burner. Lav bu düzende altı
                 hava olduğu için akıp gider; o yüzden blaze burner kullanılır
                 (o da fan_transparent tag'inde).

Crushing wheel çifti (CrushingWheelBlock.updateControllers):
    İki çark aynı eksende, aralarında 1 blok boşlukla. Boşlukta controller
    KENDİLİĞİNDEN oluşur (şematikte orası hava). Çarklar TERS yönde dönmek
    zorunda; aynı eksenli dişli ızgarası iki taraflı olduğu için bu yalnız
    dişliyle sağlanamaz, o yüzden bir çarkın miline kalıcı olarak beslenen
    (yanında redstone bloğu olan) bir GEARSHIFT konur.
"""

from __future__ import annotations

from .. import blocks as B
from .. import stress as S
from ..canvas import Canvas

MODULE_ID = "02_ore"
TITLE = "Modül 2 — Cevher işleme: crushing → washing → bulk smelting"

RPM = 64  # modül 1'in ana hattı bu hızda

# --- ana eksenler ---------------------------------------------------------
LANE_Z = 2  # her şey bu Z hattında
BELT_Y = 10
BELT_X0, BELT_X1 = 3, 22
DRIVE_Y = 17  # ana tahrik hattı (fanların üstünden geçer)

# --- istasyon konumları ---------------------------------------------------
CRUSH_X = 6  # çark çiftinin ortası (controller burada oluşur)
CRUSH_Y = 12
WASH_X = 12
BLAST_X = 17
FAN_Y = CRUSH_Y + 1  # 13
CATALYST_Y = CRUSH_Y  # 12


def _drive_line(c: Canvas) -> None:
    """Ana tahrik hattı: y=DRIVE_Y, z=LANE_Z, eksen X."""
    for x in range(0, BLAST_X + 1):
        c.set((x, DRIVE_Y, LANE_Z), B.shaft("x"))
    c.io(
        "güç girişi",
        (0, DRIVE_Y, LANE_Z),
        "rotation-in",
        f"{RPM} RPM. Modül 1'in dal çıkışına (clutch+gearshift sonrası) hizalanır.",
    )


def _belt(c: Canvas) -> None:
    c.belt_run((BELT_X0, BELT_Y, LANE_Z), "east", BELT_X1 - BELT_X0 + 1)

    # bant tahriki: başlangıç segmentinin ±Z yüzüne eksen-Z şaft
    c.set((BELT_X0, BELT_Y, LANE_Z - 1), B.shaft("z"))
    c.set((BELT_X0, BELT_Y, LANE_Z - 2), B.gearbox("x"))  # ±Y ve ±Z
    for y in range(BELT_Y + 1, DRIVE_Y):
        c.set((BELT_X0, y, LANE_Z - 2), B.shaft("y"))
    c.set((BELT_X0, DRIVE_Y, LANE_Z - 2), B.gearbox("x"))
    c.set((BELT_X0, DRIVE_Y, LANE_Z - 1), B.shaft("z"))
    c.set((BELT_X0, DRIVE_Y, LANE_Z), B.gearbox("y"), overwrite=True)  # ±X hat, ±Z dal

    # çıkış: bandın ucu funnel'a iter, funnel vault'a
    c.set((BELT_X1 + 1, BELT_Y, LANE_Z), B.andesite_funnel("west", extracting=False))
    c.set((BELT_X1 + 2, BELT_Y, LANE_Z), B.item_vault("x"))
    c.io(
        "ürün çıkışı",
        (BELT_X1 + 2, BELT_Y, LANE_Z),
        "item-out",
        "iron nugget / redstone / külçe. Vault sırası modül 5'e uzatılabilir.",
    )


def _crusher(c: Canvas) -> None:
    """Crushing wheel çifti + tahriki + girdi tamponu."""
    # çarklar: eksen X, aralarında 1 blok (controller orada oluşacak)
    c.set((CRUSH_X, CRUSH_Y, LANE_Z - 1), B.crushing_wheel("x"))
    c.set((CRUSH_X, CRUSH_Y, LANE_Z + 1), B.crushing_wheel("x"))
    c.set((CRUSH_X, CRUSH_Y, LANE_Z), B.AIR)  # controller kendiliğinden oluşur
    c.set((CRUSH_X, CRUSH_Y - 1, LANE_Z), B.AIR)  # ürün buradan bandın üstüne düşer

    # A çarkı düz milden, B çarkı redstone ile kalıcı beslenen gearshift'ten
    # -> ikisi TERS yönde döner (crushing wheel'ın çalışma şartı)
    c.set((CRUSH_X - 1, CRUSH_Y, LANE_Z - 1), B.shaft("x"))
    c.set((CRUSH_X - 1, CRUSH_Y, LANE_Z + 1), B.gearshift("x", powered=True))
    c.set((CRUSH_X - 1, CRUSH_Y + 1, LANE_Z + 1), B.REDSTONE_BLOCK)

    # üç dişli: ortadaki tahrik alır, iki yana kavrar (her kavrama yönü çevirir)
    for dz in (-1, 0, 1):
        c.set((CRUSH_X - 2, CRUSH_Y, LANE_Z + dz), B.cog("x"))

    # tahrik: ana hattan aşağı
    c.set((CRUSH_X - 3, CRUSH_Y, LANE_Z), B.shaft("x"))
    c.set((CRUSH_X - 4, CRUSH_Y, LANE_Z), B.gearbox("z"))  # ±X ve ±Y
    for y in range(CRUSH_Y + 1, DRIVE_Y):
        c.set((CRUSH_X - 4, y, LANE_Z), B.shaft("y"))
    c.set((CRUSH_X - 4, DRIVE_Y, LANE_Z), B.gearbox("z"), overwrite=True)

    # girdi: vault -> chute -> crushing wheel controller
    c.set((CRUSH_X, CRUSH_Y + 1, LANE_Z), B.chute("down"))
    c.set((CRUSH_X, CRUSH_Y + 2, LANE_Z), B.item_vault("x"))
    c.set((CRUSH_X, CRUSH_Y + 3, LANE_Z), B.andesite_funnel("up", extracting=False))
    c.io(
        "hammadde girişi",
        (CRUSH_X, CRUSH_Y + 3, LANE_Z),
        "item-in",
        "Raw iron / raw copper / raw gold / raw zinc. Yukarıdan besleyin.",
    )


def _fan_station(c: Canvas, x: int, catalyst: str) -> None:
    """Fan yukarıdan aşağı bakar, katalizör fan ile bandın arasındadır."""
    c.set((x, FAN_Y, LANE_Z), B.encased_fan("down"))
    c.set((x, CATALYST_Y, LANE_Z), catalyst)
    c.set((x, CATALYST_Y - 1, LANE_Z), B.AIR)  # akımın bandı görmesi için boş

    # fanın dönme ekseni Y -> mili ÜSTTEN gelir
    for y in range(FAN_Y + 1, DRIVE_Y):
        c.set((x, y, LANE_Z), B.shaft("y"))
    c.set((x, DRIVE_Y, LANE_Z), B.gearbox("z"), overwrite=True)  # ±X hat, ±Y aşağı


def _blast_burner_feed(c: Canvas) -> None:
    """Eritme katalizörü olan blaze burner'ı yakıtla besleyen deployer."""
    x = BLAST_X - 1
    c.set((x, CATALYST_Y, LANE_Z), B.deployer("east", axis_along_first=False))
    c.set((x, CATALYST_Y + 1, LANE_Z), B.chute("down"))
    c.set((x, CATALYST_Y + 2, LANE_Z), B.item_vault("x"))
    c.set((x, CATALYST_Y + 3, LANE_Z), B.andesite_funnel("up", extracting=False))
    c.io(
        "eritme yakıtı",
        (x, CATALYST_Y + 3, LANE_Z),
        "item-in",
        "Kömür / odun kömürü yeter (blasting için burner'ın yanıyor olması "
        "kâfi: heat >= FADING). Blaze cake da olur.",
    )

    # deployer: facing=east (eksen X), axis_along_first=false -> dönme ekseni Z
    c.set((x, CATALYST_Y, LANE_Z - 1), B.shaft("z"))
    c.set((x, CATALYST_Y, LANE_Z - 2), B.gearbox("x"))  # ±Y ve ±Z
    for y in range(CATALYST_Y + 1, DRIVE_Y):
        c.set((x, y, LANE_Z - 2), B.shaft("y"))
    c.set((x, DRIVE_Y, LANE_Z - 2), B.gearbox("x"))
    c.set((x, DRIVE_Y, LANE_Z - 1), B.shaft("z"))
    c.set((x, DRIVE_Y, LANE_Z), B.gearbox("y"), overwrite=True)


def _stress_budget() -> S.Budget:
    b = S.Budget("Modül 2 (modül 1'in dalından beslenir @ 64 RPM)")
    b.add_load("Crushing wheel", "create:crushing_wheel", 2, RPM)
    b.add_load("Encased fan", "create:encased_fan", 2, RPM)
    b.add_load("Deployer (yakıt)", "create:deployer", 1, RPM)
    return b


def build() -> Canvas:
    c = Canvas(MODULE_ID, TITLE)
    _drive_line(c)
    _belt(c)
    _crusher(c)
    _fan_station(c, WASH_X, "minecraft:iron_bars[east=false,north=false,south=false,waterlogged=true,west=false]")
    _fan_station(c, BLAST_X, B.blaze_burner("kindled", facing="north"))
    _blast_burner_feed(c)

    budget = _stress_budget()
    c.manifest.stress = {"used": budget.used}
    c.note(f"Toplam yük: {budget.used:,.0f} SU @ {RPM} RPM.")
    c.note(
        "Seri hat: bant önce yıkama (12), sonra eritme (17) istasyonundan geçer. "
        "Yıkanan parça nugget olur ve eritmeden etkilenmez."
    )
    return c


BUDGETS = _stress_budget
