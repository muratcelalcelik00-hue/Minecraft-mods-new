"""
Şematik doğrulayıcı.

Create'in gerçek bağlantı kurallarını (RotationPropagator, SteamEngineBlock,
BoilerData, FluidPropagator) yeniden uygulayıp üretilen yapının oyunda
çalışıp çalışmayacağını paste etmeden kontrol eder.

Yakaladığı hatalar: kopuk kinetik ağ, yanlış eksende şaft, motor-şaft
geometrisi, kazan boyutu/ısısı, yanlışlıkla birleşmiş boru ağları, dolu
kalması gereken motor boşluğu, vb.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict, deque

Pos = tuple[int, int, int]

DIRS: dict[str, Pos] = {
    "east": (1, 0, 0),
    "west": (-1, 0, 0),
    "up": (0, 1, 0),
    "down": (0, -1, 0),
    "south": (0, 0, 1),
    "north": (0, 0, -1),
}
OPPOSITE = {
    "east": "west",
    "west": "east",
    "up": "down",
    "down": "up",
    "south": "north",
    "north": "south",
}
DIR_AXIS = {"east": "x", "west": "x", "up": "y", "down": "y", "south": "z", "north": "z"}

SMALL_COGS = {"create:cogwheel", "create:mechanical_pump", "create:mechanical_mixer"}
LARGE_COGS = {"create:large_cogwheel"}
#: axis property'si dönme eksenini doğrudan veren bloklar
AXIS_BLOCKS = {
    "create:shaft",
    "create:cogwheel",
    "create:large_cogwheel",
    "create:clutch",
    "create:gearshift",
    "create:powered_shaft",
    "create:crushing_wheel",
}


class Report:
    def __init__(self):
        self.errors: list[str] = []
        self.info: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def ok(self, msg: str) -> None:
        self.info.append(msg)

    @property
    def failed(self) -> bool:
        return bool(self.errors)

    def render(self) -> str:
        out = [f"  ✓ {m}" for m in self.info]
        out += [f"  ✗ {m}" for m in self.errors]
        return "\n".join(out)


# ---------------------------------------------------------------------------
# blockstate ayrıştırma
# ---------------------------------------------------------------------------

_STATE_RE = re.compile(r"^(?P<id>[a-z0-9_.:]+)(?:\[(?P<props>[^\]]*)\])?(?P<nbt>\{.*\})?$")


def parse(block: str) -> tuple[str, dict[str, str]]:
    m = _STATE_RE.match(block)
    if not m:
        raise ValueError(f"ayrıştırılamayan blok: {block!r}")
    props = {}
    if m.group("props"):
        for kv in m.group("props").split(","):
            k, _, v = kv.partition("=")
            props[k] = v
    return m.group("id"), props


class World:
    def __init__(self, blocks: dict[Pos, str]):
        self.raw = blocks
        self.parsed = {p: parse(b) for p, b in blocks.items()}

    def id_at(self, pos: Pos) -> str | None:
        e = self.parsed.get(pos)
        return e[0] if e else None

    def props_at(self, pos: Pos) -> dict[str, str]:
        e = self.parsed.get(pos)
        return e[1] if e else {}

    def is_air(self, pos: Pos) -> bool:
        return pos not in self.parsed or self.parsed[pos][0] == "minecraft:air"


# ---------------------------------------------------------------------------
# kinetik kurallar
# ---------------------------------------------------------------------------


def rotation_axis(bid: str, props: dict[str, str]) -> str | None:
    if bid in AXIS_BLOCKS:
        return props.get("axis")
    if bid == "create:gearbox":
        return None  # özel: kendi ekseni HARİÇ tüm yönlere şaft verir
    if bid == "create:mechanical_mixer":
        return "y"  # MechanicalMixerBlock.getRotationAxis -> sabit Y
    if bid == "create:belt":
        # bandın kasnak ekseni, bandın gidiş yönüne DİK yatay eksendir
        return "z" if DIR_AXIS[props["facing"]] == "x" else "x"
    if bid == "create:mechanical_saw":
        # yatay testere: dönme ekseni = facing ekseni
        return DIR_AXIS[props["facing"]]
    if bid == "create:mechanical_press":
        return DIR_AXIS[props["facing"]]
    if bid in ("create:water_wheel", "create:mechanical_pump", "create:encased_fan"):
        return DIR_AXIS[props["facing"]]
    if bid == "create:deployer":
        facing_axis = DIR_AXIS[props["facing"]]
        along_first = props.get("axis_along_first") == "true"
        table = {
            "x": ("y", "z"),
            "y": ("x", "z"),
            "z": ("x", "y"),
        }[facing_axis]
        return table[0] if along_first else table[1]
    if bid == "create:rotation_speed_controller":
        return props.get("axis")
    return None


def is_kinetic(bid: str) -> bool:
    return bid in AXIS_BLOCKS or bid in {
        "create:gearbox",
        "create:water_wheel",
        "create:mechanical_pump",
        "create:deployer",
        "create:rotation_speed_controller",
        "create:steam_engine",
        "create:encased_fan",
        "create:mechanical_mixer",
        "create:belt",
        "create:mechanical_saw",
        "create:mechanical_press",
    }


def has_shaft_towards(w: World, pos: Pos, direction: str) -> bool:
    bid, props = w.parsed[pos]
    if bid == "create:steam_engine":
        return False  # motor şaftı 2 blok ileride, doğrudan bağlanmaz
    if bid == "create:mechanical_mixer":
        return False  # hasShaftTowards her yön için false
    if bid == "create:belt":
        # yalnız kasnaklı segmentlere (start/end/pulley) şaft takılır;
        # iki ucuna şaft takılan bir bant, şaftları 1:1 birbirine bağlar
        if props.get("part") not in ("start", "end", "pulley"):
            return False
        return DIR_AXIS[direction] == rotation_axis(bid, props)
    if bid == "create:mechanical_saw":
        # yatay testereye mil YALNIZ arkadan takılır
        return direction == OPPOSITE[props["facing"]]
    if bid == "create:gearbox":
        return DIR_AXIS[direction] != props["axis"]
    axis = rotation_axis(bid, props)
    return axis is not None and DIR_AXIS[direction] == axis


def kinetic_edges(w: World, ratios: dict | None = None, signs: dict | None = None) -> dict[Pos, set[Pos]]:
    """Create'in bağlantı kurallarına göre kinetik komşuluk grafiği.

    `ratios` verilirse (a,b) -> hız çarpanı (mutlak değer) da doldurulur;
    RSC -> large cog bağlantısı için ("set", hedef_rpm) yazılır.
    """
    g: dict[Pos, set[Pos]] = defaultdict(set)
    nodes = [p for p, (bid, _) in w.parsed.items() if is_kinetic(bid)]

    def link(a: Pos, b: Pos, factor=1.0, inverse=None, sign=1) -> None:
        g[a].add(b)
        g[b].add(a)
        if signs is not None:
            signs[(a, b)] = sign
            signs[(b, a)] = sign
        if ratios is not None:
            ratios[(a, b)] = factor
            ratios[(b, a)] = inverse if inverse is not None else (
                1.0 / factor if isinstance(factor, float) else factor
            )

    for a in nodes:
        bid_a, props_a = w.parsed[a]
        axis_a = rotation_axis(bid_a, props_a)

        # 1) eksen (şaft) bağlantısı
        for d, off in DIRS.items():
            b = (a[0] + off[0], a[1] + off[1], a[2] + off[2])
            if b in w.parsed and is_kinetic(w.id_at(b)):
                if has_shaft_towards(w, a, d) and has_shaft_towards(w, b, OPPOSITE[d]):
                    link(a, b)

        # 1b) bant zinciri: bir bandın tüm segmentleri tek parça döner.
        #     (Kinetik bağlantı kasnaktan gelir, ama zincirin tamamı aynı
        #      hızda ve yönde hareket eder.)
        if bid_a == "create:belt":
            fa = props_a["facing"]
            for d in (fa, OPPOSITE[fa]):
                off = DIRS[d]
                b = (a[0] + off[0], a[1] + off[1], a[2] + off[2])
                if w.id_at(b) == "create:belt" and w.props_at(b).get("facing") == fa:
                    link(a, b)

        # 2) küçük dişli <-> küçük dişli (manhattan 1, aynı eksen, yön != eksen)
        if bid_a in SMALL_COGS:
            for d, off in DIRS.items():
                b = (a[0] + off[0], a[1] + off[1], a[2] + off[2])
                if w.id_at(b) in SMALL_COGS:
                    if rotation_axis(*w.parsed[b]) == axis_a and DIR_AXIS[d] != axis_a:
                        link(a, b, 1.0, sign=-1)

        # 3) büyük dişli <-> küçük dişli (aynı eksen, ortak eksende 0, diğer
        #    iki eksende +-1 -> çapraz)
        if bid_a in LARGE_COGS:
            for dy in (-1, 1):
                for dz in (-1, 1):
                    offs = {
                        "x": (0, dy, dz),
                        "y": (dy, 0, dz),
                        "z": (dy, dz, 0),
                    }[axis_a]
                    b = (a[0] + offs[0], a[1] + offs[1], a[2] + offs[2])
                    if w.id_at(b) in SMALL_COGS and rotation_axis(*w.parsed[b]) == axis_a:
                        link(a, b, 2.0, sign=-1)  # büyük -> küçük: hız x2, yön ters

        # 4) RSC <-> tam üstündeki büyük dişli
        if bid_a == "create:rotation_speed_controller":
            b = (a[0], a[1] + 1, a[2])
            if w.id_at(b) in LARGE_COGS:
                cog_axis = rotation_axis(*w.parsed[b])
                if cog_axis in ("x", "z") and cog_axis != axis_a:
                    target = float(re.search(r"ScrollValue:(-?\d+)", w.raw[a]).group(1))
                    link(a, b, ("set", abs(target)), inverse=("set", None))
    return g


def components(g: dict[Pos, set[Pos]], nodes: list[Pos]) -> list[set[Pos]]:
    seen: set[Pos] = set()
    out = []
    for n in nodes:
        if n in seen:
            continue
        comp = set()
        q = deque([n])
        seen.add(n)
        while q:
            cur = q.popleft()
            comp.add(cur)
            for nb in g.get(cur, ()):
                if nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        out.append(comp)
    return out


# ---------------------------------------------------------------------------
# akışkan kuralları
# ---------------------------------------------------------------------------

FLUID_BLOCKS = {"create:fluid_pipe", "create:mechanical_pump", "create:fluid_tank"}


def fluid_components(w: World) -> list[set[Pos]]:
    """Borular birbirine bitişikse BAĞLANIR (blockstate'e bakmadan Create
    bağlantıyı yeniden hesaplar). Tank'lar uç nokta sayılır, ağı birleştirmez.
    """
    nodes = [p for p in w.parsed if w.id_at(p) in ("create:fluid_pipe", "create:mechanical_pump")]
    g: dict[Pos, set[Pos]] = defaultdict(set)
    for a in nodes:
        for d, off in DIRS.items():
            b = (a[0] + off[0], a[1] + off[1], a[2] + off[2])
            if b in w.parsed and w.id_at(b) in ("create:fluid_pipe", "create:mechanical_pump"):
                bid_a, props_a = w.parsed[a]
                bid_b, props_b = w.parsed[b]
                # pompa yalnız kendi ekseninde akışkan geçirir
                if bid_a == "create:mechanical_pump" and DIR_AXIS[d] != DIR_AXIS[props_a["facing"]]:
                    continue
                if (
                    bid_b == "create:mechanical_pump"
                    and DIR_AXIS[d] != DIR_AXIS[props_b["facing"]]
                ):
                    continue
                g[a].add(b)
                g[b].add(a)
    return components(g, nodes)


# ---------------------------------------------------------------------------
# modüle özel kontroller
# ---------------------------------------------------------------------------


def check_boiler(w: World, rep: Report) -> int:
    tanks = [p for p in w.parsed if w.id_at(p) == "create:fluid_tank"]
    if not tanks:
        rep.error("hiç fluid_tank yok")
        return 0
    xs = {p[0] for p in tanks}
    ys = {p[1] for p in tanks}
    zs = {p[2] for p in tanks}
    width, depth, height = len(xs), len(zs), len(ys)
    if width != depth:
        rep.error(f"tank tabanı kare değil: {width}x{depth} (Create kare taban ister)")
    if len(tanks) != width * depth * height:
        rep.error(f"tank kutusu dolu değil: {len(tanks)} != {width * depth * height}")
    size_limit = min(18, len(tanks) // 4)
    if size_limit < 18:
        rep.error(f"tank boyutu yetersiz: {len(tanks)} blok -> maks ısı {size_limit} (>=72 gerekli)")
    else:
        rep.ok(f"tank {width}x{depth}x{height} = {len(tanks)} blok -> boyut limiti 18")

    # burner'lar tabanın bir altında ve taban ayak izinin İÇİNDE olmalı
    y0 = min(ys)
    heat = 0
    strays = 0
    for p, (bid, props) in w.parsed.items():
        if bid != "create:blaze_burner":
            continue
        inside = p[1] == y0 - 1 and p[0] in xs and p[2] in zs
        if not inside:
            strays += 1
            continue
        heat += {"seething": 2, "kindled": 1, "fading": 1}.get(props.get("blaze"), 0)
    if strays:
        rep.error(f"{strays} blaze burner kazan ayak izinin dışında (ısı vermez)")
    if heat < 18:
        rep.error(f"toplam ısı {heat} < 18")
    else:
        rep.ok(f"blaze burner toplam ısı = {heat} (>= 18)")
    return len(tanks)


def check_engines(w: World, rep: Report) -> int:
    engines = [p for p in w.parsed if w.id_at(p) == "create:steam_engine"]
    bad = 0
    for p in engines:
        props = w.props_at(p)
        facing = props["facing"] if props.get("face") == "wall" else (
            "up" if props.get("face") == "floor" else "down"
        )
        off = DIRS[facing]
        back = (p[0] - off[0], p[1] - off[1], p[2] - off[2])
        gap = (p[0] + off[0], p[1] + off[1], p[2] + off[2])
        shaft = (p[0] + off[0] * 2, p[1] + off[1] * 2, p[2] + off[2] * 2)
        if w.id_at(back) != "create:fluid_tank":
            rep.error(f"motor {p}: arkasında ({back}) tank yok")
            bad += 1
        if not w.is_air(gap):
            rep.error(f"motor {p}: {gap} boş olmalı (motor gövdesi oraya taşar)")
            bad += 1
        sid = w.id_at(shaft)
        if sid not in ("create:shaft", "create:cogwheel"):
            rep.error(f"motor {p}: {shaft} konumunda şaft yok ({sid})")
            bad += 1
        elif w.props_at(shaft).get("axis") == DIR_AXIS[facing]:
            rep.error(f"motor {p}: şaft ekseni motorun ekseniyle aynı, geçersiz")
            bad += 1
    if len(engines) > 18:
        rep.error(f"{len(engines)} motor > 18; fazlası verimi düşürür")
    if not bad:
        rep.ok(f"{len(engines)} steam engine geometrisi doğru (tank / boşluk / şaft)")
    return len(engines)


def check_deployers(w: World, rep: Report) -> None:
    """Deployer'ın önünde geçerli bir hedef, arkasında da besleme var mı?

    Geçerli hedefler:
      - blaze burner  (yakıtlama; modül 1/2/3)
      - bant / depot  (sequenced assembly, deploying; modül 4)
    Besleme: chute / smart chute (üstten) ya da bitişik funnel.
    """
    TARGETS = {
        "create:blaze_burner", "create:belt", "create:depot",
        # ekim yapan deployer'lar: hedef fidan/bitki konumudur
        "minecraft:oak_sapling", "minecraft:spruce_sapling", "minecraft:birch_sapling",
        "minecraft:bamboo", "minecraft:sugar_cane", "minecraft:wheat",
    }
    FEEDERS = {"create:chute", "create:smart_chute", "create:andesite_funnel",
               "create:brass_funnel", "create:andesite_belt_funnel", "create:brass_belt_funnel"}
    bad = 0
    deployers = [p for p in w.parsed if w.id_at(p) == "create:deployer"]
    for p in deployers:
        facing = w.props_at(p)["facing"]
        off = DIRS[facing]
        target = (p[0] + off[0], p[1] + off[1], p[2] + off[2])
        if w.id_at(target) not in TARGETS:
            rep.error(
                f"deployer {p} -> {target} geçerli hedef değil ({w.id_at(target)}); "
                "blaze burner / bant / depot olmalı"
            )
            bad += 1
        neighbours = [(p[0] + o[0], p[1] + o[1], p[2] + o[2]) for o in DIRS.values()]
        if not any(w.id_at(n) in FEEDERS for n in neighbours):
            rep.error(f"deployer {p}: besleyen chute/funnel yok")
            bad += 1
    if not bad and deployers:
        rep.ok(f"{len(deployers)} deployer: hedef ve besleme zinciri doğru")

    for p in [q for q in w.parsed if w.id_at(q) in ("create:chute", "create:smart_chute")]:
        above = (p[0], p[1] + 1, p[2])
        below = (p[0], p[1] - 1, p[2])
        if w.id_at(above) not in ("create:item_vault", "minecraft:barrel", "create:chute",
                                  "create:smart_chute", "minecraft:chest"):
            rep.error(f"chute {p}: üstünde çekilecek envanter yok ({w.id_at(above)})")
        if w.is_air(below):
            # crushing wheel çiftinin arasındaki boşluk geçerli hedeftir:
            # controller orada çalışma anında oluşur
            flanked = any(
                w.id_at((below[0] + o[0], below[1] + o[1], below[2] + o[2])) == "create:crushing_wheel"
                and w.id_at((below[0] - o[0], below[1] - o[1], below[2] - o[2])) == "create:crushing_wheel"
                for o in ((1, 0, 0), (0, 0, 1))
            )
            if not flanked:
                rep.error(f"chute {p}: altında hedef yok")


def check_fluid(w: World, rep: Report, expected_networks: int) -> None:
    comps = fluid_components(w)
    if len(comps) != expected_networks:
        rep.error(
            f"boru ağı sayısı {len(comps)}, beklenen {expected_networks} "
            "(bitişik borular birleşir -> debi düşer)"
        )
    else:
        rep.ok(f"{len(comps)} bağımsız boru ağı (her biri kendi pompasıyla)")

    for comp in comps:
        pumps = [p for p in comp if w.id_at(p) == "create:mechanical_pump"]
        if len(pumps) != 1:
            rep.error(f"bir boru ağında {len(pumps)} pompa var (tam 1 olmalı)")
        # açık uç su kaynağına bakmalı, diğer uç tanka değmeli
        touches_tank = any(
            w.id_at((p[0] + o[0], p[1] + o[1], p[2] + o[2])) == "create:fluid_tank"
            for p in comp
            for o in DIRS.values()
        )
        touches_water = any(
            (w.id_at((p[0] + o[0], p[1] + o[1], p[2] + o[2])) or "").startswith("minecraft:water")
            for p in comp
            for o in DIRS.values()
        )
        if not touches_tank:
            rep.error("bir boru ağı kazana bağlı değil")
        if not touches_water:
            rep.error("bir boru ağının açık ucu su kaynağına bakmıyor")


def check_kinetics(w: World, rep: Report, ratios: dict, signs: dict | None = None) -> list[set[Pos]]:
    g = kinetic_edges(w, ratios, signs)
    _NEIGHBOR_GRAPH.clear()
    _NEIGHBOR_GRAPH.update(g)
    nodes = [p for p, (bid, _) in w.parsed.items() if is_kinetic(bid)]
    comps = components(g, nodes)
    comps.sort(key=len, reverse=True)

    isolated = [c for c in comps if len(c) == 1]
    for c in isolated:
        p = next(iter(c))
        if w.id_at(p) != "create:steam_engine":  # motorlar zaten tek başına durur
            rep.error(f"kopuk kinetik blok: {p} {w.id_at(p)}")

    def kinds(comp):
        d = defaultdict(int)
        for p in comp:
            d[w.id_at(p)] += 1
        return dict(d)

    real = [c for c in comps if len(c) > 1]
    rep.ok(f"{len(real)} kinetik ağ bulundu:")
    for c in real:
        k = kinds(c)
        rep.info.append(
            "      - "
            + ", ".join(f"{v}x {kk.split(':')[-1]}" for kk, v in sorted(k.items()))
        )
    return real


def propagate_signs(w: World, comp: set[Pos], graph, signs: dict) -> dict[Pos, int]:
    """Bileşen içinde GÖRECELİ dönüş yönlerini yayar.

    Kurallar: eksen bağlantısı +1, dişli kavraması -1, beslenen gearshift'ten
    ÇIKIŞ -1 (GearshiftBlock yönü çevirir).

    Gearbox'lar +1 kabul edilir (gerçek işaretleri giriş yönüne bağlıdır).
    Bu, MUTLAK yön için doğru değildir; ama iki çıkışın da aynı gearbox
    zincirinden beslendiği durumlarda GÖRECELİ karşılaştırma doğru kalır —
    crushing wheel çiftini denetlemek için gereken tam olarak budur.
    """
    start = next(iter(comp))
    out = {start: 1}
    q = deque([start])
    while q:
        cur = q.popleft()
        bid, props = w.parsed[cur]
        flip_on_exit = bid == "create:gearshift" and props.get("powered") == "true"
        for nb in graph.get(cur, ()):
            if nb not in comp or nb in out:
                continue
            sign = out[cur] * signs.get((cur, nb), 1)
            if flip_on_exit:
                sign = -sign
            out[nb] = sign
            q.append(nb)
    return out


def check_crushing_wheels(w: World, rep: Report, comps, graph, signs) -> None:
    wheels = [p for p in w.parsed if w.id_at(p) == "create:crushing_wheel"]
    if not wheels:
        return
    if len(wheels) % 2:
        rep.error(f"{len(wheels)} crushing wheel — çift sayı olmalı (çiftler hâlinde çalışır)")

    signmap = {}
    for comp in comps:
        signmap.update(propagate_signs(w, comp, graph, signs))

    seen = set()
    for p in wheels:
        if p in seen:
            continue
        axis = w.props_at(p)["axis"]
        partner = None
        for d, off in DIRS.items():
            if DIR_AXIS[d] == axis:
                continue  # side ekseni çarkın ekseninden farklı olmalı
            cand = (p[0] + off[0] * 2, p[1] + off[1] * 2, p[2] + off[2] * 2)
            if w.id_at(cand) == "create:crushing_wheel" and w.props_at(cand)["axis"] == axis:
                gap = (p[0] + off[0], p[1] + off[1], p[2] + off[2])
                if not w.is_air(gap):
                    rep.error(
                        f"crushing wheel çifti {p}/{cand}: aradaki {gap} boş değil "
                        f"({w.id_at(gap)}) — controller oluşamaz"
                    )
                partner = cand
                break
        if partner is None:
            rep.error(f"crushing wheel {p}: 2 blok ötede aynı eksenli eş çark yok")
            continue
        seen.update({p, partner})

        sa, sb = signmap.get(p), signmap.get(partner)
        if sa is None or sb is None:
            rep.error(f"crushing wheel çifti {p}/{partner}: en az biri güç almıyor")
        elif sa == sb:
            rep.error(
                f"crushing wheel çifti {p}/{partner} AYNI yönde dönüyor — "
                "Create bu çifti çalıştırmaz (ters yön şart)"
            )
        else:
            rep.ok(f"crushing wheel çifti {p}/{partner} ters yönde dönüyor")


MAX_ROTATION_SPEED = 256  # CKinetics.maxRotationSpeed varsayılanı
MAX_BELT_LENGTH = 20  # CKinetics.maxBeltLength varsayılanı


def check_belts(w: World, rep: Report) -> None:
    """Bant zincirleri: uzunluk sınırı ve en az 2 segment.

    BeltBlock.initBelt zinciri 2'den kısaysa bandı KIRAR. Uzunluk sınırı
    (varsayılan 20) elle inşa edilebilirlik için kontrol edilir.
    """
    belts = {p for p in w.parsed if w.id_at(p) == "create:belt"}
    seen: set[Pos] = set()
    for p in sorted(belts):
        if p in seen:
            continue
        facing = w.props_at(p)["facing"]
        off = DIRS[facing]
        chain = [p]
        cur = p
        while True:
            nxt = (cur[0] + off[0], cur[1] + off[1], cur[2] + off[2])
            if nxt in belts and w.props_at(nxt).get("facing") == facing:
                chain.append(nxt)
                cur = nxt
            else:
                break
        # yalnız zincirin başından say
        prev = (p[0] - off[0], p[1] - off[1], p[2] - off[2])
        if prev in belts and w.props_at(prev).get("facing") == facing:
            continue
        seen.update(chain)
        if len(chain) < 2:
            rep.error(f"bant {p}: zincir {len(chain)} blok — initBelt 2'den kısa bandı kırar")
        elif len(chain) > MAX_BELT_LENGTH:
            rep.error(f"bant {p}: zincir {len(chain)} blok > {MAX_BELT_LENGTH} (maxBeltLength)")
        else:
            rep.ok(f"bant zinciri {p} -> {chain[-1]}: {len(chain)} blok")


def check_speeds(w: World, rep: Report, comps, ratios, external_power: bool = False) -> None:
    """Hızı kaynaklardan yayıp ÇAKIŞMA arar.

    Aynı ağda bir bloğa iki farklı hız ulaşırsa Create tüm ağı durdurur
    ("speed conflict"). Paralel bir yol yanlışlıkla RSC'yi baypas ederse
    tam da bu olur; bu yüzden ayrı bir kontrol.
    """
    sources: dict[Pos, float] = {}
    for p, (bid, props) in w.parsed.items():
        if bid == "create:water_wheel":
            sources[p] = 8.0
        elif bid == "create:steam_engine":
            facing = props["facing"] if props.get("face") == "wall" else "up"
            o = DIRS[facing]
            sources[(p[0] + o[0] * 2, p[1] + o[1] * 2, p[2] + o[2] * 2)] = 64.0

    for comp in comps:
        speeds: dict[Pos, float] = {}
        q = deque()
        for p, rpm in sources.items():
            if p in comp:
                speeds[p] = rpm
                q.append(p)
        if not q:
            if external_power:
                rep.ok(
                    f"kinetik ağ ({len(comp)} blok) dış güçle beslenir — "
                    "modülün güç girişine bağlanacak"
                )
            else:
                rep.error(f"kinetik ağda hiç güç kaynağı yok ({len(comp)} blok)")
            continue

        conflicts = []
        while q:
            cur = q.popleft()
            for nb in sorted(w_neighbors(cur, comp)):
                f = ratios.get((cur, nb))
                if f is None:
                    continue
                if isinstance(f, tuple):  # RSC
                    if f[1] is None:
                        continue  # geri yönde bariyer: RSC girişi bağımsız
                    val = f[1]
                else:
                    val = speeds[cur] * f
                if nb in speeds:
                    if not math.isclose(speeds[nb], val, rel_tol=1e-6):
                        conflicts.append((nb, speeds[nb], val))
                else:
                    speeds[nb] = val
                    q.append(nb)

        if conflicts:
            p, a, b = conflicts[0]
            rep.error(
                f"HIZ ÇAKIŞMASI {p}: {a:g} RPM ve {b:g} RPM aynı ağda buluşuyor "
                f"(toplam {len(conflicts)} çakışma) — ağ tamamen durur"
            )
            continue

        top = max(speeds.values())
        if top > MAX_ROTATION_SPEED:
            rep.error(f"maksimum hız aşıldı: {top:g} RPM > {MAX_ROTATION_SPEED}")
        else:
            distinct = sorted({round(v) for v in speeds.values()})
            rep.ok(
                f"ağ hızları tutarlı: {', '.join(str(d) + ' RPM' for d in distinct)} "
                f"({len(speeds)}/{len(comp)} blok beslenmiş)"
            )
        if len(speeds) < len(comp):
            rep.error(
                f"{len(comp) - len(speeds)} kinetik blok güç almıyor (RSC bariyerinin ters tarafı?)"
            )


_NEIGHBOR_GRAPH: dict[Pos, set[Pos]] = {}


def w_neighbors(pos: Pos, comp: set[Pos]) -> set[Pos]:
    return {n for n in _NEIGHBOR_GRAPH.get(pos, ()) if n in comp}


def run(blocks: dict[Pos, str], *, expected_fluid_networks: int | None = None,
        external_power: bool = False) -> Report:
    rep = Report()
    w = World(blocks)
    if any(w.id_at(p) == "create:fluid_tank" for p in w.parsed):
        check_boiler(w, rep)
    if any(w.id_at(p) == "create:steam_engine" for p in w.parsed):
        check_engines(w, rep)
    check_deployers(w, rep)
    check_belts(w, rep)
    if expected_fluid_networks is not None:
        check_fluid(w, rep, expected_fluid_networks)
    ratios: dict = {}
    signs: dict = {}
    comps = check_kinetics(w, rep, ratios, signs)
    check_speeds(w, rep, comps, ratios, external_power)
    check_crushing_wheels(w, rep, comps, _NEIGHBOR_GRAPH, signs)
    return rep
