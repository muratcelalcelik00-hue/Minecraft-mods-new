# Birleşik Kompleks

`out/00_complex.schem` (WorldEdit) · `out/00_complex.nbt` (Create Print)
**75 × 18 × 63** blok · **15,190 blok** · .nbt 44 KB

Yedi modülün tamamı tek şematikte, güç dağıtım hatları döşenmiş ve hepsi bir
fabrika binasının içinde.

---

## Neden modül dokümanlarındaki ofsetler kullanılmadı

Her modül dokümanındaki paste ofseti, o modülü **kendi güç dalına** hizalamak
için hesaplanmıştı. Hepsini aynı anda yerleştirince modüllerin hacimleri
birbiriyle kesişiyordu (örn. modül 2 x44..68/z16..19 ile modül 3 x32..45/z16..23).

Gerçek bir fabrikada modüller ayrı hollere konur ve güç onlara **şaft hattıyla**
götürülür. Burada yapılan da bu: modüller çakışmayan hollere yerleştirildi,
modül 1'in altı dalı her birine kadar döşendi.

## Güç dağıtımı

* dal 1 -> 02_ore güç girişi (44, 7, 2)
* dal 2 -> 03_alloy güç girişi (44, 6, 12)
* dal 3 -> 04_mechanism güç girişi (44, 6, 22)
* dal 4 -> 05_storage güç girişi (44, 5, 27)
* dal 5 -> 06_farm güç girişi (54, 2, 34)
* dal 6 -> 07_press güç girişi (44, 5, 52)

Her dal **kendi X kolonunu** kullanır (x=33+dal), böylece hatlar birbirine
değmez. Köşelerde gearbox ekseni üçüncü eksendir (`hasShaftTowards`:
`face.getAxis() != AXIS`).

> Bu yerleşimde bir hata yakalandı ve düzeltildi: modül 6'nın Z koridoru
> başlangıçta y=10'dan geçiyordu ve modül 7'nin X hattını `(37,10,28)`'de
> eziyordu. Doğrulayıcı bunu "modül 6 ayrı kinetik ağda" diye raporladı;
> koridor modülün giriş yüksekliğine indirildi. Router artık sessizce ezmiyor,
> çakışmada hata veriyor.

## İki kinetik ağ (kasıtlı)

| Ağ | İçerik | Hız |
|---|---|---|
| **Ana** (575 blok) | 18 steam engine → 6 dal → 6 modülün tamamı | 64 RPM |
| **Bootstrap** (69 blok) | 10 su çarkı → 3 pompa + 10 kazan deployer'ı | 8 / 64 / 128 RPM |

Bootstrap ayrı kalmalı: kazanın suyu ve yakıtı ana ağa bağlansaydı, güç bir kez
kesilince sistem kendini bir daha başlatamazdı.

## Stres

```
### Stres bütçesi — Birleşik kompleks

| | Blok | Adet | RPM | SU |
|---|---|---:|---:|---:|
| kaynak | Steam engine (modül 1) | 18 | 64 | +294,912 |
| yük | Crushing wheel | 2 | 64 | −1,024 |
| yük | Encased fan | 2 | 64 | −256 |
| yük | Deployer (yakıt) | 1 | 64 | −256 |
| yük | Mechanical mixer | 2 | 64 | −512 |
| yük | Deployer (yakıt) | 1 | 64 | −256 |
| yük | Deployer (montaj) | 15 | 64 | −3,840 |
| yük | Mechanical saw | 3 | 64 | −768 |
| yük | Deployer (fidan) | 1 | 64 | −256 |
| yük | Mechanical press | 2 | 64 | −1,024 |
| **toplam** | | | | **8,192 / 294,912 SU (97% boş)** |
```

---

## Fabrika binası

* Taban: cilalı andezit
* Duvarlar: derin arduvaz tuğlası, **y+3..y+4 arası cam pencere kuşağı**
* Çatı: kapalı, altında 8 blokta bir **shroomlight** (ışık 15 — fidanların
  büyümesi için de gerekli)
* Kapı: batı duvarının ortasında 2×3 açıklık

Bina `set_if_empty` ile örüldü, yani hiçbir makine bloğunun üstüne yazmaz.

---

## Basma

| Yol | Çalışır mı |
|---|---|
| **Create Print** (`.nbt`) | ✅ Önerilen. Dosya 44 KB, Create'in 256 KB sınırının altında |
| **WorldEdit** (`.schem`) | ✅ |
| Vanilla Structure Block | ❌ Yapı 75×63, structure block sınırı 48×48×48 |

Boş ve düz bir alana bas; bina kendi tabanını ve duvarlarını getiriyor.

---

## Giriş / çıkış noktaları

