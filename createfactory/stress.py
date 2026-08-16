"""
Create 6.x stres (SU) muhasebesi.

Create'te ağ kapasitesi ve yükü HIZA ORANTILIDIR:

    kapasite = Σ (üretecin base capacity'si  × kendi RPM'i)
    yük      = Σ (makinenin base impact'i    × kendi RPM'i)

Aşağıdaki base değerler AllBlocks.java'daki CStress.setCapacity/setImpact
çağrılarından birebir alınmıştır (bkz. docs/create-6-dogrulama.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --- üreteçler: (base capacity, ürettiği RPM) ------------------------------
CAPACITY = {
    "create:steam_engine": 1024.0,
    "create:water_wheel": 32.0,
    "create:large_water_wheel": 128.0,
    "create:windmill_bearing": 512.0,
    "create:hand_crank": 8.0,
    "create:creative_motor": 16384.0,
}

GENERATED_RPM = {
    "create:steam_engine": 64,  # tam verimde: 16 * speedModifier(=4)
    "create:water_wheel": 8,
    "create:large_water_wheel": 4,
    "create:windmill_bearing": 16,
    "create:hand_crank": 32,
    "create:creative_motor": 256,
}

# --- tüketiciler: base impact (1 RPM'deki maliyet) -------------------------
IMPACT = {
    "create:mechanical_pump": 4.0,
    "create:deployer": 4.0,
    "create:mechanical_press": 8.0,
    "create:crushing_wheel": 8.0,
    "create:millstone": 4.0,
    "create:mechanical_mixer": 4.0,
    "create:mechanical_saw": 4.0,
    "create:encased_fan": 2.0,
    "create:mechanical_crafter": 2.0,
}

#: Boiler sabitleri (BoilerData.java)
BOILER_MAX_LEVEL = 18
BOILER_WATER_PER_LEVEL = 10  # mB/t, her ısı seviyesi için
BOILER_BLOCKS_PER_LEVEL = 4  # tank blok sayısı / 4 = maks ısı seviyesi


def engine_bank_su(engines: int, boiler_level: int = BOILER_MAX_LEVEL) -> float:
    """Steam engine bankasının GERÇEK ağ kapasitesi.

    Her motor: capacity 1024 / speedModifier 4 = 256 SU/RPM, 64 RPM'de
    256*64 = 16.384 SU. Verim 1 ise (motor sayısı <= kazan seviyesi)
    toplam = motor sayısı * 16.384.

    NOT: Kazanın goggle tooltip'i max(boilerLevel, engines) kullandığı için
    18'den az motorla da "294.912 SU" yazabilir; gerçekte üretilen kapasite
    motor başına 16.384'tür.
    """
    if engines > boiler_level:
        efficiency = boiler_level / engines
    else:
        efficiency = 1.0
    per_engine = efficiency * CAPACITY["create:steam_engine"] / 4 * GENERATED_RPM["create:steam_engine"]
    return engines * per_engine


def water_needed(boiler_level: int = BOILER_MAX_LEVEL) -> int:
    """Kazanın verilen seviyeyi tutması için gereken su debisi (mB/t)."""
    return boiler_level * BOILER_WATER_PER_LEVEL


def pump_throughput(rpm: float) -> int:
    """Tek bir boru AĞININ debisi (mB/t).

    FluidNetwork: transferSpeed = max(1, pompa_basinci / 2) ve basınç =
    |pompa RPM|. Debi ağ başınadır; daha fazla debi için AYRI boru ağları
    (birbirine değmeyen borular) gerekir.
    """
    return int(max(1, rpm / 2))


def pump_cost(rpm: float) -> float:
    return IMPACT["create:mechanical_pump"] * rpm


@dataclass
class Load:
    label: str
    block: str
    count: int
    rpm: float

    @property
    def su(self) -> float:
        return IMPACT[self.block] * self.rpm * self.count


@dataclass
class Source:
    label: str
    block: str
    count: int
    rpm: float | None = None

    @property
    def su(self) -> float:
        rpm = self.rpm if self.rpm is not None else GENERATED_RPM[self.block]
        if self.block == "create:steam_engine":
            return engine_bank_su(self.count)
        return CAPACITY[self.block] * rpm * self.count


@dataclass
class Budget:
    """Tek bir kinetik ağın stres bütçesi."""

    name: str
    sources: list[Source] = field(default_factory=list)
    loads: list[Load] = field(default_factory=list)

    def add_source(self, label, block, count, rpm=None):
        self.sources.append(Source(label, block, count, rpm))

    def add_load(self, label, block, count, rpm):
        self.loads.append(Load(label, block, count, rpm))

    @property
    def capacity(self) -> float:
        return sum(s.su for s in self.sources)

    @property
    def used(self) -> float:
        return sum(l.su for l in self.loads)

    @property
    def free(self) -> float:
        return self.capacity - self.used

    @property
    def headroom_pct(self) -> float:
        return 100.0 * self.free / self.capacity if self.capacity else 0.0

    def check(self) -> None:
        if self.used > self.capacity:
            raise AssertionError(
                f"[{self.name}] AŞIRI YÜK: {self.used:,.0f} SU / {self.capacity:,.0f} SU"
            )

    def report(self) -> str:
        lines = [f"### Stres bütçesi — {self.name}", ""]
        lines.append("| | Blok | Adet | RPM | SU |")
        lines.append("|---|---|---:|---:|---:|")
        for s in self.sources:
            rpm = s.rpm if s.rpm is not None else GENERATED_RPM[s.block]
            lines.append(f"| kaynak | {s.label} | {s.count} | {rpm:g} | +{s.su:,.0f} |")
        for l in self.loads:
            lines.append(f"| yük | {l.label} | {l.count} | {l.rpm:g} | −{l.su:,.0f} |")
        lines.append(
            f"| **toplam** | | | | **{self.used:,.0f} / {self.capacity:,.0f} SU "
            f"({self.headroom_pct:.0f}% boş)** |"
        )
        return "\n".join(lines)
