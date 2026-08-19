# Create 6.x (1.21.1) — doğrulama notları

Bu projedeki hiçbir registry adı, blockstate property'si veya SU değeri
tahminle yazılmadı. Hepsi Create'in **`mc1.21.1/dev`** dalındaki kaynak
kodundan okundu. Aşağıda her iddianın kaynağı var; kendiniz kontrol etmek
isterseniz dosya yolları doğrudan
`https://github.com/Creators-of-Create/Create/blob/mc1.21.1/dev/<yol>`
altında.

---

## 1. Kazan (boiler)

`src/main/java/com/simibubi/create/content/fluids/tank/BoilerData.java`

```java
private static final int waterSupplyPerLevel = 10;
private static final float passiveEngineEfficiency = 1 / 8f;

public int getMaxHeatLevelForBoilerSize(int boilerSize) {
    return (int) Math.min(18, boilerSize / 4);
}
public int getMaxHeatLevelForWaterSupply() {
    return (int) Math.min(18, Mth.ceil(waterSupply) / waterSupplyPerLevel);
}
private int getActualHeat(int boilerSize) {
    return Math.min(activeHeat, Math.min(getMaxHeatLevelForWaterSupply(),
                                         getMaxHeatLevelForBoilerSize(boilerSize)));
}
public float getEngineEfficiency(int boilerSize) {
    ...
    return attachedEngines <= actualHeat ? 1 : (float) actualHeat / attachedEngines;
}
```

Sonuçlar:

| İddia | Kaynak |
|---|---|
| Maksimum seviye **18** | `Math.min(18, …)` |
| Level 18 için **≥ 72 tank bloğu** | `boilerSize / 4 ≥ 18` |
| Level 18 için **≥ 180 mB/t su** | `waterSupply / 10 ≥ 18` |
| Su ölçümü **5 tick'lik örneklerin tepe değeri** | `SAMPLE_RATE = 5`, `supplyOverTime[10]`, `waterSupply = max(...)` |
| Aktif kazan suyu **tüketir, tank dolmaz** | `BoilerData` iç `fill()`: `gatheredSupply += amount; return amount;` — depolamaz, sayar |

### Isı kaynakları

`content/fluids/tank/BoilerHeaters.java`

```java
public static int blazeBurner(Level level, BlockPos pos, BlockState state) {
    HeatLevel value = state.getValue(BlazeBurnerBlock.HEAT_LEVEL);
    if (value == HeatLevel.NONE)             return BoilerHeater.NO_HEAT;   // -1
    if (value == HeatLevel.SEETHING)         return 2;
    if (value.isAtLeast(HeatLevel.FADING))   return 1;
    return BoilerHeater.PASSIVE_HEAT;                                       //  0
}
```

→ **seething (blaze cake) = 2 ısı**, kindled/fading = 1, smouldering = pasif.

Burner'lar `BoilerData.updateTemperature`'da **kazanın taban katmanının tam
1 blok altında ve ayak izinin içinde** taranır:

```java
for (int xOffset = 0; xOffset < controller.width; xOffset++)
  for (int zOffset = 0; zOffset < controller.width; zOffset++)
    BlockPos pos = controllerPos.offset(xOffset, -1, zOffset);
```

---

## 2. Steam engine

`content/kinetics/steamEngine/PoweredShaftBlockEntity.java`

```java
public float getGeneratedSpeed() {
    return getCombinedCapacity() > 0 ? movementDirection * 16 * getSpeedModifier() : 0;
}
private int getSpeedModifier() {
    return (int) (1 + (engineEfficiency >= 1 ? 3 : Math.min(2, Math.floor(engineEfficiency * 4))));
}
public float calculateAddedStressCapacity() {
    return getCombinedCapacity() / getSpeedModifier();   // = efficiency * 1024 / 4
}
```

`AllBlocks.java`:

```java
REGISTRATE.block("steam_engine", SteamEngineBlock::new)
    .transform(CStress.setCapacity(1024.0))
    .onRegister(BlockStressValues.setGeneratorSpeed(64, true))
```

