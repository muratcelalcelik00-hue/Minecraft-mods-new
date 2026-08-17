# Modül 1 — Güç

`out/01_power.schem` (WorldEdit) · `out/01_power.nbt` (Structure Block / Create)
**32 × 14 × 30** blok (X × Y × Z)

Level 18 boiler, 18 steam engine ve modül başına clutch + gearshift içeren ana
şaft hattı. Su ve yakıt beslemesi modülün içindedir; dışarıdan **sadece yakıt**
(blaze cake veya kömür) ister.

---

## Ne üretiyor

| | |
|---|---|
| **Ana ağ kapasitesi** | **294.912 SU @ 64 RPM** (18 motor × 16.384 SU) |
| Kazan seviyesi | **Level 18** (tavan) |
| Boşta duran kapasite | 294.912 SU'nun tamamı — modül 2-7 buradan beslenecek |

### Level 18 nasıl garanti ediliyor

Create'te kazan seviyesi üç limitin en küçüğüdür (`BoilerData.getActualHeat`):

| Limit | Formül | Bu yapıda | Sonuç |
|---|---|---|---|
| Boyut | `min(18, tank_blok / 4)` | 5×5×4 = **100 blok** | 25 → **18** ✅ |
| Su | `min(18, ceil(mB/t) / 10)` | 3 ağ × 64 = **192 mB/t** | 19 → **18** ✅ |
| Isı | blaze burner toplamı | 10 × seething = **20** | **18**'e kırpılır ✅ |

Payların büyüklüğü:

* **Boyut:** 28 blok fazla (72 yeterdi, 100 var) — hiç sorun çıkarmaz.
* **Su:** 12 mB/t fazla (180 gerekiyor, 192 var).
* **Isı:** 2 puan fazla. Yani **1 burner sönerse** ısı 18'e iner ve seviye
  korunur; 2 burner sönerse seviye 16'ya düşer. Yakıt akışı devam ettiği
  sürece bu olmaz, ama en dar pay budur.

---

## İki ayrı kinetik ağ (kasıtlı)

### A) Bootstrap ağı — 10 su çarkı @ 8 RPM

| | Blok | Adet | RPM | SU |
|---|---|---:|---:|---:|
| kaynak | Su çarkı | 10 | 8 | +2.560 |
| yük | Mekanik pompa | 3 | 128 | −1.536 |
| yük | Deployer (yakıt) | 10 | 8 | −320 |
| | **toplam** | | | **1.856 / 2.560 SU — %28 boş** |

### B) Ana ağ — 18 steam engine @ 64 RPM

| | Blok | Adet | RPM | SU |
|---|---|---:|---:|---:|
| kaynak | Steam engine | 18 | 64 | +294.912 |

**Neden ayrı?** Pompalar ve yakıt deployer'ları kazanın *çalışması* için
gerekli. Onları motorlardan beslersek klasik kilitlenme olur: güç bir kez
kesilirse (chunk yeniden yüklenmesi, aşırı yüklenme, yakıt bitmesi) su ve yakıt
durur → kazan söner → motorlar bir daha asla çalışmaz. Su çarkları bedavadır,
tıklama istemez ve her koşulda kendiliğinden döner; bu yüzden yapı her zaman
kendi kendine toparlar.

Bootstrap ağındaki hız değişimi **Rotation Speed Controller** ile yapılır:
8 RPM → RSC (hedef 64) → üstündeki large cogwheel 64 RPM → çapraz kavradığı
küçük dişli 128 RPM → pompalar. Deployer'lar 8 RPM tarafında kalır; 128 RPM'de
olsalardı tek başlarına 5.120 SU çekerlerdi.

---

## Giriş / çıkış noktaları

Koordinatlar **şematik koordinatıdır**: `//paste` sonrası yapının minimum
köşesi (0, 0, 0) kabul edilir; yani durduğunuz noktaya göre relatiftir.

### Girişler

| Ne | Koordinat | Açıklama |
|---|---|---|
| **Yakıt #1** (kuzey hattı) | `(23, 12, 10)` | Vault sırasının üstündeki andesite funnel. Yukarıdan item kabul eder. |
| **Yakıt #2** (güney hattı) | `(23, 12, 16)` | Aynısı, güney hattı için. |
| Su | — | **Gerek yok.** Havuz (13-15, 10, 11-15) kendi kendini yeniler, su çarkı deposu da kapalı devre. |

