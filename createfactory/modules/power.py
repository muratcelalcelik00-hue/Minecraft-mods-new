"""
MODÜL 1 — GÜÇ (Level 18 Boiler + 18 Steam Engine + ana şaft hattı)

Tüm sayılar Create 1.21.1 kaynak kodundan doğrulanmıştır:

  * Kazan seviyesi = min(activeHeat, min(su_limiti, boyut_limiti))   [BoilerData]
      boyut_limiti = min(18, tank_blok_sayısı / 4)   -> 18 için >= 72 blok
      su_limiti    = min(18, ceil(waterSupply) / 10) -> 18 için >= 180 mB/t
      activeHeat   = blaze burner'ların toplamı (seething=2, kindled=1)
  * Motor: capacity 1024 / speedModifier 4 = 256 SU/RPM, 64 RPM'de 16.384 SU
      18 motor -> 294.912 SU @ 64 RPM
  * Boru ağı debisi = max(1, pompaRPM/2) mB/t — AĞ BAŞINA. 180 mB/t için
    tek pompa yetmez (256 RPM'de bile 128), o yüzden 3 AYRI boru ağı var.

Yerleşim (yerel koordinatlar; +X doğu, +Y yukarı, +Z güney):

    y=13 ┐
     ... │  TANK 5x5x4 = 100 blok      x:0..4  z:0..4   y:10..13
    y=10 ┘                             (doğu duvarında 18 motor)
    y= 9    blaze burner sırası (z=0 ve z=4) + deployer'lar (z=-1 ve z=5)
    y=10    su boruları / pompalar (batıda), chute'lar (yakıt)
    y=11    item vault sırası (yakıt tamponu), RSC hattı
    y= 4    su çarkı bankası (batı-kuzey), bootstrap ağı

İKİ AYRI KİNETİK AĞ vardır ve bu kasıtlıdır:
  A) "bootstrap" ağı  : 10 su çarkı -> 3 pompa + 10 deployer
  B) "ana" ağ         : 18 steam engine -> fabrika omurgası

Neden ayrı? Pompalar ve yakıt deployer'ları kazanın ÇALIŞMASI için gerekli.
Onları motorlardan beslersek klasik kilitlenme oluşur: güç kesilince su ve
yakıt durur, kazan söner, motorlar bir daha çalışmaz. Su çarkları bedava ve
kendiliğinden başladığı için sistem her zaman kendi kendine toparlar.
"""

from __future__ import annotations

from .. import blocks as B
from .. import stress as S
from ..canvas import Canvas

MODULE_ID = "01_power"
TITLE = "Modül 1 — Güç: Level 18 Boiler + 18 Steam Engine"

# ---------------------------------------------------------------------------
# Yerleşim sabitleri
# ---------------------------------------------------------------------------

TANK_X0, TANK_Z0 = 0, 0
TANK_W = 5  # 5x5 taban
TANK_Y0, TANK_H = 10, 4  # y=10..13
TANK_BLOCKS = TANK_W * TANK_W * TANK_H  # 100 (>= 72 -> boyut limiti 18)

BURNER_Y = TANK_Y0 - 1  # 9 — kazan tabanının hemen altı
BURNER_ROWS_Z = (TANK_Z0, TANK_Z0 + TANK_W - 1)  # z=0 (kuzey) ve z=4 (güney)

ENGINE_X = TANK_X0 + TANK_W  # 5 — tankın doğu duvarı
ENGINE_SHAFT_X = ENGINE_X + 2  # 7 — motor + 2 blok (SteamEngineBlock.getShaftPos)
ENGINE_COG_Z = TANK_Z0 + TANK_W  # 5 — dikey dişli kolonu
ENGINE_COUNT = 18

BUS_Y = TANK_Y0  # 10
BUS_X = ENGINE_SHAFT_X  # 7
BUS_Z0 = ENGINE_COG_Z + 1  # 6
BRANCHES = 6  # modül 2..7 için
BRANCH_STEP = 2

