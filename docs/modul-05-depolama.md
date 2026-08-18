# Modül 5 — Depolama + Sıralama

`out/05_storage.schem` (WorldEdit) · `out/05_storage.nbt` (Structure Block / Create Print)
**24 × 6 × 4** blok (X × Y × Z), 72 blok · stres yükü ihmal edilebilir (yalnız bant döner)

Modül 2/3/4'ün karışık çıktısını tek bantta tür tür ayırır.

---

## Nasıl çalışıyor

```
karışık girdi → vault → bant ═══════════════════════════════→ taşma vault'u
                          ▲   ▲   ▲   ▲   ▲   ▲   ▲   ▲   ▲
                        filtreli brass funnel'lar (bandın ÜSTÜNDE)
                          │   │   │   │   │   │   │   │   │
                        her biri kendi 3'lü vault sütununa
```

Filtreli bir brass belt funnel bandın üstünden **yalnız filtresine uyanı**
çeker; eşleşmeyen her şey altından geçip devam eder. Sıralama mantığı bu kadar
basit ve tek NBT alanı istiyor: `{Filter:{id:"...",count:1}}`.

### Neden brass tunnel değil?

Kullanıcı isteğinde "brass tunnel / smart chute" geçiyordu. Brass tunnel'ın
asıl işi **paralel bantlar arasında dağıtım** yapmaktır; çalışması için her yüz
başına ayrı filtre **ve** bir dağıtım modu (split / forced split / round robin /
prefer nearest / randomize / synchronize) NBT'si ister. Buradaki iş "tek bant,
çok hedef" olduğu için filtreli brass funnel hem daha az NBT'yle hem de daha
öngörülebilir şekilde aynı sonucu veriyor. (Smart chute modül 4'te, dikey
filtreleme için kullanıldı.)

---

## Sıralanan türler

| # | Filtre | Nereden gelir |
|---|---|---|
| 1 | `create:precision_mechanism` | modül 4 |
| 2 | `create:brass_ingot` | modül 3 |
| 3 | `create:andesite_alloy` | modül 3 |
| 4 | `minecraft:iron_ingot` | modül 2 (eritme) |
| 5 | `minecraft:copper_ingot` | modül 2 |
| 6 | `create:zinc_ingot` | modül 2 |
| 7 | `minecraft:iron_nugget` | modül 2 (yıkama) |
| 8 | `minecraft:redstone` | modül 2 (yıkama yan ürünü) |
| 9 | `create:experience_nugget` | modül 2 (kırma yan ürünü) |
| — | **taşma** | hiçbirine uymayan her şey |

Tüm item id'leri Create'in kendi tag dosyalarından doğrulandı
(`c:ingots/zinc → create:zinc_ingot`, `c:plates/gold → create:golden_sheet` vb.).

---

## Giriş / çıkış (şematik koordinatı)

| Ne | Koordinat |
|---|---|
| **Güç girişi** | `(0, 5, 1)` |
| **Karışık girdi** | `(2, 2, 0)` |
| precision mechanism | `(5, 1, 0)` |
| brass ingot | `(7, 1, 0)` |
| andesite alloy | `(9, 1, 0)` |
| iron ingot | `(11, 1, 0)` |
| copper ingot | `(13, 1, 0)` |
| zinc ingot | `(15, 1, 0)` |
| iron nugget | `(17, 1, 0)` |
| redstone | `(19, 1, 0)` |
| experience nugget | `(21, 1, 0)` |
| **taşma** | `(23, 0, 1)` |

Her depo sütunu **3 vault yüksekliğinde** — aynı eksende bitişik vault'lar tek
envanter oluşturduğu için üç blok tek büyük depo olarak çalışır. Hatlar
aralarında 1 blok boşluk bırakılarak dizildi ki komşu hatların vault'ları
**birleşmesin**.

### Modül 1'e bağlama

Modül 1'i **P**'ye bastıysan modül 5'i **P + (31, 5, 23)**'e bas; güç girişi
modül 1'in **4 numaralı** dalıyla (`P + (31,10,24)`) hizalanır.

---

## Paste sonrası kontrol listesi

1. Güç bağla (`(0,5,1)`).
2. `(2,2,0)` funnel'ına karışık bir yığın at (örn. modül 2'nin çıkış vault'unu
   boşalt).
3. Bant çalışırken her item kendi sütununa ayrılmalı; tanımadıkları uçtaki
   taşma vault'una gitmeli.
4. Bir tür yanlış yere gidiyorsa o funnel'ın filtresini elle kontrol et
   (funnel'a sağ tık → filtre yuvası).

---

## Genişletme

Yeni bir tür eklemek için `createfactory/modules/storage.py` içindeki
`FILTERS` listesine bir satır ekleyip `build.py --module storage` çalıştırmak
yeterli — hat otomatik uzar. **Dikkat:** bant Create'in varsayılan
`maxBeltLength = 20` sınırına dayandı; daha fazla hat için ikinci bir bant
(uçtan funnel ile devam) gerekir. `build.py` bu sınırı her üretimde kontrol
ediyor.
