package com.mrvoid.voiddunyasi.yapi;

import com.mrvoid.voiddunyasi.Asker;
import com.mrvoid.voiddunyasi.VoidDunyasi;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.BarrelBlock;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.SpawnerBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.SlabType;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceSerializationContext;

import java.util.ArrayList;
import java.util.List;

/**
 * Bir ordu binasını NBT şablonu kullanmadan, blok blok kuran parça.
 * <p>
 * postProcess her chunk için ayrı çağrılır; bu yüzden tüm rastgele kararlar kayıtlı {@link #tohum}'dan
 * yeniden üretilir ve yalnızca o chunk'ın kutusuna düşen bloklar/askerler yerleştirilir.
 * Hiçbir yapıda ışık kaynağı yoktur.
 */
public class OrduBinasiParca extends StructurePiece {
    private static final int KENAR = 6;
    private static final BlockState HAVA = Blocks.AIR.defaultBlockState();

    private final BinaTuru tur;
    private final long tohum;
    private final int cx;
    private final int cy; // zeminin üstündeki ilk boş blok
    private final int cz;
    private final int yukseklik;

    public OrduBinasiParca(BinaTuru tur, BlockPos merkez, long tohum) {
        super(VoidDunyasi.ORDU_BINASI_PARCA.get(), 0, kutuHesapla(tur, merkez, yukseklikHesapla(tur, tohum)));
        this.tur = tur;
        this.tohum = tohum;
        this.cx = merkez.getX();
        this.cy = merkez.getY();
        this.cz = merkez.getZ();
        this.yukseklik = yukseklikHesapla(tur, tohum);
    }

    public OrduBinasiParca(CompoundTag tag) {
        super(VoidDunyasi.ORDU_BINASI_PARCA.get(), tag);
        BinaTuru okunan = BinaTuru.adIle(tag.getString("Tur"));
        this.tur = okunan != null ? okunan : BinaTuru.KAPISIZ_YAPI;
        this.tohum = tag.getLong("Tohum");
        this.cx = tag.getInt("CX");
        this.cy = tag.getInt("CY");
        this.cz = tag.getInt("CZ");
        this.yukseklik = tag.getInt("Yukseklik");
    }

    @Override
    protected void addAdditionalSaveData(StructurePieceSerializationContext context, CompoundTag tag) {
        tag.putString("Tur", this.tur.ad);
        tag.putLong("Tohum", this.tohum);
        tag.putInt("CX", this.cx);
        tag.putInt("CY", this.cy);
        tag.putInt("CZ", this.cz);
        tag.putInt("Yukseklik", this.yukseklik);
    }

    private static int yukseklikHesapla(BinaTuru tur, long tohum) {
        if (tur == BinaTuru.PENCERESIZ_KULE) {
            return 30 + RandomSource.create(tohum).nextInt(11); // 30-40
        }
        return tur.yukseklik;
    }

    private static BoundingBox kutuHesapla(BinaTuru tur, BlockPos merkez, int yukseklik) {
        int x0 = merkez.getX() - tur.genislik / 2;
        int z0 = merkez.getZ() - tur.derinlik / 2;
        int kenar = tur.cevredeAsker ? KENAR : 0;
        return new BoundingBox(
                x0 - kenar, merkez.getY() - 1, z0 - kenar,
                x0 + tur.genislik - 1 + kenar, merkez.getY() + yukseklik - 1, z0 + tur.derinlik - 1 + kenar);
    }

    @Override
    public void postProcess(WorldGenLevel level, StructureManager structureManager, ChunkGenerator generator,
                            RandomSource random, BoundingBox kutu, ChunkPos chunkPos, BlockPos pivot) {
        int x0 = this.cx - this.tur.genislik / 2;
        int z0 = this.cz - this.tur.derinlik / 2;
        int x1 = x0 + this.tur.genislik - 1;
        int z1 = z0 + this.tur.derinlik - 1;
        int y = this.cy;

        switch (this.tur) {
            case SPAWNER_BINASI -> spawnerBinasi(level, kutu, x0, z0, x1, z1, y);
            case FABRIKA -> fabrika(level, kutu, x0, z0, x1, z1, y);
            case PENCERESIZ_KULE -> kabuk(level, kutu, x0, y - 1, z0, x1, y + this.yukseklik - 1, z1, muhur());
            case KAPISIZ_YAPI -> kabuk(level, kutu, x0, y - 1, z0, x1, y + 6, z1, muhur());
            case MUHURLU_BINA -> muhurluBina(level, kutu, x0, z0, x1, z1, y);
            case CEPHANELIK -> cephanelik(level, kutu, x0, z0, x1, z1, y);
            case EGITIM_SAHASI -> doldur(level, kutu, x0, y - 1, z0, x1, y - 1, z1,
                    Blocks.POLISHED_ANDESITE.defaultBlockState());
        }

        askerleriYerlestir(level, kutu, x0, z0, x1, z1, y);
    }

    // ---------------------------------------------------------------- binalar