# Su tarafı
POOL_X = (-8, -6)  # 3 blok geniş havuz
POOL_Y = TANK_Y0  # 10 — borularla aynı seviye
PIPE_LANES_Z = (0, 2, 4)  # 3 AYRI ağ; aralarında 1 blok boşluk şart
PUMP_X = -2
PUMP_RPM = 128  # -> ağ başına 64 mB/t, 3 ağ = 192 mB/t (>= 180)
RSC_TARGET_RPM = PUMP_RPM // 2  # RSC -> large cog -> small cog (x2) -> pompa

# Su çarkı bankası
WHEEL_Y = 4
WHEEL_Z = -8
WHEEL_X0, WHEEL_COUNT = -20, 10
TOWER_X = -3  # dikey dişli kulesi
SPINE_X = -2  # bootstrap dağıtım hattı

# Yakıt hatları
LANES = (
    # (deployer z, deployer'ın baktığı yön, funnel yönü)
    (BURNER_ROWS_Z[0] - 1, "south", "north"),  # kuzey hattı: z=-1
    (BURNER_ROWS_Z[1] + 1, "north", "south"),  # güney hattı: z=5
)
BURNERS_PER_ROW = TANK_W  # 5
BURNER_COUNT = BURNERS_PER_ROW * 2  # 10 seething = 20 ısı (>= 18)


# ---------------------------------------------------------------------------
# Alt bölümler
# ---------------------------------------------------------------------------


def _boiler(c: Canvas) -> None:
    """5x5x4 fluid tank + altında blaze burner sıraları."""
    for i in range(TANK_H):
        y = TANK_Y0 + i
        for x in range(TANK_X0, TANK_X0 + TANK_W):
            for z in range(TANK_Z0, TANK_Z0 + TANK_W):
                c.set(
                    (x, y, z),
                    B.fluid_tank(top=(i == TANK_H - 1), bottom=(i == 0), shape="plain"),
                )

    for z in BURNER_ROWS_Z:
        for x in range(TANK_X0, TANK_X0 + TANK_W):
            c.set((x, BURNER_Y, z), B.blaze_burner("seething", facing="north"))


def _engine_bank(c: Canvas) -> None:
    """18 steam engine + her kat için şaft hattı + dikey dişli kolonu.

    Motor doğuya bakar (tanktan uzağa), şaftı 2 blok ileride (x=7) ve şaftın
    ekseni Z (motorun ekseni X olduğu için farklı olmak zorunda).
    Aradaki x=6 kolonu BOŞ kalmalı.
    """
    slots = []
    for y in range(TANK_Y0, TANK_Y0 + TANK_H):
        for z in range(TANK_Z0, TANK_Z0 + TANK_W):
            slots.append((y, z))
    slots = slots[:ENGINE_COUNT]

    for y, z in slots:
        c.set((ENGINE_X, y, z), B.steam_engine(facing="east", face="wall"))

    # her katta z=0..4 şaft + z=5 dişli (dişliler dikeyde birbirine kavrar)
    for y in range(TANK_Y0, TANK_Y0 + TANK_H):
        for z in range(TANK_Z0, TANK_Z0 + TANK_W):
            c.set((ENGINE_SHAFT_X, y, z), B.shaft("z"))
        c.set((ENGINE_SHAFT_X, y, ENGINE_COG_Z), B.cog("z"))

    c.note(
        f"{ENGINE_COUNT} motor: y={TANK_Y0}..{TANK_Y0 + TANK_H - 1} katlarında, "
        f"x={ENGINE_X} duvarında. Şaftlar x={ENGINE_SHAFT_X}, x={ENGINE_X + 1} kolonu boş."
    )