Koordinatlar şematik koordinatıdır (min köşe = paste noktası).

| Koordinat | Tür | Ne |
|---|---|---|
| `(34, 11, 21)` | rotation-out | [01_power] modül-2 güç çıkışı |
| `(34, 11, 23)` | rotation-out | [01_power] modül-3 güç çıkışı |
| `(34, 11, 25)` | rotation-out | [01_power] modül-4 güç çıkışı |
| `(34, 11, 27)` | rotation-out | [01_power] modül-5 güç çıkışı |
| `(34, 11, 29)` | rotation-out | [01_power] modül-6 güç çıkışı |
| `(34, 11, 31)` | rotation-out | [01_power] modül-7 güç çıkışı |
| `(26, 13, 13)` | item-in | [01_power] yakıt girişi #1 |
| `(26, 13, 19)` | item-in | [01_power] yakıt girişi #2 |
| `(19, 11, 14)` | fluid-in | [01_power] su alışı |
| `(47, 8, 5)` | rotation-in | [02_ore] güç girişi |
| `(71, 1, 5)` | item-out | [02_ore] ürün çıkışı |
| `(53, 6, 5)` | item-in | [02_ore] hammadde girişi |
| `(63, 6, 5)` | item-in | [02_ore] eritme yakıtı |
| `(47, 7, 15)` | rotation-in | [03_alloy] güç girişi |
| `(48, 4, 13)` | item-in | [03_alloy] andesite_alloy girişi |
| `(60, 1, 13)` | item-out | [03_alloy] andesite_alloy çıkışı |
| `(48, 4, 17)` | item-in | [03_alloy] brass girişi |
| `(60, 1, 17)` | item-out | [03_alloy] brass çıkışı |
| `(51, 4, 16)` | item-in | [03_alloy] eritme yakıtı (pirinç) |
| `(56, 5, 25)` | item-in | [04_mechanism] parça girişi |
| `(48, 3, 24)` | item-in | [04_mechanism] altın levha girişi |
| `(67, 1, 25)` | item-out | [04_mechanism] ürün çıkışı |
| `(47, 7, 25)` | rotation-in | [04_mechanism] güç girişi |
| `(51, 2, 29)` | item-out | [05_storage] precision mechanism deposu |
| `(53, 2, 29)` | item-out | [05_storage] brass ingot deposu |
| `(55, 2, 29)` | item-out | [05_storage] andesite alloy deposu |
| `(57, 2, 29)` | item-out | [05_storage] iron ingot deposu |
| `(59, 2, 29)` | item-out | [05_storage] copper ingot deposu |
| `(61, 2, 29)` | item-out | [05_storage] zinc ingot deposu |
| `(63, 2, 29)` | item-out | [05_storage] iron nugget deposu |
| `(65, 2, 29)` | item-out | [05_storage] redstone deposu |
| `(67, 2, 29)` | item-out | [05_storage] experience nugget deposu |
| `(49, 3, 29)` | item-in | [05_storage] karışık girdi |
| `(70, 1, 30)` | item-out | [05_storage] taşma / sınıflandırılmamış |
| `(47, 6, 30)` | rotation-in | [05_storage] güç girişi |
| `(47, 2, 38)` | item-out | [06_farm] mese_agaci çıkışı |
| `(53, 6, 38)` | item-in | [06_farm] fidan girişi |
| `(47, 2, 42)` | item-out | [06_farm] bambu çıkışı |
| `(47, 2, 46)` | item-out | [06_farm] seker_kamisi çıkışı |
| `(57, 3, 37)` | rotation-in | [06_farm] güç girişi |
| `(47, 3, 53)` | item-in | [07_press] golden_sheet girişi |
| `(57, 1, 53)` | item-out | [07_press] golden_sheet çıkışı |
| `(47, 3, 57)` | item-in | [07_press] iron_sheet girişi |
| `(57, 1, 57)` | item-out | [07_press] iron_sheet çıkışı |
| `(47, 6, 55)` | rotation-in | [07_press] güç girişi |

---

## Paste sonrası kontrol listesi

1. **Yakıt**: kazanın iki vault'una blaze cake (Level 18) veya kömür (Level 10);
   modül 2'nin eritme burner'ına ve modül 3'ün pirinç burner'ına kömür.
2. **Pompa yönü**: modül 1'in üç pompası — su havuzdan tanka akmalı, ters ise
   wrench ile birer tık.
3. **Su çarkları** dönüyor mu (bootstrap ağı buna bağlı).
4. **Goggle ile kazana bak**: `Level 18` + `294.912 SU`.
5. Hammaddeleri ilgili giriş funnel'larına at (yukarıdaki tablo).

Modül bazlı ayrıntılar için ilgili modül dokümanlarına bak.