    private void spawnerBinasi(WorldGenLevel level, BoundingBox kutu, int x0, int z0, int x1, int z1, int y) {
        kabuk(level, kutu, x0, y - 1, z0, x1, y + 5, z1, Blocks.DEEPSLATE_BRICKS.defaultBlockState());

        // Güney duvarında kemerli açıklık.
        doldur(level, kutu, this.cx - 1, y, z1, this.cx + 1, y + 2, z1, HAVA);
        BlockState ustYarim = Blocks.DEEPSLATE_BRICK_SLAB.defaultBlockState().setValue(SlabBlock.TYPE, SlabType.TOP);
        koy(level, kutu, this.cx - 1, y + 2, z1, ustYarim);
        koy(level, kutu, this.cx + 1, y + 2, z1, ustYarim);

        BlockPos spawnerKonum = new BlockPos(this.cx, y, this.cz);
        if (kutu.isInside(spawnerKonum)) {
            level.setBlock(spawnerKonum, Blocks.SPAWNER.defaultBlockState(), 2);
            BlockEntity be = level.getBlockEntity(spawnerKonum);
            if (be instanceof SpawnerBlockEntity spawner) {
                spawner.load(spawnerVerisi());
            }
        }
    }

    private static CompoundTag spawnerVerisi() {
        CompoundTag canli = new CompoundTag();
        canli.putString("id", VoidDunyasi.MODID + ":asker");
        canli.putBoolean("PersistenceRequired", true);

        CompoundTag spawnData = new CompoundTag();
        spawnData.put("entity", canli);

        CompoundTag olasilik = new CompoundTag();
        olasilik.putInt("weight", 1);
        olasilik.put("data", spawnData.copy());
        ListTag olasiliklar = new ListTag();
        olasiliklar.add(olasilik);

        CompoundTag tag = new CompoundTag();
        tag.put("SpawnData", spawnData);
        tag.put("SpawnPotentials", olasiliklar);
        tag.putShort("Delay", (short) 20);
        tag.putShort("MinSpawnDelay", (short) 200);
        tag.putShort("MaxSpawnDelay", (short) 800);
        tag.putShort("SpawnCount", (short) 1);
        tag.putShort("MaxNearbyEntities", (short) 3);
        tag.putShort("RequiredPlayerRange", (short) 32);
        tag.putShort("SpawnRange", (short) 3);
        return tag;
    }

    private void fabrika(WorldGenLevel level, BoundingBox kutu, int x0, int z0, int x1, int z1, int y) {
        BlockState demir = Blocks.IRON_BLOCK.defaultBlockState();
        BlockState siyahTas = Blocks.POLISHED_BLACKSTONE.defaultBlockState();

        kabuk(level, kutu, x0, y - 1, z0, x1, y + 7, z1, demir);
        doldur(level, kutu, x0, y - 1, z0, x1, y - 1, z1, siyahTas); // zemin
        doldur(level, kutu, x0, y + 7, z0, x1, y + 7, z1, siyahTas); // çatı
        for (int[] kose : new int[][]{{x0, z0}, {x1, z0}, {x0, z1}, {x1, z1}}) {
            doldur(level, kutu, kose[0], y, kose[1], kose[0], y + 6, kose[1], siyahTas);
        }

        // Güneyde büyük giriş.
        doldur(level, kutu, this.cx - 1, y, z1, this.cx + 1, y + 3, z1, HAVA);

        // İki baca, yerden 18 bloğa kadar; ortaları hole açık.
        for (int bx : new int[]{this.cx - 4, this.cx + 4}) {
            doldur(level, kutu, bx - 1, y + 7, this.cz - 1, bx + 1, y + 17, this.cz + 1, siyahTas);
            doldur(level, kutu, bx, y + 7, this.cz, bx, y + 17, this.cz, HAVA);
        }
    }

    private void muhurluBina(WorldGenLevel level, BoundingBox kutu, int x0, int z0, int x1, int z1, int y) {
        doldur(level, kutu, x0, y - 1, z0, x1, y + 8, z1, Blocks.SMOOTH_BASALT.defaultBlockState());
        doldur(level, kutu, x0 + 1, y - 1, z0 + 1, x1 - 1, y + 7, z1 - 1, muhur());
        doldur(level, kutu, x0 + 2, y, z0 + 2, x1 - 2, y + 6, z1 - 2, HAVA);
    }

    private void cephanelik(WorldGenLevel level, BoundingBox kutu, int x0, int z0, int x1, int z1, int y) {
        kabuk(level, kutu, x0, y - 1, z0, x1, y + 4, z1, Blocks.STONE_BRICKS.defaultBlockState());
        doldur(level, kutu, this.cx - 1, y, z1, this.cx + 1, y + 2, z1, HAVA); // giriş

        // Duvar diplerinde boş raflar: fıçı ve sandık dönüşümlü (iki sandık asla yan yana gelmez).
        for (int x = x0 + 1; x <= x1 - 1; x++) {
            raf(level, kutu, x, y, z0 + 1, Direction.SOUTH);
        }
        for (int z = z0 + 2; z <= z1 - 2; z++) {
            raf(level, kutu, x0 + 1, y, z, Direction.EAST);
            raf(level, kutu, x1 - 1, y, z, Direction.WEST);
        }
    }

