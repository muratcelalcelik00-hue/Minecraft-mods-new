package com.mrvoid.voiddunyasi.sinir;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.RegistryAccess;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.LevelHeightAccessor;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.chunk.ChunkGeneratorStructureState;
import net.minecraft.world.level.levelgen.FlatLevelSource;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.levelgen.blending.Blender;
import net.minecraft.world.level.levelgen.flat.FlatLevelGeneratorSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplateManager;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;

/**
 * Düz dünya; ancak (0,0) etrafındaki dairesel sınırın dışındaki sütunlar tamamen hava kalır.
 * Kenar düz bir uçurumdur, hiçbir işaret yoktur.
 */
public class SinirliDuz extends FlatLevelSource {
    public static final Codec<SinirliDuz> CODEC = RecordCodecBuilder.create(ornek -> ornek.group(
            FlatLevelGeneratorSettings.CODEC.fieldOf("settings").forGetter(SinirliDuz::settings)
    ).apply(ornek, ornek.stable(SinirliDuz::new)));

    /** Yapı başlangıçları sınıra bundan daha yakın olamaz. */
    private static final int YAPI_PAYI = 48;

    public SinirliDuz(FlatLevelGeneratorSettings settings) {
        super(settings);
    }

    @Override
    protected Codec<? extends ChunkGenerator> codec() {
        return CODEC;
    }

    @Override
    public CompletableFuture<ChunkAccess> fillFromNoise(Executor executor, Blender blender, RandomState randomState,
                                                        StructureManager structureManager, ChunkAccess chunk) {
        List<BlockState> katmanlar = this.settings().getLayers();
        long r = SinirVerisi.yaricap;
        int minX = chunk.getPos().getMinBlockX();
        int minZ = chunk.getPos().getMinBlockZ();
        int katmanSayisi = Math.min(chunk.getHeight(), katmanlar.size());

        BlockPos.MutableBlockPos konum = new BlockPos.MutableBlockPos();
        Heightmap okyanusTabani = chunk.getOrCreateHeightmapUnprimed(Heightmap.Types.OCEAN_FLOOR_WG);
        Heightmap yuzey = chunk.getOrCreateHeightmapUnprimed(Heightmap.Types.WORLD_SURFACE_WG);

        for (int x = 0; x < 16; x++) {
            for (int z = 0; z < 16; z++) {
                if (!SinirVerisi.icinde(minX + x, minZ + z, r)) {
                    continue; // sınırın dışı: tamamen hava
                }
                for (int i = 0; i < katmanSayisi; i++) {
                    BlockState durum = katmanlar.get(i);
                    if (durum == null) {
                        continue;
                    }
                    int y = chunk.getMinBuildHeight() + i;
                    chunk.setBlockState(konum.set(x, y, z), durum, false);
                    okyanusTabani.update(x, y, z, durum);
                    yuzey.update(x, y, z, durum);
                }
            }
        }
        return CompletableFuture.completedFuture(chunk);
    }

    @Override
    public void createStructures(RegistryAccess registryAccess, ChunkGeneratorStructureState structureState,
                                 StructureManager structureManager, ChunkAccess chunk,
                                 StructureTemplateManager templateManager) {
        ChunkPos pos = chunk.getPos();
        long sinir = Math.max(0, SinirVerisi.yaricap - YAPI_PAYI);
        if (!SinirVerisi.icinde(pos.getMiddleBlockX(), pos.getMiddleBlockZ(), sinir)) {
            return; // kenara yakın ya da dışarıda: yapı yok
        }
        super.createStructures(registryAccess, structureState, structureManager, chunk, templateManager);
    }

    @Override
    public int getBaseHeight(int x, int z, Heightmap.Types type, LevelHeightAccessor level, RandomState randomState) {
        if (!SinirVerisi.icinde(x, z)) {
            return level.getMinBuildHeight();
        }
        return super.getBaseHeight(x, z, type, level, randomState);
    }
}
