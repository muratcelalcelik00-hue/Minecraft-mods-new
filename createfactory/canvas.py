"""
Ortak yerleştirme katmanı.

Canvas, mcschematic'in üstünde ince bir katman: blokları yerel koordinatlarda
tutar, çakışmaları yakalar, modülün "manifest"ini (giriş/çıkış noktaları, SU
bütçesi, notlar) toplar ve .schem dosyasını yazar.

Koordinat sistemi (Minecraft ile aynı):
    +X = doğu (east), +Y = yukarı (up), +Z = güney (south)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import mcschematic

from . import blocks as B

#: 1.21.1 data version (mcschematic.Version.JE_1_21_1 == 3955)
MC_VERSION = mcschematic.Version.JE_1_21_1

Pos = tuple[int, int, int]


class CollisionError(RuntimeError):
    pass


@dataclass
class IOPoint:
    """Modülün dış dünyaya açılan bir bağlantı noktası."""

    name: str
    pos: Pos
    kind: str  # "item-in" | "item-out" | "fluid-in" | "fluid-out" | "rotation-out" | ...
    note: str = ""


@dataclass
class Manifest:
    """README/doküman üretimi için modül meta verisi."""

    module_id: str
    title: str
    io: list[IOPoint] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    stress: dict[str, float] = field(default_factory=dict)


class Canvas:
    def __init__(self, module_id: str, title: str):
        self._blocks: dict[Pos, str] = {}
        self.manifest = Manifest(module_id=module_id, title=title)

    # -- temel yerleştirme ------------------------------------------------

    def set(self, pos: Pos, block: str, *, overwrite: bool = False) -> None:
        pos = (int(pos[0]), int(pos[1]), int(pos[2]))
        if not overwrite and pos in self._blocks and self._blocks[pos] != block:
            raise CollisionError(
                f"{pos} zaten dolu: {self._blocks[pos]!r} <- yeni {block!r}"
            )
        self._blocks[pos] = block

    def get(self, pos: Pos) -> str | None:
        return self._blocks.get((int(pos[0]), int(pos[1]), int(pos[2])))

    def fill(self, a: Pos, b: Pos, block: str, *, overwrite: bool = False) -> None:
        """a..b (dahil) kutusunu doldurur."""
        (x0, y0, z0), (x1, y1, z1) = a, b
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.set((x, y, z), block, overwrite=overwrite)

    def hollow_box(self, a: Pos, b: Pos, block: str) -> None:
        """Sadece kabuk (duvar/taban/tavan)."""
        (x0, y0, z0), (x1, y1, z1) = a, b
        xs, ys, zs = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
        for x in range(xs[0], xs[1] + 1):
            for y in range(ys[0], ys[1] + 1):
                for z in range(zs[0], zs[1] + 1):
                    on_shell = (
                        x in (xs[0], xs[1]) or y in (ys[0], ys[1]) or z in (zs[0], zs[1])
                    )
                    if on_shell:
                        self.set((x, y, z), block)

    # -- kinetik yardımcılar ---------------------------------------------

    def shaft_run(self, start: Pos, axis: str, length: int, *, block=None) -> list[Pos]:
        """axis yönünde `length` adet şaft (veya verilen blok) dizer."""
        step = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[axis]
        placed = []
        for i in range(length):
            p = (start[0] + step[0] * i, start[1] + step[1] * i, start[2] + step[2] * i)
            self.set(p, block or B.shaft(axis))
            placed.append(p)
        return placed

    def cog_column(self, start: Pos, axis: str, count: int, *, dy: int = 1) -> list[Pos]:
        """Dikey dişli kolonu: aynı eksenli, birbirine komşu küçük dişliler
        kavrar (mesh) ve gücü kat kat aktarır.

        Kural (RotationPropagator): iki KÜÇÜK dişli manhattan mesafesi 1,
        aynı dönme ekseni ve bağlantı yönü != dönme ekseni ise kavrar.
        """
        assert axis in ("x", "z"), "dikey kolon için eksen yatay olmalı"
        placed = []
        for i in range(count):
            p = (start[0], start[1] + dy * i, start[2])
            self.set(p, B.cog(axis))
            placed.append(p)
        return placed

    def belt_run(self, start: Pos, facing: str, length: int) -> list[Pos]:
        """Düz yatay bant dizer: start -> facing yönünde `length` blok.

        part = start / middle / end otomatik atanır. NBT yazılmaz (bkz.
        blocks.belt docstring'i: bant paste sonrası kendini kurar).
        """
        if length < 2:
            raise ValueError("bant zinciri en az 2 blok olmalı (initBelt aksi halde kırar)")
        step = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0)}[
            facing
        ]
        placed = []
        for i in range(length):
            part = "start" if i == 0 else ("end" if i == length - 1 else "middle")
            p = (start[0] + step[0] * i, start[1] + step[1] * i, start[2] + step[2] * i)
            self.set(p, B.belt(facing=facing, part=part))
            placed.append(p)
        return placed

    def set_if_empty(self, pos: Pos, block: str) -> bool:
        """Yalnız boşsa yazar. Bina kabuğu makinelerin üstüne taşmasın diye."""
        pos = (int(pos[0]), int(pos[1]), int(pos[2]))
        if pos in self._blocks:
            return False
        self._blocks[pos] = block
        return True

    def merge(self, other: "Canvas", offset: Pos, *, prefix: str = "") -> None:
        """Başka bir modülü, kendi min köşesi `offset` olacak şekilde ekler.

        Modülün giriş/çıkış noktaları da kaydırılarak manifest'e taşınır.
        """
        lo, _ = other.bounds
        for pos, blk in other.blocks().items():
            self.set(
                (pos[0] - lo[0] + offset[0], pos[1] - lo[1] + offset[1], pos[2] - lo[2] + offset[2]),
                blk,
            )
        for p in other.manifest.io:
            self.manifest.io.append(
                IOPoint(
                    f"{prefix}{p.name}",
                    (p.pos[0] - lo[0] + offset[0], p.pos[1] - lo[1] + offset[1],
                     p.pos[2] - lo[2] + offset[2]),
                    p.kind,
                    p.note,
                )
            )

    def route_shaft(self, points: list[Pos]) -> None:
        """Ortogonal bir polyline boyunca şaft döşer, köşelere gearbox koyar.

        Ardışık iki nokta yalnız TEK eksende farklı olmalı. Bir köşede
        A ekseninden B eksenine dönerken gearbox'ın ekseni ÜÇÜNCÜ eksendir:
        `GearboxBlock.hasShaftTowards` = `face.getAxis() != AXIS`, yani
        axis=C olan gearbox yalnız A ve B yüzlerine şaft verir.
        """
        from . import blocks as B

        # sıfır uzunluklu segmentleri at (hedef zaten o eksende hizalıysa)
        cleaned: list[Pos] = []
        for p in points:
            if not cleaned or tuple(p) != tuple(cleaned[-1]):
                cleaned.append(tuple(p))
        points = cleaned

        axes = []
        for a, b in zip(points, points[1:]):
            diff = [b[i] - a[i] for i in range(3)]
            nz = [i for i, d in enumerate(diff) if d != 0]
            if len(nz) != 1:
                raise ValueError(f"segment tek eksende olmalı: {a} -> {b}")
            axes.append("xyz"[nz[0]])

        for seg, (a, b) in enumerate(zip(points, points[1:])):
            axis = axes[seg]
            i = "xyz".index(axis)
            step = 1 if b[i] > a[i] else -1
            cur = list(a)
            # ilk segment kendi başlangıcını da döşer; sonrakiler köşeden
            # bir adım sonra başlar, yoksa önceki köşenin gearbox'ını ezerler
            if seg > 0:
                cur[i] += step
            while cur[i] != b[i]:
                self.set(tuple(cur), B.shaft(axis))
                cur[i] += step
            if seg + 1 < len(axes):
                third = ({"x", "y", "z"} - {axis, axes[seg + 1]}).pop()
                self.set(tuple(b), B.gearbox(third))
            else:
                self.set(tuple(b), B.shaft(axis))

    # -- manifest ---------------------------------------------------------

    def io(self, name: str, pos: Pos, kind: str, note: str = "") -> None:
        self.manifest.io.append(IOPoint(name, tuple(pos), kind, note))

    def note(self, text: str) -> None:
        self.manifest.notes.append(text)

    # -- çıktı ------------------------------------------------------------

    @property
    def bounds(self) -> tuple[Pos, Pos]:
        xs = [p[0] for p in self._blocks]
        ys = [p[1] for p in self._blocks]
        zs = [p[2] for p in self._blocks]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    @property
    def size(self) -> Pos:
        lo, hi = self.bounds
        return (hi[0] - lo[0] + 1, hi[1] - lo[1] + 1, hi[2] - lo[2] + 1)

    def blocks(self) -> dict[Pos, str]:
        return dict(self._blocks)

    # -- koordinat dönüşümü ----------------------------------------------

    def to_schem(self, pos: Pos) -> Pos:
        """Tasarım koordinatını şematik-içi (0 tabanlı) koordinata çevirir.

        Şematik kaydedilirken min köşe (0,0,0)'a kaydırılır; böylece WEOffset
        sıfır olur ve `//paste` yapının min köşesini oyuncunun konumuna koyar.
        """
        lo, _ = self.bounds
        return (pos[0] - lo[0], pos[1] - lo[1], pos[2] - lo[2])

    def normalized_io(self) -> list[IOPoint]:
        return [IOPoint(p.name, self.to_schem(p.pos), p.kind, p.note) for p in self.manifest.io]

    def save_nbt(self, out_dir: str, name: str) -> str:
        """Vanilla structure .nbt yazar (Create'in Schematic Table'ı bunu okur)."""
        from . import structure

        return structure.write(self._blocks, out_dir, name)

    def save(self, out_dir: str, name: str) -> str:
        """Sponge Schematic v2 (.schem) yazar. Min köşe (0,0,0)'a kaydırılır."""
        os.makedirs(out_dir, exist_ok=True)
        lo, _ = self.bounds
        schem = mcschematic.MCSchematic()
        for pos, blk in self._blocks.items():
            schem.setBlock((pos[0] - lo[0], pos[1] - lo[1], pos[2] - lo[2]), blk)
        schem.save(out_dir, name, MC_VERSION)
        return os.path.join(out_dir, name + ".schem")