    private static void raf(WorldGenLevel level, BoundingBox kutu, int x, int y, int z, Direction yon) {
        BlockState durum = ((x + z) & 1) == 0
                ? Blocks.BARREL.defaultBlockState().setValue(BarrelBlock.FACING, Direction.UP)
                : Blocks.CHEST.defaultBlockState().setValue(ChestBlock.FACING, yon);
        koy(level, kutu, x, y, z, durum);
    }

    // ---------------------------------------------------------------- askerler

    private void askerleriYerlestir(WorldGenLevel level, BoundingBox kutu, int x0, int z0, int x1, int z1, int y) {
        RandomSource r = RandomSource.create(this.tohum ^ 0x5DEECE66DL);
        List<int[]> konumlar = new ArrayList<>(); // {x, z, yaw}

        if (this.tur == BinaTuru.EGITIM_SAHASI) {
            int sayi = 8 + r.nextInt(5); // 8-12
            int sira = (sayi + 3) / 4;
            int yaw = r.nextBoolean() ? 0 : 180;
            for (int i = 0; i < sayi; i++) {
                int sutun = i % 4;
                int satir = i / 4;
                konumlar.add(new int[]{this.cx - 6 + sutun * 4, this.cz - (sira - 1) * 2 + satir * 4, yaw});
            }
        } else if (this.tur.cevredeAsker) {
            int sayi = 2 + r.nextInt(5); // 2-6
            for (int deneme = 0; deneme < 60 && konumlar.size() < sayi; deneme++) {
                int x = x0 - 5 + r.nextInt(x1 - x0 + 11);
                int z = z0 - 5 + r.nextInt(z1 - z0 + 11);
                int yaw = r.nextInt(360);
                boolean binaya = x >= x0 - 1 && x <= x1 + 1 && z >= z0 - 1 && z <= z1 + 1;
                if (binaya || cokYakin(konumlar, x, z)) {
                    continue;
                }
                konumlar.add(new int[]{x, z, yaw});
            }
        }

        for (int[] k : konumlar) {
            BlockPos konum = new BlockPos(k[0], y, k[1]);
            if (!kutu.isInside(konum)) {
                continue; // bu asker başka bir chunk'ın işi
            }
            Asker asker = VoidDunyasi.ASKER.get().create(level.getLevel());
            if (asker == null) {
                continue;
            }
            float yaw = k[2];
            asker.moveTo(k[0] + 0.5D, y, k[1] + 0.5D, yaw, 0.0F);
            asker.setYHeadRot(yaw);
            asker.setYBodyRot(yaw);
            asker.setPersistenceRequired();
            level.addFreshEntityWithPassengers(asker);
        }
    }

    private static boolean cokYakin(List<int[]> konumlar, int x, int z) {
        for (int[] k : konumlar) {
            if (Math.abs(k[0] - x) < 2 && Math.abs(k[1] - z) < 2) {
                return true;
            }
        }
        return false;
    }

    // ---------------------------------------------------------------- yardımcılar

    private static BlockState muhur() {
        return VoidDunyasi.MUHUR.get().defaultBlockState();
    }

    private static void koy(WorldGenLevel level, BoundingBox kutu, int x, int y, int z, BlockState durum) {
        BlockPos konum = new BlockPos(x, y, z);
        if (kutu.isInside(konum)) {
            level.setBlock(konum, durum, 2);
        }
    }

    /** Dolu kutu; yalnızca chunk kutusuyla kesişen kısmı yerleştirir. */
    private static void doldur(WorldGenLevel level, BoundingBox kutu, int x0, int y0, int z0,
                               int x1, int y1, int z1, BlockState durum) {
        int ax = Math.max(x0, kutu.minX());
        int bx = Math.min(x1, kutu.maxX());
        int ay = Math.max(y0, kutu.minY());
        int by = Math.min(y1, kutu.maxY());
        int az = Math.max(z0, kutu.minZ());
        int bz = Math.min(z1, kutu.maxZ());
        BlockPos.MutableBlockPos konum = new BlockPos.MutableBlockPos();
        for (int x = ax; x <= bx; x++) {
            for (int z = az; z <= bz; z++) {
                for (int y = ay; y <= by; y++) {
                    level.setBlock(konum.set(x, y, z), durum, 2);
                }
            }
        }
    }

    /** İçi hava dolu, hiçbir açıklığı olmayan kapalı kutu. */
    private static void kabuk(WorldGenLevel level, BoundingBox kutu, int x0, int y0, int z0,
                              int x1, int y1, int z1, BlockState durum) {
        doldur(level, kutu, x0, y0, z0, x1, y1, z1, durum);
        doldur(level, kutu, x0 + 1, y0 + 1, z0 + 1, x1 - 1, y1 - 1, z1 - 1, HAVA);
    }
}
