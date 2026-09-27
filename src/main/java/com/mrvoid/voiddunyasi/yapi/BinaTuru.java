package com.mrvoid.voiddunyasi.yapi;

/** Ordu binası türleri: taban genişliği (X), derinliği (Z) ve yerden en fazla yüksekliği. */
public enum BinaTuru {
    SPAWNER_BINASI("spawner_binasi", 9, 9, 6, true),
    FABRIKA("fabrika", 15, 11, 18, true),
    PENCERESIZ_KULE("penceresiz_kule", 5, 5, 40, false),
    KAPISIZ_YAPI("kapisiz_yapi", 11, 11, 7, false),
    MUHURLU_BINA("muhurlu_bina", 9, 13, 9, false),
    CEPHANELIK("cephanelik", 13, 9, 5, true),
    EGITIM_SAHASI("egitim_sahasi", 21, 21, 3, false);

    public final String ad;
    public final int genislik;
    public final int derinlik;
    public final int yukseklik;
    /** Çevresine dağınık 2-6 asker konur mu? */
    public final boolean cevredeAsker;

    BinaTuru(String ad, int genislik, int derinlik, int yukseklik, boolean cevredeAsker) {
        this.ad = ad;
        this.genislik = genislik;
        this.derinlik = derinlik;
        this.yukseklik = yukseklik;
        this.cevredeAsker = cevredeAsker;
    }

    /** Bilinmeyen ad (ör. "rastgele") için null döner. */
    public static BinaTuru adIle(String ad) {
        for (BinaTuru tur : values()) {
            if (tur.ad.equals(ad)) {
                return tur;
            }
        }
        return null;
    }

    public static BinaTuru sirayla(int i) {
        BinaTuru[] hepsi = values();
        return hepsi[Math.floorMod(i, hepsi.length)];
    }
}
