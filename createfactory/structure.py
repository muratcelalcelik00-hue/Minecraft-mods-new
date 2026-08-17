"""
Vanilla "structure" NBT yazıcısı (.nbt).

Bu format Create'in kendi şematik sisteminin (Schematic Table +
Schematicannon) okuduğu formattır ve vanilla structure block'unun formatıyla
aynıdır. WorldEdit gerekmez.

Kök yapı (Create'in kendi ponder .nbt dosyalarından birebir doğrulandı):

    ""  (isimsiz, gzip'li kök compound)
      size        : List[Int]  [W, H, L]
      entities    : List
      blocks      : List[Compound]  { pos: List[Int], state: Int, nbt?: Compound }
      palette     : List[Compound]  { Name: String, Properties?: Compound }
      DataVersion : Int
"""

from __future__ import annotations

import os

import nbtlib
from nbtlib.tag import Compound, Int, List, String

#: Block entity tipi registry adı, blok registry adından FARKLI olan bloklar.
#: (AllBlockEntityTypes.java'dan doğrulandı — örn. blaze burner'ın BE'si
#: "blaze_heater" adıyla kayıtlı.) Burada olmayan bloklar için blok adı
#: kullanılır.
BE_TYPE_ID = {
    "create:blaze_burner": "create:blaze_heater",
}

DATA_VERSION = 3955  # Minecraft 1.21.1


def _parse(block: str) -> tuple[str, dict[str, str], str | None]:
    """'create:shaft[axis=x]{Nbt:1}' -> ('create:shaft', {'axis':'x'}, '{Nbt:1}')"""
    nbt = None
    if "{" in block:
        i = block.index("{")
        block, nbt = block[:i], block[i:]
    props: dict[str, str] = {}
    if "[" in block:
        i = block.index("[")
        body = block[i + 1 : block.rindex("]")]
        block = block[:i]
        for kv in body.split(","):
            k, _, v = kv.partition("=")
            props[k] = v
    return block, props, nbt


def write(blocks: dict[tuple[int, int, int], str], out_dir: str, name: str) -> str:
    """Blok sözlüğünü .nbt structure dosyası olarak yazar.

    Koordinatlar minimum köşe (0,0,0) olacak şekilde kaydırılır.
    """
    os.makedirs(out_dir, exist_ok=True)
    if not blocks:
        raise ValueError("boş yapı")

    xs = [p[0] for p in blocks]
    ys = [p[1] for p in blocks]
    zs = [p[2] for p in blocks]
    lo = (min(xs), min(ys), min(zs))
    size = (max(xs) - lo[0] + 1, max(ys) - lo[1] + 1, max(zs) - lo[2] + 1)

    palette: list[Compound] = []
    palette_index: dict[tuple[str, tuple], int] = {}
    block_list: list[Compound] = []

    for pos in sorted(blocks, key=lambda p: (p[1], p[0], p[2])):
        bid, props, snbt = _parse(blocks[pos])
        key = (bid, tuple(sorted(props.items())))
        if key not in palette_index:
            entry = Compound({"Name": String(bid)})
            if props:
                entry["Properties"] = Compound({k: String(v) for k, v in props.items()})
            palette_index[key] = len(palette)
            palette.append(entry)

        entry = Compound(
            {
                "pos": List[Int]([Int(pos[i] - lo[i]) for i in range(3)]),
                "state": Int(palette_index[key]),
            }
        )
        if snbt:
            be = nbtlib.parse_nbt(snbt)
            # structure formatında block entity verisi kendi tip adını taşır
            be["id"] = String(BE_TYPE_ID.get(bid, bid))
            entry["nbt"] = be
        block_list.append(entry)

    root = nbtlib.File(
        {
            "size": List[Int]([Int(v) for v in size]),
            "entities": List([]),
            "blocks": List[Compound](block_list),
            "palette": List[Compound](palette),
            "DataVersion": Int(DATA_VERSION),
        },
        gzipped=True,
        root_name="",
    )
    path = os.path.join(out_dir, name + ".nbt")
    root.save(path)
    return path
