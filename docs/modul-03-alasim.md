# Modül 3 — Alaşım

`out/03_alloy.schem` (WorldEdit) · `out/03_alloy.nbt` (Structure Block / Create Print)
**14 × 7 × 8** blok (X × Y × Z), 93 blok · **768 SU** @ 64 RPM

İki bağımsız mixer hattı: andesite alloy ve brass.

---

## Tarifler (kaynaktan doğrulandı)

```json
// mixing/andesite_alloy.json          — ısı GEREKMEZ
andesite + #c:nuggets/iron  →  1 × create:andesite_alloy
andesite + #c:nuggets/zinc  →  1 × create:andesite_alloy   (alternatif)

// mixing/brass_ingot.json             — "heat_requirement": "heated"
#c:ingots/copper + #c:ingots/zinc  →  2 × create:brass_ingot
```

Modül 2 ile doğrudan uyumlu: oradan çıkan **iron nugget** andesite alloy
hattına, **copper/zinc külçe** pirinç hattına gider.

---

## Isı: neden kamp ateşi yetmiyor

`HeatCondition.testBlazeBurner`:

```java
if (this == HEATED)
    return level != HeatLevel.NONE && level != HeatLevel.SMOULDERING;
```

`BasinBlockEntity.getHeatLevelOf` ise basin'in **tam altındaki** bloğa bakar:
blaze burner ise kendi ısı seviyesini, kamp ateşi / lav / magma ise yalnız
**SMOULDERING** döndürür. SMOULDERING açıkça reddedildiği için pirinç hattında
**yakıtlı blaze burner** zorunlu — bu yüzden orada bir deployer + yakıt tamponu
var. Andesite alloy hattı ısı istemediğinden çıplak.

---

## Giriş / çıkış (şematik koordinatı)

| Ne | Koordinat | Açıklama |
|---|---|---|
| **Güç girişi** | `(0, 6, 4)` | 64 RPM, eksen X |
| Andesite alloy girişi | `(1, 3, 2)` | andesite + iron/zinc nugget (aynı vault'a ikisi de) |
| Andesite alloy çıkışı | `(13, 0, 2)` | |
| Brass girişi | `(1, 3, 6)` | copper ingot + zinc ingot |
| Brass çıkışı | `(13, 0, 6)` | |
| Pirinç yakıtı | `(4, 3, 5)` | kömür / odun kömürü |

İki bileşen **aynı** vault'a atılır — basin ikisini de kabul eder ve tarif
kendiliğinden eşleşir, filtre gerekmez.

### Modül 1'e bağlama

Modül 1'i **P**'ye bastıysan modül 3'ü **P + (32, 4, 16)**'ya bas; güç girişi
modül 1'in **2 numaralı** dalıyla (`P + (31,10,20)`) birleşir.

---

## Geometri (doğrulanmış kurallar)

```
 Y=6  ═══════════════  ana tahrik hattı (eksen X, z=4)
 Y=3         MIXER              ← şaftı YOK, yandaki Y eksenli dişliyle kavrar
 Y=2         (boş)              ← basin ile mixer arası boş kalmalı
 Y=1  bant→ BASIN               ← bandın ucu doğrudan basin'e item verir
 Y=0         burner (yalnız pirinç hattı) ve çıkış bandı
```

* **Mixer, basin'in tam 2 blok üstünde** (`BasinOperatingBlockEntity`:
  `worldPosition.below(2)`), arada bir blok boşluk.
* **Mixer'a şaft takılamaz**: `hasShaftTowards` her yön için `false`, ve blok
  `ICogWheel`. Yani yalnızca yanına konan **Y eksenli küçük dişli** ile döner.
  İki mixer, aralarındaki dişli zinciriyle tek noktadan sürülüyor.
* **Basin girdisi**: `BasinBlockEntity.addBehaviours` içinde
  `new DirectBeltInputBehaviour(this)` var → bandın **ucu** basin'e dayanınca
  item doğrudan girer, funnel gerekmez.
* **Basin çıkışı** (`BasinBlock.canOutputTo`): yan komşu **boş** olmalı ve
  **onun altı** bant/depot olmalı. Create doğru yönü kendi bulur
  (`updateSpoutput` yatay yönleri tarar ve blockstate'i günceller), o yüzden
  şematikte basin `facing=down` bırakıldı.

### Bant kasnağı hilesi

Bantların kasnakları tek bir Z hattından sürülüyor. Bir bandın start/end
segmenti, gidiş yönüne **dik** yatay eksende şaft kabul eder; yani hattın
üstünden geçen bant, iki yanındaki şaftları 1:1 birbirine bağlar ve hat
kesintiye uğramaz. Böylece 4 bant tek şaft hattıyla dönüyor.

---

## Paste sonrası kontrol listesi

1. **Güç bağla** (modül 1'e bitişikse otomatik; tek başına test için
   `(0,6,4)`'e creative motor).
2. Pirinç hattının yakıt vault'una `(4,3,5)` kömür at → blaze burner yansın.
3. `(1,3,2)`'ye andesite + iron nugget, `(1,3,6)`'ya copper + zinc külçe at.
4. Mixer'lar dönmeli, basin'ler dolup ürünü **doğu** yanındaki alt banda
   dökmeli, bant vault'lara taşımalı.
5. Basin ürünü dökmüyorsa: doğu komşusunun boş, altının bant olduğunu kontrol
   et — Create çıkış yönünü buna göre seçiyor.

---

## Bilinen sınırlar

* Bileşenler **dengeli** beslenmeli. Vault'a sadece andesite atarsan basin
  dolar ve tıkanır; oranı 1:1 tutmak (ya da modül 5'te sıralayıcıyla ayarlamak)
  gerekir.
* Pirinç tarifi 1 copper + 1 zinc → **2 brass** verir; zinc modül 2'den gelir.
* Mixer minimum **MEDIUM** hız ister; 64 RPM fazlasıyla yeterli.