def _main_bus(c: Canvas) -> None:
    """Ana şaft hattı + modül başına clutch & gearshift."""
    last_z = BUS_Z0 + BRANCH_STEP * BRANCHES
    for z in range(BUS_Z0, last_z + 1):
        c.set((BUS_X, BUS_Y, z), B.shaft("z"))

    for i in range(BRANCHES):
        z = BUS_Z0 + 1 + BRANCH_STEP * i
        # gearbox (axis=y) Z hattını sürdürür ve X'e dal verir
        c.set((BUS_X, BUS_Y, z), B.gearbox("y"), overwrite=True)
        c.set((BUS_X + 1, BUS_Y, z), B.clutch("x"))
        c.set((BUS_X + 2, BUS_Y, z), B.gearshift("x"))
        c.set((BUS_X + 3, BUS_Y, z), B.shaft("x"))
        c.io(
            f"modül-{i + 2} güç çıkışı",
            (BUS_X + 3, BUS_Y, z),
            "rotation-out",
            f"64 RPM. Clutch x={BUS_X + 1}, gearshift x={BUS_X + 2} (ikisi de z={z}).",
        )


def _fuel_lanes(c: Canvas) -> None:
    """Her burner sırası için: deployer + chute + item vault tamponu.

    Zincir: item vault (üst) -> chute (aşağı iter) -> deployer -> blaze burner.
    Chute güç istemez, üstündeki envanterden çeker altındakine iter.
    Vault'lar aynı eksende bitişik olduğu için TEK envanter oluşturur; bu
    yüzden hat başına tek bir yakıt giriş noktası yeterli.
    """
    for lane_i, (z_dep, dep_facing, funnel_facing) in enumerate(LANES):
        for x in range(TANK_X0, TANK_X0 + TANK_W):
            # facing ekseni Z -> axis_along_first=true => dönme ekseni X
            # (böylece sıradaki deployer'lar birbirine şaft gibi bağlanır)
            c.set((x, BURNER_Y, z_dep), B.deployer(dep_facing, axis_along_first=True))
            c.set((x, TANK_Y0, z_dep), B.chute("down"))
            c.set((x, TANK_Y0 + 1, z_dep), B.item_vault("x"))

        # yakıt giriş hunisi: vault sırasının üstüne (yukarıdan item kabul eder)
        fx = TANK_X0 + TANK_W // 2
        c.set((fx, TANK_Y0 + 2, z_dep), B.andesite_funnel("up", extracting=False))
        c.io(
            f"yakıt girişi #{lane_i + 1}",
            (fx, TANK_Y0 + 2, z_dep),
            "item-in",
            "Blaze cake (seething=2 ısı) ya da kömür/odun kömürü (kindled=1 ısı). "
            "Yukarıdan besleyin; vault sırası tüm deployer'lara dağıtır.",
        )


def _water_supply(c: Canvas) -> None:
    """Havuz -> 3 ayrı boru ağı -> 3 pompa -> kazan.

    Açık uçlu boru yalnız KAYNAK bloğu çeker (OpenEndedPipe: fluidState.isSource()).
    Havuz 3x5 kaynak olduğu için her çekilen blok komşularından anında yenilenir
    (vanilla sonsuz su kuralı).
    """
    # havuz teknesi
    c.fill((POOL_X[0] - 1, POOL_Y - 1, -1), (-5, POOL_Y - 1, TANK_Z0 + TANK_W), B.STONE)
    c.fill((POOL_X[0] - 1, POOL_Y, -1), (POOL_X[1], POOL_Y, -1), B.STONE)
    c.fill(
        (POOL_X[0] - 1, POOL_Y, TANK_Z0 + TANK_W),
        (POOL_X[1], POOL_Y, TANK_Z0 + TANK_W),
        B.STONE,
    )
    c.fill((POOL_X[0] - 1, POOL_Y, 0), (POOL_X[0] - 1, POOL_Y, 4), B.STONE)
    c.fill((POOL_X[0], POOL_Y, 0), (POOL_X[1], POOL_Y, 4), B.WATER)

    # boru hatları arasındaki tıkaçlar (su doğuya kaçmasın + hatlar ayrı kalsın)
    for z in (1, 3):
        c.set((-5, POOL_Y, z), B.STONE)

    for z in PIPE_LANES_Z:
        c.set((-5, POOL_Y, z), B.fluid_pipe(west=True, east=True))  # açık uç: batı
        c.set((-4, POOL_Y, z), B.fluid_pipe(west=True, east=True))
        c.set((-3, POOL_Y, z), B.fluid_pipe(west=True, east=True))
        c.set((PUMP_X, POOL_Y, z), B.mechanical_pump("east"))
        c.set((-1, POOL_Y, z), B.fluid_pipe(west=True, east=True))  # doğu ucu = tank

    # pompaları birbirine bağlayan dişliler (pompa ICogWheel'dir, kavrar)
    for z in (1, 3):
        c.set((PUMP_X, POOL_Y, z), B.cog("x"))

    # RSC katı: large cog RSC'nin TAM ÜSTÜNDE, eksenleri farklı olmalı
    c.set((PUMP_X, POOL_Y + 1, 3), B.cog("x"))  # large cog ile çapraz kavrar (x2)
    c.set((PUMP_X, POOL_Y + 2, 2), B.large_cog("x"))
    c.set((PUMP_X, POOL_Y + 1, 2), B.speed_controller("z", RSC_TARGET_RPM))

    c.io(
        "su alışı",
        (-5, POOL_Y, PIPE_LANES_Z[0]),
        "fluid-in",
        "Havuz kendi kendine yenilenir; dışarıdan su gerekmez.",
    )


