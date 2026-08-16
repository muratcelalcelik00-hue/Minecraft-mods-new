# Create Fabrika Şematikleri (MC 1.21.1 / Create 6.x)

Create 6.x için modüler, büyük ölçekli bir fabrika kompleksinin WorldEdit
şematiklerini üreten Python projesi. Her modül ayrı bir `.schem` dosyasıdır ve
tek başına paste edilip test edilebilir.

**Durum:** Modül 1 (Güç) hazır. Diğer modüller, modül 1 oyunda onaylandıktan
sonra eklenecek.

---

## Çıktı formatı

| | |
|---|---|
| Format | **Sponge Schematic v2** (NBT kökü `Schematic`, `Version: 2`) |
| Kütüphane | [`mcschematic`](https://pypi.org/project/mcschematic/) (v2 yazar), okuma/denetim için `nbtlib` |
| DataVersion | **3955** (Minecraft 1.21.1) |
| Uyumluluk | WorldEdit 7.3.x — v2 ve v3'ü de okur |
| Blok verisi | Tam BlockState (`create:belt[facing=east,part=start,slope=horizontal,casing=false]` gibi) |
| Block entity | Gereken yerlerde SNBT olarak (`BlockEntities` listesine yazılır) |

`Metadata.WEOffset*` sıfırdır: şematiğin **minimum köşesi** paste konumuna gelir.

---

## Kurulum

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Kullanım

```bash
.venv/bin/python build.py                 # tüm modülleri üret + doğrula
.venv/bin/python build.py --module power  # tek modül
```

Dosyalar `out/` klasörüne yazılır.

### Oyuna aktarma

1. `out/*.schem` dosyalarını sunucu/dünya klasörünüzdeki
   `config/worldedit/schematics/` altına kopyalayın.
   *(Tek oyunculuda: `.minecraft/config/worldedit/schematics/`; sunucuda
   `plugins/WorldEdit/schematics/` veya `config/worldedit/schematics/`.)*
2. Oyunda, yapının **kuzeybatı-alt köşesinin** geleceği yere geçin ve yüzünüzü
   güneye (+Z) dönün — şematikler bu yönde tasarlandı:

   ```
   //schem load 01_power
   //paste -a
   ```

   `-a` havayı atlar, yani mevcut arazi silinmez. Yapıyı tam olarak
   kopyalandığı gibi (hava dahil) basmak isterseniz `-a` olmadan kullanın;
   temiz düz zemine basıyorsanız `//paste -a` yeterlidir.
3. Paste sonrası kontrol listesi için ilgili modül dokümanına bakın.

> **Not:** `//paste` yapının min köşesini ayaklarınızın altındaki bloğa değil,
> **durduğunuz konuma** yerleştirir. Emin olmak için önce `//paste -a -s`
> (seçim olarak göster) deneyebilirsiniz.

---

## Kısıtlar

* **Sadece vanilla Create 6.x + vanilla Minecraft blokları.** Hiçbir addon
  bloğu kullanılmaz; bu yüzden şematikler her addon kurulumuyla uyumludur.
* Güç: **Level 18 boiler + steam engine bankası** (bkz. modül 1).
* Her modül tek başına paste edilip test edilebilir.

---

## Modüller

| # | Modül | Dosya | Durum |
|---|---|---|---|
| 1 | Güç (boiler + engine bankası + ana şaft hattı) | `out/01_power.schem` | ✅ hazır — [doküman](docs/modul-01-guc.md) |
| 2 | Cevher işleme (crushing → washing → bulk smelting) | | beklemede |
| 3 | Alaşım (andesite alloy, brass, zinc) | | beklemede |
| 4 | Mekanizma (kinetic → precision mechanism) | | beklemede |
| 5 | Depolama + sıralama (vault dizisi, brass tunnel) | | beklemede |
| 6 | Tarım (ağaç, kaktüs/bambu, buğday) | | beklemede |
| 7 | Yardımcı (sıvı sistemleri, sequenced assembly) | | beklemede |

---

## Proje yapısı

```
createfactory/
  blocks.py        # doğrulanmış registry adları + blockstate üreticileri
  canvas.py        # ortak yerleştirme katmanı (set/fill/shaft_run/belt_run…)
  stress.py        # SU muhasebesi (kapasite/impact tabloları, kazan formülleri)
  validate.py      # Create'in bağlantı kurallarını yeniden uygulayan denetleyici
  modules/
    power.py       # Modül 1
build.py           # CLI
docs/
  modul-01-guc.md          # modül dokümanı
  create-6-dogrulama.md    # her sayının kaynak koddaki karşılığı
```

### Doğrulama katmanı

`build.py` her üretimden sonra şematiği paste etmeden denetler. Create'in
gerçek kuralları yeniden uygulanır:

* kazan boyut/ısı/su limitleri (`BoilerData`),
* steam engine geometrisi (tank arkada, 1 blok boşluk, 2 blok ileride doğru
  eksende şaft),
* kinetik ağ grafiği (şaft ekseni bağlantısı, küçük↔küçük dişli kavraması,
  büyük↔küçük çapraz kavrama, gearbox, RSC),
* **hız çakışması** (aynı ağda iki farklı RPM buluşursa Create ağı komple
  durdurur — bu hatayı oyunda bulmak çok zordur),
* boru ağlarının yanlışlıkla birleşip birleşmediği (bitişik borular birleşir,
  debi düşer),
* deployer → blaze burner ve vault → chute → deployer zincirleri.

---

## Sayılar nereden geliyor?

Bu projedeki **hiçbir registry adı, blockstate property'si veya SU değeri
tahmin edilmemiştir.** Hepsi Create'in 1.21.1 kaynak kodundan doğrulanmıştır;
dosya/satır referansları için [`docs/create-6-dogrulama.md`](docs/create-6-dogrulama.md).

Örnek: blaze burner'ın blockstate property'si `heat_level` değil **`blaze`**'dir
(`EnumProperty.create("blaze", HeatLevel.class)`), ve bir seething burner
kazana **2** ısı verir.