| İddia | Hesap |
|---|---|
| Tam verimde **64 RPM** | `16 × speedModifier(4)` |
| Motor başına **16.384 SU** | kapasite `1024/4 = 256 SU/RPM`, `× 64 RPM` |
| 18 motor → **294.912 SU** | `18 × 16.384` |

> **Dikkat:** Kazanın goggle tooltip'i `16 × max(boilerLevel, attachedEngines) ×
> 1024` gösterir; yani 5 motorla da "294.912 SU" yazabilir. **Gerçekte** üretilen
> kapasite motor başınadır — tam 294.912 SU için 18 motor gerekir.

### Motor geometrisi

`content/kinetics/steamEngine/SteamEngineBlock.java`

```java
public static BlockPos getShaftPos(BlockState sideState, BlockPos pos) {
    return pos.relative(getConnectedDirection(sideState), 2);
}
public static boolean isShaftValid(BlockState state, BlockState shaft) {
    return (AllBlocks.SHAFT.has(shaft) || AllBlocks.POWERED_SHAFT.has(shaft))
        && shaft.getValue(ShaftBlock.AXIS) != getFacing(state).getAxis();
}
// onPlace: FluidTankBlock.updateBoilerState(state, level, pos.relative(getFacing(state).getOpposite()))
```

→ tank motorun **arkasında**, şaft motorun **2 blok önünde**, aradaki blok
**boş**, şaftın ekseni motorun ekseninden **farklı**.

Create'in kendi ponder sahnesi (`assets/create/ponder/steam_engine.nbt`)
bunu birebir doğruluyor: motor `[3,4,3] face=wall,facing=west`, tank
`[4,4,3]`, powered_shaft `[1,4,3] axis=z`, ve kat kat şaft hatlarının uçları
`[1,4..8,7]` konumundaki **dikey cogwheel kolonuyla** birleştiriliyor —
bu modüldeki dişli kolonu aynı desen.

---

## 3. Stres (SU) modeli

`infrastructure/config/CStress.java` + `api/stress/BlockStressValues.java`:
kapasite ve impact değerleri **1 RPM için** tanımlıdır, ağdaki gerçek değer
hıza orantılıdır.

`AllBlocks.java`'dan okunan taban değerler:

| Blok | Değer |
|---|---|
| `steam_engine` | capacity **1024**, üretilen RPM 64 |
| `water_wheel` | capacity **32**, üretilen RPM **8** |
| `large_water_wheel` | capacity **128**, RPM 4 |
| `windmill_bearing` | capacity 512, RPM 16 |
| `mechanical_pump` | impact **4** |
| `deployer` | impact **4** |
| `crushing_wheel` | impact 8 |
| `mechanical_press` | impact 8 |
| `mechanical_mixer` / `mechanical_saw` / `millstone` | impact 4 |
| `encased_fan` | impact 2 |
| `rotation_speed_controller` | `setNoImpact()` — bedava |

---

## 4. Akışkan taşıma

`content/fluids/FluidNetwork.java`

```java
transferSpeed = (int) Math.max(1, pipeConnection.pressure.get(true) / 2f);
...
int flowSpeed = transferSpeed;   // mB / tick, AĞ BAŞINA
```

`content/fluids/pump/PumpBlockEntity.java`: `pressure.set(pull, Math.abs(getSpeed()))`

→ **debi = max(1, pompaRPM / 2) mB/t ve bu değer ağ başınadır.** 256 RPM'de
bile tek ağ 128 mB/t verir; Level 18'in istediği 180 mB/t için **en az 2,
pratikte 3 ayrı boru ağı** gerekir. Bu yüzden modülde 3 pompa ve aralarında
1'er blok boşluk bırakılmış 3 ayrı boru hattı var (bitişik borular birleşir).

`content/fluids/OpenEndedPipe.java`: açık uç yalnızca **kaynak** blok çeker
(`if (fluidState.isEmpty() || !fluidState.isSource()) return empty;`), bloğu
kaldırır. 3×5'lik havuzda her konumun ≥2 kaynak komşusu olduğu için vanilla
sonsuz su kuralıyla anında yenilenir.

`infrastructure/config/CFluids.java`: `mechanicalPumpRange = 16`,
`hosePulleyBlockThreshold = 10000` (yani hose pulley'in "sonsuz" sayması için
10.000 blokluk bir su kütlesi gerekir — bu yüzden hose pulley kullanılmadı).

---

## 5. Kinetik bağlantı kuralları

`content/kinetics/RotationPropagator.java`

```java
// eksen bağlantısı: aynı doğrultuda, iki taraf da o yöne şaft veriyorsa
boolean connectedByAxis = alignedAxes
    && definitionFrom.hasShaftTowards(...) && definitionTo.hasShaftTowards(...);

