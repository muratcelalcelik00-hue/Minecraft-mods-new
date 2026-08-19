# Create Fabrika Şematikleri (MC 1.21.1 / Create 6.x)

Create 6.x için modüler, büyük ölçekli bir fabrika kompleksinin WorldEdit
şematiklerini üreten Python projesi. Her modül ayrı bir `.schem` dosyasıdır ve
tek başına paste edilip test edilebilir.

**Durum:** Modül 1-6 hazır. Modül 7 sırada.

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

#### C) Create'in kendi şematiği — **Print** aracı (ek mod yok, malzeme yok, anında)

Create'in şematik sisteminde, **creative modda** Schematicannon'a hiç gerek
olmadan yapıyı anında basan bir araç var: **Print**.

1. `out/*.nbt` → `.minecraft/schematics/`
   *(oyun klasörünün kökü, `config/` değil — Schematic Table'daki
   **"Open Folder"** düğmesi tam bu klasörü açar)*
2. Creative moda geçin. **Schematic Table** ve **Empty Schematic** alın.
3. Table'a boş schematic'i koyun → listeden `01_power` seçin → yükleyin →
   yazılı Schematic'i alın.
4. Schematic'i elinize alın, yere **sağ tık** — yapının hayaleti görünür
   (*Position* aracı).
5. **Sol Alt** tuşunu basılı tutun → araç menüsü açılır → **Print**'i seçin.
6. **Sağ tık** → yapı anında, tam haliyle basılır.

Kaynak doğrulaması: `ToolType.getTools(creative)` listesine `PRINT` yalnız
creative'de ekleniyor; `SchematicPlacePacket.handle()` `player.isCreative()`
kontrolünden sonra tüm blokları block entity verisiyle birlikte tek seferde
yerleştiriyor. Oyun içi açıklaması: *"Instantly places the structure in the
world. [Right-Click] to confirm placement at the current location."*

> **Not:** `creativePrintIncludesAir` ayarı varsayılan olarak **kapalı**, yani
> Print havayı basmaz (WorldEdit'teki `//paste -a` gibi davranır). Boş/düz bir
> alana basıyorsanız fark etmez. Dolu araziye basacaksanız
> `config/create-server.toml` içinden açabilirsiniz.

#### D) Create Schematicannon (`.nbt`) — yapıyı gerçekten inşa eder

Aynı Schematic item'ı Schematicannon'a + barut + malzemeleri verirseniz top
yapıyı blok blok inşa eder. Survival için doğru yol, ama **tüm blokların
malzemesi gerekir**; hızlı test için C yolu çok daha pratik.

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
| 2 | Cevher işleme (crushing → washing → bulk smelting) | `out/02_ore.schem` / `.nbt` | ✅ hazır — [doküman](docs/modul-02-cevher.md) |
| 3 | Alaşım (andesite alloy, brass) | `out/03_alloy.schem` / `.nbt` | ✅ hazır — [doküman](docs/modul-03-alasim.md) |
| 4 | Mekanizma (precision mechanism) | `out/04_mechanism.schem` / `.nbt` | ✅ hazır — [doküman](docs/modul-04-mekanizma.md) |
| 5 | Depolama + sıralama (vault dizisi, filtreli funnel) | `out/05_storage.schem` / `.nbt` | ✅ hazır — [doküman](docs/modul-05-depolama.md) |
| 6 | Tarım (ağaç, bambu, şeker kamışı) | `out/06_farm.schem` / `.nbt` | ✅ hazır — [doküman](docs/modul-06-tarim.md) |
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
    ore.py         # Modül 2
    alloy.py       # Modül 3
    mechanism.py   # Modül 4
    storage.py     # Modül 5
    farm.py        # Modül 6
build.py           # CLI
docs/
  modul-01-guc.md          # modül dokümanları
  modul-02-cevher.md
  modul-03-alasim.md
  modul-04-mekanizma.md
  modul-05-depolama.md
  modul-06-tarim.md
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
* deployer → blaze burner ve vault → chute → deployer zincirleri,
* **crushing wheel çiftinin ters yönde döndüğü** (Create aynı yönde dönen
  çifti çalıştırmaz; dişli ızgarası iki taraflı olduğu için bu hata kolayca
  yapılır),
* bant zincirleri: en az 2 segment (kısası `initBelt` tarafından kırılır) ve
  `maxBeltLength = 20` sınırı.

---

## Sayılar nereden geliyor?

Bu projedeki **hiçbir registry adı, blockstate property'si veya SU değeri
tahmin edilmemiştir.** Hepsi Create'in 1.21.1 kaynak kodundan doğrulanmıştır;
dosya/satır referansları için [`docs/create-6-dogrulama.md`](docs/create-6-dogrulama.md).

Örnek: blaze burner'ın blockstate property'si `heat_level` değil **`blaze`**'dir
(`EnumProperty.create("blaze", HeatLevel.class)`), ve bir seething burner
kazana **2** ısı verir.
