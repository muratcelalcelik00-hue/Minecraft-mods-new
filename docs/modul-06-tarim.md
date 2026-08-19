# Modül 6 — Tarım

`out/06_farm.schem` (WorldEdit) · `out/06_farm.nbt` (Structure Block / Create Print)
**11 × 6 × 12** blok (X × Y × Z), 104 blok · **1.024 SU** @ 64 RPM

Üç paralel hat, hepsi **contraption gerektirmeden** çalışır.

| Hat | Bitki | Ürün | Yeniden ekim |
|---|---|---|---|
| z=1 | meşe ağacı | kütük, fidan, çubuk, elma | deployer eker |
| z=5 | bambu | yakıt / bambu tahtası / kâğıt | kendi büyür |
| z=9 | şeker kamışı | kâğıt | kendi büyür |

---

## Testere geometrisi (kaynak doğrulaması)

Create'in kendi ponder sahnesi `mechanical_saw/breaker.nbt`:

```
[2,1,2] minecraft:oak_log        ← kesilen gövde
[3,1,2] create:mechanical_saw{facing:west, axis_along_first:true}
[4,1,2] create:shaft{axis:x}     ← mil ARKADAN
```

`SawBlock`:

```java
public Axis getRotationAxis(BlockState state) {
    return isHorizontal(state) ? state.getValue(FACING).getAxis() : super...;
}
public boolean hasShaftTowards(..., Direction face) {
    return isHorizontal(state) ? face == state.getValue(FACING).getOpposite() : super...;
}
```

→ Testere bitkinin **altına değil, yanına** gelir; ona bakar ve mili **yalnız
arkasından** alır.

## Toplama neden batıda

`SawBlockEntity.dropItemFromCutTree`:

```java
entity.setDeltaMovement(Vec3.atLowerCornerOf(breakingPos.subtract(this.worldPosition))
    .scale(distance / 20f));
```

Düşen item **testereden uzağa** itilir ve ne kadar yüksekten kesilirse o kadar
uzağa gider. Bu yüzden testere bitkinin doğusunda, toplama bandı batısında;
bandın iki yanına da itemler hattan çıkmasın diye kenarlık konuldu.

## Ağaç: fidan neden yandan ekiliyor

Deployer gövdenin **üstüne** konsaydı ağaç büyüyemezdi (fidanın üstünde boş yer
lazım). Bu yüzden deployer fidan konumunun **yanında** duruyor ve fidanı oraya
yerleştiriyor; gövde dikey olarak serbest kalıyor.

---

## Giriş / çıkış (şematik koordinatı)

| Ne | Koordinat |
|---|---|
| **Güç girişi** | `(10, 2, 0)` — eksen Z |
| Meşe ağacı çıkışı | `(0, 1, 1)` |
| Bambu çıkışı | `(0, 1, 5)` |
| Şeker kamışı çıkışı | `(0, 1, 9)` |
| **Fidan girişi** | `(6, 5, 1)` |

Fidan girişi: ağacın kendi yaprakları fidan düşürür, o da çıkış vault'una gider.
Modül 5'e bir `minecraft:oak_sapling` filtre hattı ekleyip buraya geri
yönlendirirsen döngü kapanır.

### Modül 1'e bağlama

Modül 1'i **P**'ye bastıysan modül 6'yı **P + (21, 8, 26)**'ya bas; güç girişi
modül 1'in **5 numaralı** dalıyla (`P + (31,10,26)`) hizalanır.
*(Güç girişi bu modülde Z ekseninde olduğu için ana hattın dal ucuna bir
gearbox ile dönmen gerekir — dal çıkışı X ekseninde.)*

---

## Fabrikaya katkısı

* **Kütük → kömür**: modül 1'in blaze burner'ları kömürle de yanar (kindled=1
  ısı, Level 10). Blaze cake gelene kadar buradan besleyebilirsin.
* **Kütük → tahta → cogwheel**: modül 4'ün cogwheel/large cogwheel ihtiyacı
  andesite alloy (modül 3) + tahta ile karşılanır.
* **Bambu**: fırın yakıtı ve bambu tahtası.
* **Şeker kamışı → kâğıt**: şematik/kitap üretimi.

---

## Buğday neden yok

`create:mechanical_harvester` yalnız **hareketli bir contraption** üstünde
çalışır (mechanical bearing, cart, train). Contraption'lar elle "assemble"
edilmek zorunda olduğu için "paste et ve çalışsın" kuralını bozuyor. Aynı sebep
klasik dönen ağaç çiftlikleri için de geçerli; bu modül contraption'sız
çalışan üç hatla sınırlı tutuldu.

İstersen bearing + harvester'lı bir buğday hattı ayrı bir şematik olarak
eklerim — tek fark, paste sonrası bearing'e bir kez sağ tıklaman gerekmesi.

---

## Paste sonrası kontrol listesi

1. Güç bağla (`(10,2,0)`, eksen Z).
2. `(6,5,1)` funnel'ına birkaç meşe fidanı at.
3. Bambu ve şeker kamışı kendiliğinden büyür; ilk kesim birkaç dakika sürebilir.
4. Testereler dönmeli; kesilen parçalar batıdaki banda düşüp vault'lara gitmeli.
5. Ağaç büyümüyorsa: fidanın üstünde en az 5-6 blok boş yer olduğundan emin ol
   (yapı 6 blok yüksek, üstü açık olmalı).