// büyük dişli -> küçük dişli
if (ICogWheel.isLargeCog(stateFrom) && ICogWheel.isSmallCog(stateTo))
    if (isLargeToSmallCog(...)) return -2f;

// küçük <-> küçük
if (connectedByGears) {
    if (diff.distManhattan(BlockPos.ZERO) != 1) return 0;
    if (direction.getAxis() == definitionFrom.getRotationAxis(stateFrom)) return 0;
    if (definitionFrom.getRotationAxis(stateFrom) == definitionTo.getRotationAxis(stateTo)) return -1;
}

private static boolean isLargeToSmallCog(BlockState from, BlockState to, IRotate defTo, BlockPos diff) {
    // aynı eksen, ortak eksende fark 0, diğer iki eksende |fark| == 1  -> ÇAPRAZ
}
private static boolean isLargeCogToSpeedController(BlockState from, BlockState to, BlockPos diff) {
    // large cog, RSC'nin TAM ÜSTÜNDE (diff == below), cog ekseni yatay,
    // RSC'nin horizontal_axis'i cog ekseninden FARKLI
}
```

Bunların hepsi `createfactory/validate.py` içinde yeniden uygulandı.

Ayrıca: **`PumpBlock implements ICogWheel`** — yani mekanik pompa küçük dişli
gibi kavrar. Modüldeki pompa sırası bu sayede aralarındaki dişlilerle
sürülüyor (Create'in kendi steam_engine ponder'ında da aynı desen var).

`content/kinetics/base/DirectionalAxisKineticBlock.java` (deployer):

```java
if (pistonAxis == Axis.Z) return alongFirst ? Axis.X : Axis.Y;
```

---

## 6. Blockstate property adları (sık yanlış bilinenler)

| Blok | Property'ler | Kaynak |
|---|---|---|
| `create:blaze_burner` | **`blaze`** (none/smouldering/fading/kindled/seething) + `facing` | `EnumProperty.create("blaze", HeatLevel.class)` — `heat_level` **değil** |
| `create:fluid_tank` | `top`, `bottom`, `shape` (plain/window/window_nw/window_sw/window_ne/window_se) | `FluidTankBlock` |
| `create:steam_engine` | `face` (floor/wall/ceiling), `facing`, `waterlogged` | `SteamEngineBlock` |
| `create:deployer` | `facing`, **`axis_along_first`** | `BooleanProperty.create("axis_along_first")` |
| `create:item_vault` | `horizontal_axis`, `large` | `ItemVaultBlock` |
| `create:chute` | `facing` (FACING_HOPPER), `shape` (normal/window/intersection), `waterlogged` | `ChuteBlock` |
| `create:andesite_funnel` | `facing`, `extracting`, `powered` | `FunnelBlock` |
| `create:andesite_belt_funnel` | `facing`, `shape` (pushing/pulling/retracted/extended), `powered` | `BeltFunnelBlock` |
| `create:belt` | `facing`, `part` (start/middle/end/pulley), `slope` (horizontal/upward/downward/vertical/sideways), `casing` | `BeltBlock`, `BeltSlope`, `BeltPart` |
| `create:fluid_pipe` | 6 yön bool + `waterlogged` | `FluidPipeBlock extends PipeBlock` |
| `create:rotation_speed_controller` | `axis` (yalnız x/z) | `horizontalAxisBlockProvider` |
| `create:gearbox` | `axis` | ponder NBT'de doğrulandı |

### Funnel yönü

`FunnelBlock.getStateForPlacement`: `FACING = bakılan yönün tersi`, yani
**funnel bağlı olduğu envanterden DIŞARI bakar**; bağlı envanter
`pos.relative(facing.getOpposite())`.

* `extracting=false` → ağızdan alır, envantere iter (**giriş**)
* `extracting=true` → envanterden çeker, ağızdan verir (**çıkış**)

Create'in `funnels/intro` ponder sahnesi bunu doğruluyor: sandık `[2,2,4]`,
üstündeki funnel `[2,3,4] facing=up, extracting=false`.

---

## 7. Block entity NBT — nereye yazılır, nereye yazılmaz

| Blok | Durum |
|---|---|
| `rotation_speed_controller` | **Yazılır**: `{ScrollValue: <rpm>}` (`ScrollValueBehaviour.write` → `nbt.putInt("ScrollValue", value)`) |
| `create:belt` | **YAZILMAZ.** `BeltBlockEntity.tick()` içinde `if (beltLength == 0) BeltBlock.initBelt(...)` var; bant paste sonrası ilk tick'te blockstate'lerden kendini kurar. NBT'deki `Controller` **dünya koordinatıdır**, şematikte anlamsızdır ve yazılırsa bandı bozar. |
| `create:item_vault`, `create:fluid_tank` | **YAZILMAZ.** Bunlar da `Controller`/`LastKnownPos` gibi mutlak koordinat tutar; boş bırakılınca çok bloklu yapı yerleştirmede yeniden kurulur. |

Bu yüzden şematikte tek bir block entity var (RSC) — geri kalan her şey
blockstate'ten kendini kuruyor. `//paste` sonrası elle "düzeltme" gerekmez.

