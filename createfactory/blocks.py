"""
Create 6.x (MC 1.21.1) blok / blockstate yardımcıları.

Buradaki HER registry adı ve HER blockstate property adı, Create'in
1.21.1 kaynak kodundan doğrulanmıştır (bkz. docs/create-6-dogrulama.md).
Tahmin edilmiş / uydurulmuş isim yoktur.

Blok string formatı (mcschematic'in beklediği format):
    namespace:id[prop=val,prop2=val2]{NbtSnbt}
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# Düşük seviye yardımcılar
# --------------------------------------------------------------------------


def block(block_id: str, *, nbt: str | None = None, **props) -> str:
    """Blockstate string'i üretir.

    >>> block("create:shaft", axis="x")
    'create:shaft[axis=x]'
    >>> block("create:rotation_speed_controller", axis="z", nbt="{ScrollValue:64}")
    'create:rotation_speed_controller[axis=z]{ScrollValue:64}'
    """
    out = block_id
    if props:
        body = ",".join(f"{k}={_val(v)}" for k, v in sorted(props.items()))
        out += f"[{body}]"
    if nbt:
        out += nbt
    return out


def _val(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


AIR = "minecraft:air"
WATER = "minecraft:water[level=0]"  # kaynak blok (level=0 == source)


# --------------------------------------------------------------------------
# Vanilla
# --------------------------------------------------------------------------

STONE = "minecraft:smooth_stone"
CASING_BLOCK = "create:andesite_casing"


# --------------------------------------------------------------------------
# Kinetik: şaft / dişli / aktarım
#   ShaftBlock, CogWheelBlock : AbstractSimpleShaftBlock -> RotatedPillarKineticBlock
#   -> property'ler: axis (x|y|z), waterlogged (bool)
# --------------------------------------------------------------------------


def shaft(axis: str) -> str:
    return block("create:shaft", axis=axis, waterlogged=False)


def cog(axis: str) -> str:
    """Küçük dişli (small cogwheel)."""
    return block("create:cogwheel", axis=axis, waterlogged=False)


def large_cog(axis: str) -> str:
    return block("create:large_cogwheel", axis=axis, waterlogged=False)


def gearbox(axis: str) -> str:
    """GearboxBlock: RotatedPillarKineticBlock -> axis.

    axis=y olan bir gearbox 4 yatay yöne şaft verir (X <-> Z dönüşü).
    """
    return block("create:gearbox", axis=axis)


def clutch(axis: str, powered: bool = False) -> str:
    """ClutchBlock extends GearshiftBlock -> axis + powered.

    powered=false -> güç iletir, powered=true -> bağlantıyı keser.
    """
    return block("create:clutch", axis=axis, powered=powered)


def gearshift(axis: str, powered: bool = False) -> str:
    """GearshiftBlock -> axis + powered. powered=true -> yön tersine döner."""
    return block("create:gearshift", axis=axis, powered=powered)


def speed_controller(axis: str, target_rpm: int) -> str:
    """Rotation Speed Controller.

    - blockstate: horizontalAxisBlockProvider -> axis (yalnız x|z)
    - üstündeki LARGE cogwheel'in hızını target_rpm'e sabitler
    - hedef hız ScrollValueBehaviour ile saklanır -> NBT anahtarı "ScrollValue"
    - RSC'nin ekseni, üstündeki large cog'un ekseninden FARKLI olmalı
    """
    return block(
        "create:rotation_speed_controller",
        axis=axis,
        nbt=f"{{ScrollValue:{int(target_rpm)}}}",
    )


# --------------------------------------------------------------------------
# Kinetik: üreteçler
# --------------------------------------------------------------------------


def water_wheel(facing: str) -> str:
    """WaterWheelBlock: DirectionalKineticBlock -> facing.

    Dönme ekseni = facing ekseni. hasShaftTowards eksen bazlı olduğu için
    aynı eksende yan yana dizilen su çarkları birbirine bağlanır (tek mil).
    """
    return block("create:water_wheel", facing=facing)


def steam_engine(facing: str, face: str = "wall") -> str:
    """SteamEngineBlock: FaceAttachedHorizontalDirectionalBlock -> face/facing/waterlogged.

    Geometri (SteamEngineBlock kaynağı):
      - tank  = pos.relative(facing.getOpposite())   -> motor tanktan UZAĞA bakar
      - şaft  = pos.relative(facing, 2)              -> 2 blok ileride
      - aradaki blok (pos.relative(facing,1)) BOŞ olmalı
      - şaftın ekseni facing ekseninden farklı olmalı
    """
    return block("create:steam_engine", face=face, facing=facing, waterlogged=False)


# --------------------------------------------------------------------------
# Akışkan
# --------------------------------------------------------------------------


def fluid_tank(*, top: bool, bottom: bool, shape: str = "plain") -> str:
    """FluidTankBlock -> top(bool), bottom(bool), shape(enum).

    shape: plain | window | window_nw | window_sw | window_ne | window_se
    (Görsel amaçlı; Create bağlantı güncellemesinde kendi yeniden hesaplar.)
    """
    return block("create:fluid_tank", top=top, bottom=bottom, shape=shape)


def fluid_pipe(*, north=False, east=False, south=False, west=False, up=False, down=False) -> str:
    """FluidPipeBlock extends (vanilla) PipeBlock -> 6 yönlü bool + waterlogged."""
    return block(
        "create:fluid_pipe",
        north=north,
        east=east,
        south=south,
        west=west,
        up=up,
        down=down,
        waterlogged=False,
    )


def mechanical_pump(facing: str) -> str:
    """PumpBlock: DirectionalKineticBlock + ICogWheel.

    - akışkan facing ekseni boyunca akar (isOpenAt: d.axis == facing.axis)
    - dönme ekseni = facing ekseni
    - ICogWheel olduğu için yanındaki KÜÇÜK dişlilerle kavrar (mesh)
    """
    return block("create:mechanical_pump", facing=facing, waterlogged=False)


# --------------------------------------------------------------------------
# Isı
# --------------------------------------------------------------------------

#: BoilerHeaters.blazeBurner() -> kazana verdiği ısı puanı
BURNER_HEAT = {"seething": 2, "kindled": 1, "fading": 1, "smouldering": 0, "none": -1}


def blaze_burner(heat: str = "seething", facing: str = "north") -> str:
    """BlazeBurnerBlock: HorizontalDirectionalBlock -> HEAT_LEVEL + FACING.

    DİKKAT: property adı "heat_level" DEĞİL, **"blaze"**'dir
    (EnumProperty.create("blaze", HeatLevel.class)).

    Değerler: none | smouldering | fading | kindled | seething
      seething  = blaze cake ile beslenmiş (super-heated) -> 2 ısı
      kindled   = normal yakıt (kömür vb.)                -> 1 ısı
    """
    assert heat in BURNER_HEAT, heat
    return block("create:blaze_burner", blaze=heat, facing=facing)


# --------------------------------------------------------------------------
# Lojistik
# --------------------------------------------------------------------------


def deployer(facing: str, axis_along_first: bool) -> str:
    """DeployerBlock: DirectionalAxisKineticBlock -> facing + axis_along_first.

    Dönme ekseni (DirectionalAxisKineticBlock.getRotationAxis):
        facing ekseni X -> axis_along_first ? Y : Z
        facing ekseni Y -> axis_along_first ? X : Z
        facing ekseni Z -> axis_along_first ? X : Y

    Varsayılan mod USE'dur (DeployerBlockEntity: mode = Mode.USE), yani
    sağ tık yapar -> blaze burner'a yakıt vermek için doğru mod.
    """
    return block("create:deployer", facing=facing, axis_along_first=axis_along_first)


def chute(facing: str = "down", shape: str = "normal") -> str:
    """ChuteBlock -> facing (FACING_HOPPER: down + yatay) + shape + waterlogged.

    Chute üstündeki envanterden çeker, altındaki envantere iter (güç istemez).
    shape: normal | window | intersection
    """
    return block("create:chute", facing=facing, shape=shape, waterlogged=False)


def item_vault(horizontal_axis: str = "x", large: bool = False) -> str:
    """ItemVaultBlock -> horizontal_axis (x|z) + large(bool).

    Aynı eksende yan yana dizilen vault'lar TEK bir envanter oluşturur;
    bu yüzden tek noktadan doldurup tüm sıraya dağıtabiliyoruz.
    """
    return block("create:item_vault", horizontal_axis=horizontal_axis, large=large)


def andesite_funnel(facing: str, extracting: bool, powered: bool = False) -> str:
    """FunnelBlock -> facing + extracting + powered.

    FACING, bağlı olduğu envanterden DIŞARI bakar (ağız yönü).
    Bağlı envanter = pos.relative(facing.getOpposite()).
        extracting=false -> ağızdan alır, envantere İTER   (giriş)
        extracting=true  -> envanterden çeker, ağızdan verir (çıkış)
    """
    return block("create:andesite_funnel", facing=facing, extracting=extracting, powered=powered)


def andesite_belt_funnel(facing: str, shape: str = "pulling", powered: bool = False) -> str:
    """BeltFunnelBlock (bir BELT'in tam üstüne konan funnel).

    shape: pushing (envanter -> bant) | pulling (bant -> envanter)
           | retracted | extended
    FACING yine bağlı envanterden dışarı bakar.
    """
    return block("create:andesite_belt_funnel", facing=facing, shape=shape, powered=powered)


def belt(facing: str, part: str, slope: str = "horizontal", casing: bool = False) -> str:
    """BeltBlock: HorizontalKineticBlock -> facing + part + slope + casing.

    part : start | middle | end | pulley
    slope: horizontal | upward | downward | vertical | sideways

    ÖNEMLİ: Belt'e ASLA block entity NBT yazma. BeltBlockEntity.tick():
        if (beltLength == 0) BeltBlock.initBelt(level, worldPosition);
    yani paste sonrası ilk tick'te zincir blockstate'lerden yeniden kurulur.
    NBT yazarsak (Controller dünya koordinatı olduğu için) bant bozulur.
    Zincir en az 2 blok olmalı, yoksa initBelt bandı kırar.
    """
    return block("create:belt", facing=facing, part=part, slope=slope, casing=casing)


# --------------------------------------------------------------------------
# Modül 2: işleme blokları
# --------------------------------------------------------------------------


def crushing_wheel(axis: str) -> str:
    """CrushingWheelBlock -> axis.

    Çift kurulumu (CrushingWheelBlock.updateControllers):
      - iki çark AYNI eksende ve aralarında 1 blok boşlukla
        (otherWheelPos = pos.relative(side, 2))
      - `side` ekseni çarkın dönme ekseninden FARKLI olmalı
      - aradaki boşlukta `create:crushing_wheel_controller` KENDİLİĞİNDEN oluşur
        (biz oraya blok koymayız, hava bırakırız)
      - çarklar TERS yönde dönmeli: (speed > 0) != (otherSpeed > 0)
    """
    return block("create:crushing_wheel", axis=axis)


def encased_fan(facing: str) -> str:
    """EncasedFanBlock: DirectionalKineticBlock -> facing.

    İşlem tipi, hava akımının geçtiği bloktan gelir
    (AllFanProcessingTypes.isValidAt önce getFluidState'e bakar):
      su   -> splashing (yıkama)
      lav  -> blasting  (eritme)
    Fan katı bir blok olduğu için, YUKARI bakan bir fanın üstündeki su/lav
    akıp gitmez; işlenecek eşya da onun bir üstündeki bantta durur.
    """
    return block("create:encased_fan", facing=facing)


LAVA = "minecraft:lava[level=0]"
REDSTONE_BLOCK = "minecraft:redstone_block"


# --------------------------------------------------------------------------
# Modül 3: alaşım
# --------------------------------------------------------------------------


def basin(facing: str = "down") -> str:
    """BasinBlock -> FACING (FACING_HOPPER: down + 4 yatay).

    FACING = ÇIKIŞ yönüdür ve Create bunu KENDİ bulur
    (BasinBlockEntity.updateSpoutput yatay yönleri tarar), o yüzden
    şematikte varsayılan `down` bırakmak yeterli.

    Çıkış şartı (BasinBlock.canOutputTo):
      - basin.relative(yön) BOŞ olmalı (çarpışma kutusu yok)
      - basin.relative(yön).below() DirectBeltInputBehaviour taşımalı
        (bant, depot, ...)

    Girdi: basin'in kendisi DirectBeltInputBehaviour taşır, yani bir bandın
    UCU doğrudan basin'e item verebilir — funnel gerekmez.

    Isı (BasinBlockEntity.getHeatLevelOf, below(1)):
      - blaze burner  -> kendi HEAT_LEVEL'i
      - kamp ateşi / lav / magma (passive_boiler_heaters) -> SMOULDERING
      HeatCondition.HEATED, SMOULDERING'i KABUL ETMEZ:
        `level != NONE && level != SMOULDERING`
      Yani "heated" tarifler (pirinç) için yakıtlı blaze burner ŞART.
    """
    return block("create:basin", facing=facing)


def mechanical_mixer() -> str:
    """MechanicalMixerBlock: KineticBlock + ICogWheel.

    - dönme ekseni sabit **Y**
    - `hasShaftTowards` her yön için FALSE -> şaft takılamaz, yalnızca yandaki
      küçük dişliyle KAVRAYARAK sürülür
    - basin tam **2 blok altında** olmalı (BasinOperatingBlockEntity:
      `worldPosition.below(2)`), aradaki blok boş bırakılır
    - minimum hız: SpeedLevel.MEDIUM
    """
    return "create:mechanical_mixer"


# --------------------------------------------------------------------------
# Modül 4: filtreli lojistik
# --------------------------------------------------------------------------


def smart_chute(filter_item: str, powered: bool = False) -> str:
    """SmartChuteBlock -> yalnız `powered` property'si (yön yok, hep aşağı).

    `powered=true` chute'u DURDURUR (getStateForPlacement redstone sinyalinden
    okur), o yüzden şematikte false yazılır.

    Normal chute gibi üstteki envanterden çeker / alttakine iter, ama
    FilteringBehaviour taşır: `canAcceptItem` içinde `filtering.test(stack)`
    çağrılır. Yani ortak bir depodan yalnız filtreye uyan itemi çeker.

    Filtre NBT (FilteringBehaviour.write):
        nbt.put("Filter", stack.saveOptional(registries))
    1.21 ItemStack formatı: {id:"...", count:N}
    """
    return block(
        "create:smart_chute",
        powered=powered,
        nbt=f'{{Filter:{{id:"{filter_item}",count:1}}}}',
    )


def brass_belt_funnel(facing: str, shape: str = "pulling", filter_item: str | None = None,
                      powered: bool = False) -> str:
    """Bir bandın üstüne konan pirinç funnel — filtre taşıyabilir.

    shape: pulling (bant -> envanter) | pushing (envanter -> bant)
    FACING bağlı olduğu envanterden DIŞARI bakar; bağlı envanter
    pos.relative(facing.getOpposite()).

    Filtre NBT'si FilteringBehaviour'dan: {Filter:{id:"...",count:1}}
    Filtreli bir funnel bandın üstünden YALNIZ uyanı çeker, gerisi altından
    geçer — sıralama hattının çalışma prensibi budur.
    """
    nbt = f'{{Filter:{{id:"{filter_item}",count:1}}}}' if filter_item else None
    return block("create:brass_belt_funnel", facing=facing, shape=shape,
                 powered=powered, nbt=nbt)


# --------------------------------------------------------------------------
# Modül 6: tarım
# --------------------------------------------------------------------------


def mechanical_saw(facing: str, axis_along_first: bool = True, flipped: bool = False) -> str:
    """SawBlock extends DirectionalAxisKineticBlock -> facing + axis_along_first + flipped.

    YATAY testere (facing yatay) — ağaç/bitki keser:
        getRotationAxis   = FACING ekseni
        hasShaftTowards   = YALNIZ facing.getOpposite()  -> mil ARKADAN gelir
    Create'in kendi ponder sahnesi (mechanical_saw/breaker.nbt) bunu doğruluyor:
        saw [3,1,2] facing=west, kesilen gövde [2,1,2], mil [4,1,2] axis=x

    Kesilen bloklar ItemEntity olarak düşer ve testereden UZAĞA doğru itilir
    (SawBlockEntity.dropItemFromCutTree: hız = breakingPos - sawPos), o yüzden
    toplama bandı testerenin karşı tarafına konur.
    """
    return block("create:mechanical_saw", facing=facing,
                 axis_along_first=axis_along_first, flipped=flipped)


DIRT = "minecraft:dirt"
SAND = "minecraft:sand"
OAK_SAPLING = "minecraft:oak_sapling[stage=0]"
BAMBOO = "minecraft:bamboo[age=0,leaves=none,stage=0]"
SUGAR_CANE = "minecraft:sugar_cane[age=0]"


def mechanical_press(facing: str) -> str:
    """MechanicalPressBlock extends HorizontalKineticBlock -> facing (yatay).

    getRotationAxis  = facing ekseni
    hasShaftTowards  = face.getAxis() == facing ekseni  -> HER İKİ yandan mil
                       alır, yani aynı eksende dizilen presler tek hat olur.

    Geometri (Create'in `mechanical_press/pressing` ponder sahnesi):
        bant [.,1,.] · boşluk [.,2,.] · pres [.,3,.]
    yani pres bandın **2 blok üstünde**, aradaki blok boş.
    """
    return block("create:mechanical_press", facing=facing)
