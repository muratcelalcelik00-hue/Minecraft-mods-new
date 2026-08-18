# Modül 4 — Mekanizma (Precision Mechanism)

`out/04_mechanism.schem` (WorldEdit) · `out/04_mechanism.nbt` (Structure Block / Create Print)
**21 × 7 × 3** blok (X × Y × Z), 103 blok · **3.840 SU** @ 64 RPM

---

## Tarif (`sequenced_assembly/precision_mechanism.json`)

```
girdi : #c:plates/gold   (create:golden_sheet)
loops : 5
sıra  : deploying cogwheel → deploying large_cogwheel → deploying iron nugget
```

Yani toplam **5 × 3 = 15 deploy** işlemi. Ana çıktı ağırlığı 120/150
(precision mechanism); kalanı golden sheet, andesite alloy, cogwheel, gold
nugget, shaft, crushed raw gold, iron ingot, clock olarak geri döner.

## Tasarım kararı: döngü yok, 15 istasyon

Klasik sequenced assembly kurulumu bandı **döngüye** sokar: item 5 tur atar,
biten ürün filtreli bir funnel'la ayrılır, yarım kalan geri gönderilir. Bu
kurulum bir dönüş yolu, bir filtre ve bir de yükselme (chute/ejector) ister.

Bunun yerine 15 deployer'ı **yan yana** dizdim: item tek geçişte sırayı
tamamlıyor (cog, large cog, nugget, cog, ...). Ne dönüş yolu ne filtre gerekiyor,
ve sıra kendiliğinden doğru.

Deployer'lar `facing=down`, `axis_along_first=true` → dönme ekseni **X**.
Aynı eksenli deployer'lar yan yana gelince birbirine şaft gibi bağlanır, yani
15'i **tek hattan** dönüyor.

## Besleme: ortak depo + filtreli smart chute

15 istasyon üç farklı parça ister. Çözüm:

```
item vault sırası (2..16, y+3)   ← hepsi TEK envanter (aynı eksende bitişik)
        ↓
smart chute  (her biri kendi filtresiyle)
        ↓
deployer → bant
```

`SmartChuteBlockEntity.canAcceptItem` içinde `filtering.test(stack)` var; yani
smart chute ortak depodan **yalnız filtresine uyan** parçayı çeker. Böylece tek
giriş noktası 15 istasyonu doğru şekilde besliyor.

Filtre NBT (`FilteringBehaviour.write`): `nbt.put("Filter", stack.saveOptional(...))`
→ şematikte `{Filter:{id:"create:cogwheel",count:1}}`.

---

## Giriş / çıkış (şematik koordinatı)

| Ne | Koordinat | Açıklama |
|---|---|---|
| **Güç girişi** | `(0, 6, 2)` | 64 RPM, eksen X |
| **Parça girişi** | `(9, 4, 2)` | cogwheel + large cogwheel + iron nugget — **hepsi aynı vault'a** |
| **Altın levha girişi** | `(1, 2, 1)` | `create:golden_sheet` (zincirin başlangıcı) |
| **Ürün çıkışı** | `(20, 0, 2)` | precision mechanism + yan ürünler |

### Modül 1'e bağlama

Modül 1'i **P**'ye bastıysan modül 4'ü **P + (32, 4, 20)**'ye bas; güç girişi
modül 1'in **3 numaralı** dalıyla (`P + (31,10,22)`) birleşir.

### Nereden besleniyor

* **cogwheel / large cogwheel**: andesite alloy'dan (modül 3) + tahta
* **iron nugget**: modül 2'nin yıkama çıktısı — doğrudan uyumlu
* **golden sheet**: altın külçenin mekanik presle dövülmesi (modül 7)

---

## Yerleşim

```
 Y=6  ═══════════════════════  ana tahrik hattı (eksen X)
 Y=4                ▼ parça girişi (funnel)
 Y=3  ███████████████████████  item vault sırası (tek envanter)
 Y=2  ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼          15 × smart chute (filtreli)
 Y=1  ddddddddddddddd          15 × deployer (tek şaft hattı)
 Y=0  ══════════════════════→  bant: altın levha → precision mechanism → vault
      X=1              X=16        X=18   X=20
```

---

## Paste sonrası kontrol listesi

1. Güç bağla (`(0,6,2)`; tek başına test için creative motor).
2. `(9,4,2)` funnel'ına **cogwheel + large cogwheel + iron nugget** at —
   üçünü de aynı deliğe. Smart chute'lar dağıtır.
3. `(1,2,1)` funnel'ına **golden sheet** at.
4. Levhalar bandın üstünde soldan sağa ilerlerken her deployer sırayla vurmalı;
   uçtaki vault'a precision mechanism düşmeli.
5. Bir istasyon boş kalıyorsa: o smart chute'un filtresi ile deployer'ın
   sırasındaki parça uyuşmuyor olabilir — sıra `cog, large cog, nugget` diye
   tekrar eder.

---

## Bilinen sınırlar

* Parçalar **1:1:1** oranında tüketilir. Vault'a orantısız doldurursan bir tür
  biter ve hat o istasyonda bekler (tıkanmaz, sadece yavaşlar).
* Yan ürünler de aynı çıkış vault'una gider; ayırma modül 5'in işi.
* Bant 18 blok — Create'in varsayılan 20 blok sınırının altında.