---

## 8. Kullanılan araçlar

* Kaynak: `raw.githubusercontent.com/Creators-of-Create/Create/mc1.21.1/dev/…`
* Referans yapılar: Create'in kendi **ponder** sahneleri, `.nbt` structure
  dosyaları olarak okundu (`assets/create/ponder/steam_engine.nbt`,
  `water_wheel.nbt`, `deployer/processing.nbt`, `funnels/intro.nbt`,
  `chute/downward.nbt`). Bunlar Create ekibinin "çalıştığını bildiği"
  yerleşimler olduğu için geometri kararlarında referans alındı.

---

## 9. Modül 2 (cevher işleme) doğrulamaları

### Tarifler (`src/generated/resources/data/create/recipe/`)

```json
// crushing/raw_iron.json
{"type":"create:crushing","ingredients":[{"tag":"c:raw_materials/iron"}],
 "processing_time":400,
 "results":[{"id":"create:crushed_raw_iron"},
            {"chance":0.75,"id":"create:experience_nugget"}]}

// splashing/crushed_raw_iron.json
{"type":"create:splashing","ingredients":[{"item":"create:crushed_raw_iron"}],
 "results":[{"count":9,"id":"minecraft:iron_nugget"},
            {"chance":0.75,"id":"minecraft:redstone"}]}
```

Yani zincir: `raw iron → (crushing, 400 tick) → crushed raw iron → (splashing) →
9 iron nugget + %75 redstone`.

### Crushing Wheel çifti — `CrushingWheelBlock.updateControllers`

```java
BlockPos controllerPos = pos.relative(side);
BlockPos otherWheelPos  = pos.relative(side, 2);
...
if (be.getSpeed() > 0) != (otherBE.getSpeed() > 0) && ... controllerShouldBeValid = true;
if (otherState.getValue(AXIS) != state.getValue(AXIS)) controllerShouldExist = false;
```

* İki çark **aynı eksende** ve **aralarında 1 blok boşlukla** durur.
* Boşluğa `create:crushing_wheel_controller` **kendiliğinden** oluşur — şematikte
  oraya blok konmaz, hava bırakılır.
* `side` ekseni çarkın dönme ekseninden farklı olmalı.
* **Çarklar ters yönde dönmek zorunda.** Dişli ağı iki taraflıdır (bipartite):
  aynı eksenli dişli ızgarasında iki nokta arasındaki yön farkı, manhattan
  mesafesinin tek/çift olmasına bağlıdır. İki çarkın tahrik noktası her zaman
  **çift** mesafede olduğu için, sadece dişliyle ters yön elde edilemez;
  yön kıran bir eleman (gearshift veya gearbox) şart.

