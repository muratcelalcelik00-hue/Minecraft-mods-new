# Modül 2 — Cevher işleme

`out/02_ore.schem` (WorldEdit) · `out/02_ore.nbt` (Structure Block / Create Print)
**25 × 8 × 4** blok (X × Y × Z), 93 blok

Crushing wheels → washing → bulk smelting. Girdi ham cevher, çıktı metal.

---

## Zincir (tarifler kaynaktan doğrulandı)

```
raw iron  --crushing (400 tick)-->  crushed raw iron  + %75 experience nugget
crushed   --splashing----------->  9 iron nugget      + %75 redstone
crushed   --blasting------------>  külçe
```

Bant **seri** dizilmiştir: önce yıkama (X=12), sonra eritme (X=17) istasyonundan
geçer. Yıkanan parça nugget'a döner ve eritme bölgesinden etkilenmeden geçer;
yıkanmayı ıskalayan parça eritilip külçe olur. Yani bandın ucuna her hâlükârda
metal gelir, ara ürün birikmez.

Aynı düzen raw copper / raw gold / raw zinc için de çalışır — tarifler
`c:raw_materials/*` tag'i üzerinden eşleştiği için filtre gerekmez.

---

## Stres

| Blok | Adet | RPM | SU |
|---|---:|---:|---:|
| Crushing wheel | 2 | 64 | 1.024 |
| Encased fan | 2 | 64 | 256 |
| Deployer (yakıt) | 1 | 64 | 256 |
| **toplam** | | | **1.536 SU** |

Modül 1'in 294.912 SU'luk hattında bu hiçbir şey — ana bütçenin %0,5'i.

---

## Giriş / çıkış noktaları

Koordinatlar şematik koordinatıdır (min köşe = paste noktası).

| Ne | Koordinat | Açıklama |
|---|---|---|
| **Güç girişi** | `(0, 7, 2)` | 64 RPM, eksen X. Modül 1'in dal çıkışına bağlanır. |
| **Hammadde girişi** | `(6, 5, 2)` | Vault üstündeki funnel. Raw iron/copper/gold/zinc. |
| **Eritme yakıtı** | `(16, 5, 2)` | Kömür yeter (burner'ın yanıyor olması kâfi). |
| **Ürün çıkışı** | `(24, 0, 2)` | Item vault: nugget + redstone + külçe + XP nugget. |

### Modül 1'e bağlama

Modül 1'i **P** noktasına bastıysan, modül 2'yi **P + (32, 3, 16)** noktasına
bas. O zaman modül 2'nin güç giriş şaftı, modül 1'in 1 numaralı dal çıkışıyla
(`P + (31,10,18)`, clutch+gearshift'in arkası) yan yana gelir ve iki şaft
doğrudan birleşir.

Kalan 5 dal (`z = 20/22/24/26/28`) modül 3-7 için boşta.

---

## Yerleşim (şematik koordinatı)

```
   Y=7   ████████████████████  ana tahrik hattı (eksen X), fanların üstünden
          │        │      │
   Y=5    │    yakıt girişleri (funnel)
   Y=4    │    vault (tampon)
   Y=3    │    chute        FAN(aşağı)      FAN(aşağı)
   Y=2   dişli+gearshift → ÇARK/ÇARK   parmaklık(su)   blaze burner
   Y=1              (ürün düşer)      HAVA            HAVA
   Y=0   ══════════════════════════════════════════  BANT (X=3..22) → çıkış
          X=6 kırma        X=12 yıkama    X=17 eritme        X=24 vault
```

---

## Neden bu geometri (kaynak doğrulaması)

**Fan neden yukarıda?** `AirCurrent.getFlowLimit`, tam blok çarpışma kutusunda
akımı keser, kısmi blokta yüzeyde bitirir. Bant tam blok olmadığı için, fan
aşağıdan üfleseydi akım bandın alt yüzeyinde biterdi ve bandın **üstündeki**
eşyaya ulaşamazdı. Bu yüzden fan yukarıdan aşağı bakar, katalizör arada durur.

**Katalizörler** (`AllFanProcessingTypes.isValidAt`):

| İstasyon | Katalizör | Neden bu |
|---|---|---|
| Yıkama | **waterlogged demir parmaklık** | `create:fan_transparent` tag'inde → akımı kesmez; `getFluidState` su döndürür → splashing |
| Eritme | **yanan blaze burner** | O da fan_transparent; `heat >= FADING` şartını sağlar. Lav kullanılamaz: altı hava olduğu için akıp gider. |

**Crushing wheel çifti**: iki çark aynı eksende, aralarında **1 blok boşlukla**
(`otherWheelPos = pos.relative(side, 2)`). Boşluğa controller kendiliğinden
oluşur — şematikte orası bilerek hava.

**Ters dönüş zorunluluğu**: Create çifti ancak `(speed>0) != (otherSpeed>0)`
ise çalıştırır. Aynı eksenli dişli ızgarası iki taraflı (bipartite) olduğu için
iki çarkın tahrik noktası daima çift mesafededir ve **sadece dişliyle ters yön
elde edilemez**. Bu yüzden bir çarkın miline, yanında kalıcı **redstone bloğu**
olan bir **gearshift** konmuştur (`powered=true` → yönü çevirir).
`build.py` bunu her üretimde işaret yayılımıyla doğruluyor:

```
✓ crushing wheel çifti (6, 12, 1)/(6, 12, 3) ters yönde dönüyor
```

---

## Paste sonrası kontrol listesi

1. **Güç bağla.** Modül 1'e bitişik bastıysan otomatik. Tek başına test
   ediyorsan `(0,7,2)`'deki şafta bir **creative motor** tak (64 RPM'e ayarla).
2. **Yakıt at.** `(16,5,2)` funnel'ına kömür/odun kömürü. Deployer blaze
   burner'ı yakana kadar eritme istasyonu çalışmaz (yıkama etkilenmez).
3. **Hammadde at.** `(6,5,2)` funnel'ına raw iron.
4. **İzle.** Çarklar dönmeli, ezilen cevher bandın üstüne düşmeli, yıkama
   fanının altında nugget'a dönmeli, uçtaki vault'a düşmeli.
5. Çarklar dönmüyorsa: aynı yönde dönüyor olabilirler → gearshift'in yanındaki
   redstone bloğunun yerinde olduğunu kontrol et `(5,3,3)`.

---

## Bilinen sınırlar

* **XP nugget'lar** da bandın ucundaki vault'a gider (ayrıştırma yok).
  Sıralama modül 5'in işi.
* Blaze burner yakıtsız kalırsa **eritme durur ama yıkama çalışmaya devam eder**;
  yani hat tıkanmaz, sadece yıkanmamış parçalar işlenmeden çıkışa gider.
* Bant 20 blok — Create'in varsayılan `maxBeltLength` sınırıyla aynı. Uzatmak
  istersen ikinci bir bant + funnel gerekir.