def _bootstrap_drive(c: Canvas) -> None:
    """Su çarkı bankası + dikey dişli kulesi + dağıtım hattı."""
    # --- su çarkları: aynı eksende yan yana -> tek mil
    for i in range(WHEEL_COUNT):
        x = WHEEL_X0 + i
        c.set((x, WHEEL_Y, WHEEL_Z), B.water_wheel("west"))
        c.set((x, WHEEL_Y - 1, WHEEL_Z), B.STONE)  # çarkın altı kapalı (su girmesin)
        c.set((x, WHEEL_Y + 1, WHEEL_Z + 1), B.WATER)  # kaynak sırası
        c.set((x, WHEEL_Y, WHEEL_Z + 1), B.STONE)  # kaynakların tabanı
        c.set((x, WHEEL_Y + 1, WHEEL_Z + 2), B.STONE)  # arka duvar
        c.fill((x, 0, WHEEL_Z), (x, WHEEL_Y - 2, WHEEL_Z), B.STONE)

    # havuz teknesi: düşen su burada toplanır ve dışarı taşmaz
    wx0, wx1 = WHEEL_X0 - 1, WHEEL_X0 + WHEEL_COUNT
    c.fill((wx0, 0, WHEEL_Z - 3), (wx1, 0, WHEEL_Z - 1), B.STONE)
    c.fill((wx0, 0, WHEEL_Z - 3), (wx0, WHEEL_Y + 1, WHEEL_Z - 1), B.STONE)
    c.fill((wx1, 0, WHEEL_Z - 3), (wx1, WHEEL_Y + 1, WHEEL_Z - 1), B.STONE)
    c.fill((wx0, 0, WHEEL_Z - 3), (wx1, WHEEL_Y + 1, WHEEL_Z - 3), B.STONE)
    c.set((wx0, WHEEL_Y, WHEEL_Z), B.STONE)
    # kaynak sırasının ve çark üstündeki akan suyun uç kapakları:
    # bunlar olmadan su, çark sırasının ucundan taşıp şaft hattı boyunca akar
    for wx in (wx0, wx1):
        c.set((wx, WHEEL_Y + 1, WHEEL_Z + 1), B.STONE)
        c.set((wx, WHEEL_Y + 1, WHEEL_Z), B.STONE)

    # --- çark milinden doğuya şaft, sonra dikey dişli kulesi
    x_from = WHEEL_X0 + WHEEL_COUNT
    for x in range(x_from, TOWER_X):
        c.set((x, WHEEL_Y, WHEEL_Z), B.shaft("x"))
    for y in range(WHEEL_Y, POOL_Y + 2):
        c.set((TOWER_X, y, WHEEL_Z), B.cog("x"))

    # --- deployer besleme hattı (y=9) : gearbox X<->Z dönüşleri
    c.set((SPINE_X, BURNER_Y, WHEEL_Z), B.gearbox("y"))
    for z in range(WHEEL_Z + 1, LANES[1][0]):
        c.set((SPINE_X, BURNER_Y, z), B.shaft("z"))
    for z_dep, _, _ in LANES:
        # gearbox hem Z hattını sürdürür hem de +X'e (deployer sırasına) dal verir
        c.set((SPINE_X, BURNER_Y, z_dep), B.gearbox("y"), overwrite=True)
        c.set((SPINE_X + 1, BURNER_Y, z_dep), B.shaft("x"))

    # --- RSC besleme hattı (y=11)
    c.set((SPINE_X, POOL_Y + 1, WHEEL_Z), B.gearbox("y"))
    for z in range(WHEEL_Z + 1, 2):
        c.set((SPINE_X, POOL_Y + 1, z), B.shaft("z"))