**Yakıt seçimi** (`BoilerHeaters.blazeBurner`):

| Yakıt | Burner durumu | Isı / burner | 10 burner ile toplam | Kazan seviyesi |
|---|---|---:|---:|---|
| **Blaze cake** | `seething` | **2** | 20 | **18** (tavan) |
| Kömür / odun kömürü / blaze rod | `kindled` | 1 | 10 | 10 |

Şematik burner'ları `seething` olarak basar; yani **blaze cake ile beslendiği
sürece** Level 18'de kalır. Kömürle çalıştırırsanız seviye 10'a düşer
(≈163.840 SU) — çalışır ama tam güç vermez.

Yakıt zinciri: `item vault sırası → chute → deployer → blaze burner`.
Vault'lar aynı eksende bitişik olduğu için **tek envanter** oluşturur; bir
hattın herhangi bir vault'una atılan yakıt 5 deployer'a birden dağılır.
Deployer sadece burner'ın yakıta ihtiyacı olduğunda tüketir
(`tryUpdateFuel`, `remainingBurnTime > INSERTION_THRESHOLD` ise reddeder), yani
yakıt boşa gitmez.

### Çıkışlar

| Ne | Koordinat | Açıklama |
|---|---|---|
| Modül 2 güç çıkışı | `(31, 10, 18)` | 64 RPM şaft ucu |
| Modül 3 güç çıkışı | `(31, 10, 20)` | |
| Modül 4 güç çıkışı | `(31, 10, 22)` | |
| Modül 5 güç çıkışı | `(31, 10, 24)` | |
| Modül 6 güç çıkışı | `(31, 10, 26)` | |
| Modül 7 güç çıkışı | `(31, 10, 28)` | |

Her dalda sırayla: **gearbox** (x=28, ana hat üstünde) → **clutch** (x=29) →
**gearshift** (x=30) → **çıkış şaftı** (x=31).

* **Clutch**: redstone verilince o modülün gücünü keser (bakım / durdurma).
* **Gearshift**: redstone verilince o modülün yönünü ters çevirir.
* İkisi de şematikte `powered=false` (yani bağlı ve ileri yönde) basılır.
  Kolları/redstone hattını kendiniz eklemelisiniz — kaldıraçları modülün
  kendisi basmıyor, çünkü bitişik iki bloğa tek kaldıraç ikisini birden
  tetikleyebiliyor.

---

## Yerleşim haritası (şematik koordinatı)

```
        Z=3   su çarkı bankası (10 çark, X=1..10, Y=4)
              kaynak su sırası Y=5, Z=4 ; düşen su Z=2 ; havuz tabanı Y=0
                    │
        X=18  dikey dişli kulesi (Y=4..11)  ── gücü boiler katına taşır
                    │
   ┌────────────────┴──────────────────────────────────────────┐
   │  X=13..15  su havuzu (15 kaynak blok, Y=10, Z=11..15)     │
   │  X=16..18  boru + X=19 pompa + X=20 boru  (Z=11 / 13 / 15)│  ← 3 AYRI ağ
   │  X=19,Y=11 RSC (hedef 64) · X=19,Y=12 large cogwheel      │
   └───────────────────────────────────────────────────────────┘
                    │
   X=21..25, Y=10..13, Z=11..15   ►  TANK 5×5×4 (100 blok)
   X=21..25, Y=9,     Z=11 ve 15  ►  10 × blaze burner (seething)
   X=21..25, Y=9,     Z=10 ve 16  ►  10 × deployer
   X=21..25, Y=10,    Z=10 ve 16  ►  10 × chute
   X=21..25, Y=11,    Z=10 ve 16  ►  10 × item vault  (yakıt tamponu)
   X=23,     Y=12,    Z=10 ve 16  ►  yakıt giriş hunileri

   X=26, Y=10..13, Z=11..15  ►  18 × steam engine (doğuya bakar)
   X=27                      ►  BOŞ KALMALI (motor gövdesi buraya taşar)
   X=28, Y=10..13, Z=11..15  ►  motor şaft hatları (eksen Z)
   X=28, Y=10..13, Z=16      ►  dikey dişli kolonu (4 katı birleştirir)
   X=28, Y=10,     Z=17..29  ►  ANA ŞAFT HATTI + 6 dal
```

---

## Basma yöntemi

