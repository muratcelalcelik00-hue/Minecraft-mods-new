# Create Fabrika Şematikleri (MC 1.21.1 / Create 6.x)

Create 6.x için modüler, büyük ölçekli bir fabrika kompleksinin WorldEdit
şematiklerini üreten Python projesi. Her modül ayrı bir `.schem` dosyasıdır ve
tek başına paste edilip test edilebilir.

**Durum:** Modül 1 (Güç) hazır. Diğer modüller, modül 1 oyunda onaylandıktan
sonra eklenecek.

---

## Çıktı formatı

Her modül **iki formatta** üretilir:

| Dosya | Format | Nerede kullanılır |
|---|---|---|
| `out/*.schem` | **Sponge Schematic v2** (NBT kökü `Schematic`, `Version: 2`) | WorldEdit 7.3.x (`//schem load` + `//paste`) |
| `out/*.nbt` | **Vanilla structure** (`size`/`blocks`/`palette`/`DataVersion`) | Vanilla Structure Block **veya** Create Schematic Table + Schematicannon |

| | |
|---|---|
| Kütüphane | [`mcschematic`](https://pypi.org/project/mcschematic/) (Sponge v2 yazar), structure `.nbt` için `nbtlib` |
| DataVersion | **3955** (Minecraft 1.21.1) |
| Blok verisi | Tam BlockState (`create:belt[facing=east,part=start,slope=horizontal,casing=false]` gibi) |
| Block entity | Gereken yerlerde; `.nbt` tarafında BE tipi registry adıyla (`AllBlockEntityTypes`'tan doğrulandı) |

`Metadata.WEOffset*` sıfırdır: şematiğin **minimum köşesi** paste konumuna gelir.
`.nbt` tarafında da koordinatlar (0,0,0)'a normalize edilir.

Sadece bir format istersen: `build.py --format schem` / `--format nbt`.

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

### Oyuna aktarma — 3 yol

#### A) Structure Block (mod gerekmez, bedava, anında) — **en kolayı**

`.nbt` dosyasını dünyanızın klasörüne koyun:

```
.minecraft/saves/<DÜNYA ADI>/generated/minecraft/structures/01_power.nbt
```

*(`generated/minecraft/structures` klasörleri yoksa elle oluşturun.)*

Oyunda (creative + cheats açık):

```
/give @s structure_block
```

Structure block'u yerleştirin → sağ tık → mod'u **LOAD** yapın → isim kutusuna
`01_power` yazın → **LOAD** → sonra **PLACE**.

Yapı, structure block'un **1 blok yukarısından** başlayarak +X/+Z yönünde
basılır (offset'i blok arayüzünden ayarlayabilirsiniz). Vanilla structure
block sınırı 48×48×48'dir; modüller bu sınırın altında tutuluyor.

#### B) WorldEdit (`.schem`)

1. `out/*.schem` → `config/worldedit/schematics/`
   *(sunucuda `plugins/WorldEdit/schematics/` olabilir)*
2. Yapının **kuzeybatı-alt köşesinin** geleceği yerde durun:

   ```
   //schem load 01_power
   //paste -a
   ```

   `-a` havayı atlar (arazi silinmez). Düz zeminde `-a` ile basın; engebeli
   yerde `-a` olmadan basmak motor boşluğu gibi boş kalması gereken yerleri
   de temizler.

#### C) Create Schematicannon (`.nbt`, ek mod gerekmez)

1. `out/*.nbt` → `.minecraft/schematics/` (oyun klasörünün kökü, `config/` değil)
2. **Schematic Table**'a boş bir Schematic koyup listeden `01_power` seçin ve yazdırın
3. Yazılı Schematic'i elinize alıp sağ tıkla konumlandırın
4. **Schematicannon**'a Schematic'i + barut (yakıt) + malzemeleri verin

> Bu yol yapıyı **gerçekten inşa eder**, yani tüm blokların malzemesi gerekir.
> Creative'de test için topun yanına **Creative Crate** koyup malzeme
> besleyebilirsiniz. Hızlı test için A veya B yolu çok daha pratik.

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