### Fan işleme — `AirCurrent` + `AllFanProcessingTypes`

Hava akımını **durduran** şey (`AirCurrent.getFlowLimit`):

```java
if (shouldAlwaysPass(state)) continue;          // create:fan_transparent tag'i
VoxelShape shape = state.getCollisionShape(...);
if (shape.isEmpty()) continue;                  // akışkanlar (su/lav) engel değil
if (shape == Shapes.block()) return i;          // TAM blok akımı keser
return Math.min(i + shapeDepth + 1/32d, max);   // kısmi blokta yüzeyde biter
```

**Bunun tasarıma etkisi:** fan YUKARI bakıp bandın altına konamaz. Bandın
çarpışma kutusu tam blok olmadığı için akım bandın alt yüzeyinde biter,
bandın ÜSTÜNDEKİ eşyalara ulaşmaz. Doğru kurulum: **fan yukarıdan aşağı bakar**,
katalizör fanla bant arasındadır.

Katalizör kuralları (`AllFanProcessingTypes.isValidAt`):

| İşlem | Katalizör | Not |
|---|---|---|
| Splashing (yıkama) | su akışkanı | **waterlogged demir parmaklık** işe yarar: `create:fan_transparent` tag'inde olduğu için akımı kesmez, `getFluidState` su döndürür |
| Blasting (eritme) | lav akışkanı **veya** yanan blaze burner | `!hasProperty(HEAT_LEVEL) \|\| heat.isAtLeast(FADING)` |