En kolayı **vanilla Structure Block**: `01_power.nbt` dosyasını
`saves/<dünya>/generated/minecraft/structures/` altına koyup structure block'u
LOAD moduna alın, isim `01_power`. Mod gerekmez, malzeme istemez, anında basar.
Diğer yollar (WorldEdit / Schematicannon) için ana [README](../README.md).

## Paste sonrası kontrol listesi

1. **Yakıt at.** Kuzey ve güney vault sıralarına birer yığın **blaze cake**
   koyun (funnel'dan üstten atabilirsiniz: `(23, 12, 10)` ve `(23, 12, 16)`).
   Deployer'lar birkaç saniye içinde burner'ları `seething` yapar.
2. **Su çarklarını izleyin.** Kaynak su sırası (Y=5, Z=4) akmaya başlayınca
   10 çark dönmeli. Dönmüyorlarsa suyun çarkların üstünden geçip Z=2'den
   aşağı düştüğünü kontrol edin (WorldEdit bazen akan suyu güncellemez;
   bir kaynak bloğu kırıp yeniden koymak akışı tetikler).
3. **Pompa yönünü kontrol edin.** `(19, 10, 11)`, `(19, 10, 13)`,
   `(19, 10, 15)`. Create pompanın akış yönü dönüş işaretine bağlıdır ve
   şematikten önceden garanti edilemez. Borularda su **havuzdan tanka** doğru
   akmalı. Ters akıyorsa üç pompaya da **wrench** ile bir kez sağ tıklayın.
   *(Yanlış yön zararsızdır: kazan `drain()` çağrısına boş döner, sadece su
   gelmez.)*
4. **Goggle ile kazana bakın.** Tank'a gözlük takıp bakınca
   `Level 18` ve `294.912 SU` yazmalı. Yazmıyorsa:
   * *"Water supply insufficient"* → 3. adım (pompa yönü).
   * *Isı düşük* → yakıt gelmemiş, 1. adıma dönün.
5. **Ana hattı ölçün.** `(31, 10, 18)` ucuna bir **stressometer** takarak
   64 RPM ve 294.912 SU kapasiteyi doğrulayın.

---

## Komşu modüle nasıl bağlanıyor

Modül 2-7 şematikleri, kendi güç girişlerini bu modülün çıkış şaftlarının
hizasına (`X=31`, `Y=10`, `Z=18/20/22/…`) göre konumlandıracak şekilde
üretilecek. Yani modül 2'yi paste ederken onun güç giriş şaftı `(31, 10, 18)`
ile hizalanacak ve iki şaft doğrudan birleşecek.

Ana hattın tamamı **64 RPM**'dir. Bir modülün içinde daha yüksek/düşük hız
gerekiyorsa (örn. crushing wheel'lar için genelde daha düşük), hız değişimi o
modülün *içinde* yapılmalı — ana hatta dokunulmamalı, aksi halde hız çakışması
tüm fabrikayı durdurur.

**Stres bütçesi:** 294.912 SU'nun tamamı boşta. Kabaca dağıtım planı
(modüller geldikçe kesinleşecek):

| Modül | Tahmini SU |
|---|---:|
| 2 — Cevher işleme (crushing wheel çiftleri, fan, press) | ~80.000 |
| 3 — Alaşım (mixer, press, basin) | ~40.000 |
| 4 — Mekanizma (mechanical crafter, deployer, press) | ~40.000 |
| 5 — Depolama/sıralama (belt, tunnel, chute) | ~15.000 |
| 6 — Tarım (harvester, saw, fan) | ~40.000 |
| 7 — Yardımcı (pompa, mixer, sequenced assembly) | ~40.000 |
| | **~255.000 / 294.912** |

---

## Bilinen sınırlar

* **Pompa/çark dönüş yönü** şematikten deterministik değildir (Create yönü
  ağdaki işarete göre belirler). Yukarıdaki 3. adım bunu çözer.
* **Blaze cake üretimi** modül 7'ye ait. O modül gelene kadar yakıtı elle
  besleyeceksiniz; bir yığın blaze cake uzun süre yeter.
* Su çarkı bankası WorldEdit'in su akışını güncellemesine bağlıdır. Şematikte
  yalnız **kaynak** bloklar var (akan su blokları yazılmadı), çünkü akan su
  paste sonrası zaten fizik motoru tarafından üretilir ve bu daha güvenilirdir.
