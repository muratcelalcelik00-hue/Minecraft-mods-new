"""Mr Void'in Dünyası tekstürlerini üretir.

Kullanım (proje kökünden):  python3 tools/tekstur_uret.py
Gereksinim: Pillow  (pip install pillow)
"""
import math
import os
import random

from PIL import Image

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "src", "main", "resources", "assets", "voiddunyasi", "textures")

BOYUT = 16
KARE = 16

# Mor, gri, yeşil, kahverengi — hepsi biraz soluk; aralarında döngüsel kayılır.
PALET = [
    (104, 74, 128),   # soluk mor
    (112, 108, 116),  # morumsu gri
    (86, 110, 84),    # bulanık yeşil
    (112, 88, 66),    # çamurlu kahverengi
]


def paletten(t):
    """t ∈ [0,1) döngüsel; paletteki renkler arasında yumuşak (kosinüs) geçiş."""
    n = len(PALET)
    x = (t % 1.0) * n
    i = int(x)
    f = x - i
    f = (1 - math.cos(f * math.pi)) / 2
    a, b = PALET[i % n], PALET[(i + 1) % n]
    return tuple(a[k] + (b[k] - a[k]) * f for k in range(3))


def doku_gurultusu(rng):
    """16 piksellik periyotla döşenebilir, düşük frekanslı gürültü alanı."""
    dalgalar = []
    for _ in range(6):
        fx, fy = rng.randint(-2, 2), rng.randint(-2, 2)
        if fx == 0 and fy == 0:
            fx = 1
        dalgalar.append((fx, fy, rng.uniform(0, 2 * math.pi), rng.uniform(0.4, 1.0)))

    def alan(x, y):
        s = sum(g * math.sin(2 * math.pi * (fx * x + fy * y) / BOYUT + p) for fx, fy, p, g in dalgalar)
        return s / sum(d[3] for d in dalgalar)

    return alan


def bulanik(piksel, tekrar=2):
    """Kenarları saran 3x3 kutu bulanıklığı."""
    for _ in range(tekrar):
        yeni = [[None] * BOYUT for _ in range(BOYUT)]
        for y in range(BOYUT):
            for x in range(BOYUT):
                t = [0.0, 0.0, 0.0]
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        p = piksel[(y + dy) % BOYUT][(x + dx) % BOYUT]
                        for k in range(3):
                            t[k] += p[k]
                yeni[y][x] = tuple(v / 9 for v in t)
        piksel = yeni
    return piksel


def bilinmeyen_madde():
    rng = random.Random(1337)
    faz = doku_gurultusu(rng)
    parlak = doku_gurultusu(rng)
    gri = (110, 106, 112)
    img = Image.new("RGBA", (BOYUT, BOYUT * KARE))
    for kare in range(KARE):
        zaman = kare / KARE
        piksel = []
        for y in range(BOYUT):
            satir = []
            for x in range(BOYUT):
                # Her piksel paletin farklı bir noktasından başlar ve zamanla kayar.
                renk = paletten(zaman + 0.35 * faz(x, y))
                # Hiçbir renge tam oturmasın: griye doğru çek.
                renk = tuple(renk[k] * 0.72 + gri[k] * 0.28 for k in range(3))
                # Zamanla nefes alan hafif parlaklık dalgası.
                p = 1.0 + 0.10 * parlak(x, y) * math.cos(2 * math.pi * zaman + 1.3 * faz(x, y))
                satir.append(tuple(v * p for v in renk))
            piksel.append(satir)
        piksel = bulanik(piksel)
        for y in range(BOYUT):
            for x in range(BOYUT):
                r, g, b = (max(0, min(255, int(round(v)))) for v in piksel[y][x])
                img.putpixel((x, kare * BOYUT + y), (r, g, b, 255))
    yol = os.path.join(KOK, "block", "bilinmeyen_madde.png")
    img.save(yol)
    print("yazıldı:", yol)


def asa():
    img = Image.new("RGBA", (BOYUT, BOYUT), (0, 0, 0, 0))
    sap_koyu = (38, 26, 20, 255)
    sap = (62, 42, 30, 255)
    sap_acik = (84, 60, 42, 255)

    # Sol alttan sağ üste çapraz sap (vanilya aletleri gibi).
    for i in range(2, 13):
        x, y = i - 1, 16 - i
        img.putpixel((x, y), sap)
        img.putpixel((x + 1, y), sap_koyu)
        if i % 3 == 0:
            img.putpixel((x, y), sap_acik)
    # Sapın dibi
    img.putpixel((0, 15), sap_koyu)

    # Tepede taşı tutan kıskaç
    for p in [(11, 5), (10, 4)]:
        img.putpixel(p, sap_koyu)

    # Sarı taş (3x3 elmas biçimi, ışıltılı)
    tas = {
        (13, 1): (255, 236, 120, 255),
        (12, 2): (255, 222, 64, 255),
        (13, 2): (255, 248, 190, 255),
        (14, 2): (230, 180, 30, 255),
        (11, 3): (240, 196, 40, 255),
        (12, 3): (255, 214, 50, 255),
        (13, 3): (236, 186, 34, 255),
        (14, 3): (196, 140, 20, 255),
        (12, 4): (210, 156, 24, 255),
        (13, 4): (176, 120, 16, 255),
    }
    for p, c in tas.items():
        img.putpixel(p, c)

    yol = os.path.join(KOK, "item", "asa.png")
    img.save(yol)
    print("yazıldı:", yol)


if __name__ == "__main__":
    bilinmeyen_madde()
    asa()