def _clearances(c: Canvas) -> None:
    """İşlevsel olarak BOŞ kalması gereken yerlere açıkça hava yazar.

    `//paste -a` zaten havayı atlar, ama düz olmayan araziye basarken ya da
    Create'in Schematicannon'u ile basarken bu bloklar dolu kalırsa yapı
    çalışmaz: motorun gövdesi taşacak yer ve suyun akıp düşeceği kolon.
    """
    for y in range(TANK_Y0, TANK_Y0 + TANK_H):
        for z in range(TANK_Z0, TANK_Z0 + TANK_W):
            c.set((ENGINE_X + 1, y, z), B.AIR)

    for i in range(WHEEL_COUNT):
        x = WHEEL_X0 + i
        c.set((x, WHEEL_Y + 1, WHEEL_Z), B.AIR)  # çarkın üstünden akan su
        for y in range(1, WHEEL_Y + 2):
            c.set((x, y, WHEEL_Z - 1), B.AIR)  # düşen su kolonu


def _stress_budget() -> tuple[S.Budget, S.Budget]:
    boot = S.Budget("Bootstrap ağı (su çarkları @ 8 RPM)")
    boot.add_source("Su çarkı", "create:water_wheel", WHEEL_COUNT)
    boot.add_load("Mekanik pompa", "create:mechanical_pump", len(PIPE_LANES_Z), PUMP_RPM)
    boot.add_load("Deployer (yakıt)", "create:deployer", BURNER_COUNT, 8)
    boot.check()

    main = S.Budget("Ana ağ (steam engine bankası @ 64 RPM)")
    main.add_source("Steam engine", "create:steam_engine", ENGINE_COUNT)
    main.check()
    return boot, main


# ---------------------------------------------------------------------------
# Giriş noktası
# ---------------------------------------------------------------------------


def build() -> Canvas:
    c = Canvas(MODULE_ID, TITLE)

    _boiler(c)
    _engine_bank(c)
    _main_bus(c)
    _fuel_lanes(c)
    _water_supply(c)
    _bootstrap_drive(c)
    _clearances(c)

    boot, main = _stress_budget()
    c.manifest.stress = {
        "bootstrap_capacity": boot.capacity,
        "bootstrap_used": boot.used,
        "main_capacity": main.capacity,
        "main_used": main.used,
    }
    c.manifest.notes.insert(
        0,
        f"Kazan: {TANK_BLOCKS} tank bloğu (limit {TANK_BLOCKS // 4}, tavan 18), "
        f"{BURNER_COUNT} seething burner = {BURNER_COUNT * 2} ısı, "
        f"su {len(PIPE_LANES_Z)} x {S.pump_throughput(PUMP_RPM)} = "
        f"{len(PIPE_LANES_Z) * S.pump_throughput(PUMP_RPM)} mB/t "
        f"(gereken {S.water_needed()} mB/t) -> Level 18.",
    )
    c.note(
        f"Ana ağ kapasitesi: {main.capacity:,.0f} SU @ 64 RPM "
        f"({ENGINE_COUNT} motor x 16.384 SU)."
    )
    c.note(
        f"Bootstrap ağı: {boot.used:,.0f} / {boot.capacity:,.0f} SU "
        f"({boot.headroom_pct:.0f}% boş)."
    )
    return c


BUDGETS = _stress_budget