Lav bu düzende kullanılamaz: fanın altındaki katalizör konumunda lavın altı
hava olacağı için akıp gider. Bu yüzden eritme istasyonu **blaze burner** ile
kurulur (fan_transparent tag'inde olduğu için akımı kesmez) — ve burner'ın
yakıtı yine bir deployer ile beslenir.

`create:fan_transparent` tag'i (doğrulandı): blaze_burner, lit_blaze_burner,
sail_frame, andesite/brass/copper_bars, **minecraft:iron_bars**, copper_grate'ler,
mangrove_roots, `#minecraft:campfires`, `#minecraft:fences`, `#minecraft:leaves`.

---

## 10. Modül 3 (alaşım) doğrulamaları

### Tarifler

```
mixing/andesite_alloy.json : andesite + #c:nuggets/iron -> create:andesite_alloy
mixing/brass_ingot.json    : #c:ingots/copper + #c:ingots/zinc
                             "heat_requirement": "heated"  -> 2 x create:brass_ingot
```

### Isı eşiği — `HeatCondition.testBlazeBurner`

```java
if (this == SUPERHEATED) return level == HeatLevel.SEETHING;
if (this == HEATED)      return level != HeatLevel.NONE && level != HeatLevel.SMOULDERING;
return true;
```

`BasinBlockEntity.getHeatLevelOf(state)` basin'in **below(1)** bloğuna bakar:
blaze burner ise kendi HEAT_LEVEL'i, `passive_boiler_heaters` tag'indeki bir
blok (kamp ateşi, lav, magma) ise **SMOULDERING**.

→ **Kamp ateşi/lav "heated" tarifleri çalıştırmaz.** Pirinç için yakıtlı
blaze burner (kindled) şart.

### Basin

```java
// BasinOperatingBlockEntity
BlockEntity basinBE = level.getBlockEntity(worldPosition.below(2));   // mixer 2 üstte

// BasinBlockEntity.addBehaviours
behaviours.add(new DirectBeltInputBehaviour(this));   // bandın ucu doğrudan besler

// BasinBlock.canOutputTo
BlockPos neighbour = basinPos.relative(direction);
BlockPos output    = neighbour.below();
// neighbour BOŞ olmalı, output DirectBeltInputBehaviour taşımalı

// BasinBlockEntity.updateSpoutput -> FACING'i Create kendi ayarlar
```

### Mechanical mixer

```java
public class MechanicalMixerBlock extends KineticBlock implements IBE<...>, ICogWheel
public Axis getRotationAxis(BlockState state) { return Axis.Y; }
public boolean hasShaftTowards(...) { return false; }
public SpeedLevel getMinimumRequiredSpeedLevel() { return SpeedLevel.MEDIUM; }
```

→ Mixer'a **şaft takılamaz**; yalnız yanındaki Y eksenli küçük dişliyle kavrar.

### Bant, şaft hattını kesmez

`BeltBlock.hasShaftTowards` start/end/pulley segmentleri için, bandın gidiş
yönüne dik yatay eksende `true` döner. Yani bir şaft hattı bir bandın kasnak
segmentinin içinden geçebilir; bant iki yanındaki şaftları 1:1 bağlar.
Doğrulayıcı bunu ve bant zincirinin kendi içinde tek parça döndüğünü modelliyor.

---

## 11. Modül 4 (mekanizma) doğrulamaları

### Precision mechanism — sequenced assembly

`sequenced_assembly/precision_mechanism.json`:

```
ingredient: {"tag": "c:plates/gold"}    loops: 5
adım 1: create:deploying  [incomplete_precision_mechanism, create:cogwheel]
adım 2: create:deploying  [incomplete_precision_mechanism, create:large_cogwheel]
adım 3: create:deploying  [incomplete_precision_mechanism, #c:nuggets/iron]
```

→ 5 × 3 = **15 deploy** işlemi.

### Filtre NBT — `FilteringBehaviour.write`

```java
nbt.put("Filter", getFilter().saveOptional(registries));
nbt.putInt("FilterAmount", count);
```

1.21 ItemStack formatı `{id:"...", count:N}` olduğu için şematikte:
`{Filter:{id:"create:cogwheel",count:1}}`

### Smart chute

`SmartChuteBlock extends AbstractChuteBlock` — tek blockstate property'si
**`powered`** (yön yok, her zaman aşağı). `getStateForPlacement` redstone
sinyalinden okur; sinyal yoksa `false` = **çalışır**.

`SmartChuteBlockEntity`:

```java
public boolean canAcceptItem(ItemStack stack) {
    return super.canAcceptItem(stack) && canActivate() && filtering.test(stack);
}
```

→ Ortak bir depodan yalnız filtreye uyan parçayı çeker. Modül 4'te 15 istasyonu
tek vault sırasından beslemek bu sayede mümkün.

---

## 12. Modül 6 (tarım) doğrulamaları

### Mechanical saw — ağaç/bitki kesme

`SawBlock extends DirectionalAxisKineticBlock` → `facing`, `axis_along_first`,
`flipped`.

```java
public Axis getRotationAxis(BlockState state) {
    return isHorizontal(state) ? state.getValue(FACING).getAxis() : super.getRotationAxis(state);
}
public boolean hasShaftTowards(LevelReader world, BlockPos pos, BlockState state, Direction face) {
    return isHorizontal(state) ? face == state.getValue(FACING).getOpposite()
                               : super.hasShaftTowards(world, pos, state, face);
}
```

Ponder `mechanical_saw/breaker.nbt`: gövde `[2,1,2]`, testere `[3,1,2]
facing=west`, mil `[4,1,2] axis=x` → testere bitkinin YANINDA, mil ARKADA.

### Düşen itemin yönü

```java
public void dropItemFromCutTree(BlockPos pos, ItemStack stack) {
    float distance = (float) Math.sqrt(pos.distSqr(breakingPos));
    ...
    entity.setDeltaMovement(Vec3.atLowerCornerOf(breakingPos.subtract(this.worldPosition))
        .scale(distance / 20f));
}
```

→ Item testereden **uzağa** fırlatılır; yükseklik arttıkça hız artar. Toplama
bandı bu yüzden testerenin karşı tarafına konur.

### Gearbox dallanma sınırı (modül 6'da yakalandı)

`GearboxBlock.hasShaftTowards` = `face.getAxis() != AXIS`. Yani `axis=x` bir
gearbox yalnız **±Y ve ±Z** yüzlerine şaft verir. Tek bir gearbox ile aynı anda
X, Y ve Z'ye dallanmak mümkün değildir — üç eksene birden gitmek için iki
gearbox gerekir. Doğrulayıcı bunu "3 ayrı kinetik ağ" olarak raporlayarak
yakaladı.
