"""
BİRLEŞİK KOMPLEKS — 7 modül + fabrika binası

Yedi modülü tek bir şematikte birleştirir, modül 1'in altı güç dalını her
modülün güç girişine kadar döşer ve hepsini bir fabrika binasının içine alır.

Neden modül dokümanlarındaki ofsetler doğrudan kullanılmadı:
    Oradaki ofsetler her modülü KENDİ güç dalına hizalamak için hesaplanmıştı;
    modüller birbirleriyle çakışıyordu (örn. modül 2 ile modül 3'ün hacimleri
    kesişiyor). Gerçek bir yerleşimde modüller ayrı hollere konur ve güç
    onlara şaft hattıyla götürülür — burada yapılan da bu.

Güç dağıtımı:
    Modül 1'in dal çıkışları (31,10,18+2i) her biri kendi X kolonuna
    (x=33+i) çıkar, oradan Y ile modülün giriş yüksekliğine iner, Z ile
    modülün hizasına gider ve X ile modüle girer. Her dalın kendi kolonu
    olduğu için hatlar birbirine değmez.

    Köşelerde gearbox ekseni ÜÇÜNCÜ eksendir (`hasShaftTowards`:
    `face.getAxis() != AXIS`). Modül 6'da bu kural yüzünden tek gearbox'la
    üç eksene dallanılamadığı ortaya çıkmıştı; router bunu baştan doğru yapıyor.
"""

from __future__ import annotations

from .. import blocks as B
from .. import stress as S
from ..canvas import Canvas
from . import alloy, farm, mechanism, ore, power, press, storage

MODULE_ID = "00_complex"
TITLE = "Birleşik kompleks — 7 modül + fabrika binası"

#: (modül, kompleks içindeki min köşe, dal numarası)
PLACEMENT = [
    (ore, (44, 0, 0), 0),
    (alloy, (44, 0, 8), 1),
    (mechanism, (44, 0, 20), 2),
    (storage, (44, 0, 26), 3),
    (farm, (44, 0, 34), 4),
    (press, (44, 0, 50), 5),
]

BRANCH_X = 31          # modül 1'in dal çıkış şaftının x'i
BRANCH_Y = 10
BRANCH_Z0, BRANCH_STEP = 18, 2

WALL = "minecraft:deepslate_bricks"
FLOOR = "minecraft:polished_andesite"
GLASS = "minecraft:glass"
LAMP = "minecraft:shroomlight"  # ışık 15, yanmaz, fidan büyütür


def _place_modules(c: Canvas) -> dict:
    """Modülleri yerleştirir ve her birinin güç giriş noktasını döndürür."""
    inputs = {}
    for mod, offset, branch in PLACEMENT:
        sub = mod.build()
        c.merge(sub, offset, prefix=f"[{mod.MODULE_ID}] ")
        lo, _ = sub.bounds
        for p in sub.manifest.io:
            if p.kind == "rotation-in":
                inputs[mod.MODULE_ID] = (
                    (p.pos[0] - lo[0] + offset[0],
                     p.pos[1] - lo[1] + offset[1],
                     p.pos[2] - lo[2] + offset[2]),
                    branch,
                    p.note,
                )
    return inputs


def _power_routes(c: Canvas, inputs: dict) -> None:
    """Her dalı kendi modülüne kadar döşer."""
    for mod, offset, branch in PLACEMENT:
        target, _, note = inputs[mod.MODULE_ID]
        tx, ty, tz = target
        zb = BRANCH_Z0 + BRANCH_STEP * branch
        col = 33 + branch  # her dalın kendi kolonu -> hatlar birbirine değmez

        if mod is farm:
            # modül 6'nın güç girişi Z ekseninde ve modülün İÇİNDE (x=+10),
            # o yüzden kuzeyden yaklaşıyoruz
            # Z koridoru y=10'da olsaydı diğer dalların X hatlarını keserdi
            # (dal 6'nın hattı z=28'de aynı yükseklikten geçiyor), o yüzden
            # önce modülün giriş yüksekliğine iniyoruz.
            c.route_shaft([
                (BRANCH_X + 1, BRANCH_Y, zb),
                (col, BRANCH_Y, zb),
                (col, ty, zb),
                (col, ty, tz - 2),
                (tx, ty, tz - 2),
                (tx, ty, tz - 1),
            ])
        else:
            c.route_shaft([
                (BRANCH_X + 1, BRANCH_Y, zb),
                (col, BRANCH_Y, zb),
                (col, ty, zb),
                (col, ty, tz),
                (tx - 1, ty, tz),
            ])
        c.note(f"dal {branch + 1} -> {mod.MODULE_ID} güç girişi {target}")


def _building(c: Canvas) -> None:
    """Fabrika binası: taban, duvarlar, pencere kuşağı, çatı, aydınlatma."""
    lo, hi = c.bounds
    x0, z0 = lo[0] - 3, lo[2] - 3
    x1, z1 = hi[0] + 3, hi[2] + 3
    y_floor = lo[1] - 1
    y_roof = hi[1] + 3

    # taban
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            c.set_if_empty((x, y_floor, z), FLOOR)

    # duvarlar + pencere kuşağı (y_floor+3 .. y_floor+4)
    for y in range(y_floor + 1, y_roof):
        band = y_floor + 3 <= y <= y_floor + 4
        mat = GLASS if band else WALL
        for x in range(x0, x1 + 1):
            c.set_if_empty((x, y, z0), mat)
            c.set_if_empty((x, y, z1), mat)
        for z in range(z0, z1 + 1):
            c.set_if_empty((x0, y, z), mat)
            c.set_if_empty((x1, y, z), mat)

    # çatı
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            c.set_if_empty((x, y_roof, z), WALL)

    # aydınlatma: çatıdan sarkan ışık kaynakları (fidanların büyümesi için de)
    for x in range(x0 + 4, x1, 8):
        for z in range(z0 + 4, z1, 8):
            c.set_if_empty((x, y_roof - 1, z), LAMP)

    # kapı: batı duvarında 2x3 açıklık (taban seviyesinde)
    door_z = (z0 + z1) // 2
    for dz in (0, 1):
        for dy in range(1, 4):
            c.set((x0, y_floor + dy, door_z + dz), B.AIR, overwrite=True)

    c.note(f"bina: {x1 - x0 + 1} x {y_roof - y_floor + 1} x {z1 - z0 + 1}, "
           f"kapı batı duvarında z={door_z}")


def _stress_budget() -> S.Budget:
    b = S.Budget("Birleşik kompleks")
    b.add_source("Steam engine (modül 1)", "create:steam_engine", 18)
    for mod, _, _ in PLACEMENT:
        sub = mod.BUDGETS()
        for load in sub.loads:
            b.loads.append(load)
    b.check()
    return b


def build() -> Canvas:
    c = Canvas(MODULE_ID, TITLE)
    c.merge(power.build(), (0, 0, 0), prefix="[01_power] ")
    inputs = _place_modules(c)
    _power_routes(c, inputs)
    _building(c)

    budget = _stress_budget()
    c.manifest.stress = {"capacity": budget.capacity, "used": budget.used}
    c.note(f"Stres: {budget.used:,.0f} / {budget.capacity:,.0f} SU "
           f"({budget.headroom_pct:.0f}% boş)")
    return c


BUDGETS = _stress_budget
