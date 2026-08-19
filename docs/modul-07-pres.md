# Modül 7 — Yardımcı üretim (pres hattı)

`out/07_press.schem` (WorldEdit) · `out/07_press.nbt` (Structure Block / Create Print)
**11 × 6 × 7** blok (X × Y × Z), 59 blok · **1.024 SU** @ 64 RPM

Fabrikanın kalan girdi açığını kapatır.

```
#c:ingots/gold  --pressing-->  create:golden_sheet   ← modül 4'ün başlangıç maddesi
#c:ingots/iron  --pressing-->  create:iron_sheet
```

---

## Pres geometrisi (kaynak doğrulaması)

Create'in kendi `mechanical_press/pressing` ponder sahnesi:

```
[2,1,2] create:belt              ← bant
[2,2,2] (boş)                    ← aradaki blok boş kalmalı
[2,3,2] create:mechanical_press{facing:north}
[2,3,3] create:cogwheel{axis:z}  ← tahrik
```

`MechanicalPressBlock`:

```java
public Axis getRotationAxis(BlockState state) { return state.getValue(HORIZONTAL_FACING).getAxis(); }
public boolean hasShaftTowards(..., Direction face) {
    return face.getAxis() == state.getValue(HORIZONTAL_FACING).getAxis();
}
```

→ Pres milini **iki yanından** da alır, yani aynı eksende dizilen presler tek
şaft hattının parçası olur. İki hattın presi bu sayede tek milden dönüyor.

---

## Giriş / çıkış (şematik koordinatı)

| Ne | Koordinat |
|---|---|
| **Güç girişi** | `(0, 5, 2)` |
| Altın külçe girişi | `(0, 2, 0)` |
| Golden sheet çıkışı | `(10, 0, 0)` |
| Demir külçe girişi | `(0, 2, 4)` |
| Iron sheet çıkışı | `(10, 0, 4)` |

### Modül 1'e bağlama

Modül 1'i **P**'ye bastıysan modül 7'yi **P + (32, 5, 26)**'ya bas; güç girişi
modül 1'in **6 numaralı** dalıyla (`P + (31,10,28)`) hizalanır.

---

## Kapsam dışı bıraktıklarım

İlk istekte modül 7 için "sıvı sistemleri, sequenced assembly hatları"
yazıyordu. Durum şöyle:

* **Sequenced assembly** zaten **modül 4**'te kuruldu (precision mechanism,
  15 istasyon).
* **Sıvı sistemi** zaten **modül 1**'de var (3 bağımsız boru ağı, pompalar,
  kendini yenileyen havuz, 192 mB/t).
* Geriye kalan asıl açık **golden sheet** idi — bu modül onu kapatıyor.

**Blaze cake hattı eklenmedi.** Modül 1'in Level 18'de kalması için blaze cake
gerekiyor (seething = 2 ısı). Cinder flour → blaze cake zincirinin tarif
dosyalarını hızlıca bulamadım ve **tahmin etmek istemedim**. Tarif yollarını
birlikte doğrularsak bu hattı da eklerim; o zamana kadar modül 1 kömürle
Level 10'da çalışır (≈163.840 SU, yine fazlasıyla yeterli).
