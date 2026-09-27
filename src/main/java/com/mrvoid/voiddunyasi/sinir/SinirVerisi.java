package com.mrvoid.voiddunyasi.sinir;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.saveddata.SavedData;

/**
 * Void dünyasının (0,0) merkezli dairesel sınırının yarıçapı.
 * Kalıcı değer overworld'ün SavedData'sında ("voiddunyasi_sinir") durur; worldgen thread'lerinin
 * okuyabilmesi için güncel değer ayrıca {@link #yaricap} alanında tutulur.
 */
public class SinirVerisi extends SavedData {
    public static final String AD = "voiddunyasi_sinir";
    public static final int VARSAYILAN = 5000;
    public static final int EN_BUYUK = 29_000_000;

    public static volatile int yaricap = VARSAYILAN;

    private int deger;

    public SinirVerisi() {
        this(VARSAYILAN);
    }

    private SinirVerisi(int deger) {
        this.deger = deger;
    }

    public static SinirVerisi yukle(CompoundTag tag) {
        return new SinirVerisi(tag.contains("Yaricap") ? tag.getInt("Yaricap") : VARSAYILAN);
    }

    @Override
    public CompoundTag save(CompoundTag tag) {
        tag.putInt("Yaricap", this.deger);
        return tag;
    }

    public int deger() {
        return this.deger;
    }

    public void ayarla(int yeni) {
        this.deger = Math.max(0, Math.min(EN_BUYUK, yeni));
        yaricap = this.deger;
        this.setDirty();
    }

    /** Veriyi okur (yoksa varsayılanla oluşturur) ve statik alanı günceller. */
    public static SinirVerisi al(ServerLevel overworld) {
        SinirVerisi veri = overworld.getDataStorage().computeIfAbsent(SinirVerisi::yukle, SinirVerisi::new, AD);
        yaricap = veri.deger;
        return veri;
    }

    public static SinirVerisi al(MinecraftServer server) {
        return al(server.overworld());
    }

    /** Sütun sınırın içinde mi? (x² + z² ≤ r²) */
    public static boolean icinde(long x, long z, long r) {
        return x * x + z * z <= r * r;
    }

    public static boolean icinde(int x, int z) {
        return icinde(x, z, yaricap);
    }

    /**
     * Nokta sınırın dışındaysa merkeze doğru çekip sınırın {@code pay} blok içine getirir.
     * İçerideyse olduğu gibi döner. Sonuç: {x, z}.
     */
    public static int[] iceriCek(int x, int z, int pay) {
        int r = yaricap;
        if (icinde(x, z, r)) {
            return new int[]{x, z};
        }
        double uzaklik = Math.sqrt((double) x * x + (double) z * z);
        double hedef = Math.max(0, r - pay);
        double oran = hedef / uzaklik;
        return new int[]{(int) Math.floor(x * oran), (int) Math.floor(z * oran)};
    }
}
