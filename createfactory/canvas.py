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
