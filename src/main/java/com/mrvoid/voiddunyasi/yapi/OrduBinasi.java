package com.mrvoid.voiddunyasi.yapi;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.mrvoid.voiddunyasi.VoidDunyasi;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureType;

import java.util.Optional;

/**
 * Tek yapı tipi; 7 bina türünden birini üretir. "bina" alanı verilmezse ("rastgele") tür rastgele seçilir,
 * verilirse (ör. "fabrika") hep o tür üretilir.
 */
public class OrduBinasi extends Structure {
    public static final String RASTGELE = "rastgele";

    public static final Codec<OrduBinasi> CODEC = RecordCodecBuilder.create(ornek -> ornek.group(
            settingsCodec(ornek),
            Codec.STRING.optionalFieldOf("bina", RASTGELE).forGetter(yapi -> yapi.bina)
    ).apply(ornek, OrduBinasi::new));

    private final String bina;

    public OrduBinasi(StructureSettings settings, String bina) {
        super(settings);
        this.bina = bina;
    }

    @Override
    protected Optional<GenerationStub> findGenerationPoint(GenerationContext context) {
        ChunkPos chunk = context.chunkPos();
        int x = chunk.getMiddleBlockX();
        int z = chunk.getMiddleBlockZ();
        // Zeminin hemen üstündeki ilk boş blok.
        int y = context.chunkGenerator().getBaseHeight(x, z, Heightmap.Types.WORLD_SURFACE_WG,
                context.heightAccessor(), context.randomState());
        BlockPos merkez = new BlockPos(x, y, z);

        BinaTuru sabit = BinaTuru.adIle(this.bina);
        BinaTuru tur = sabit != null ? sabit : BinaTuru.sirayla(context.random().nextInt(BinaTuru.values().length));
        long tohum = context.random().nextLong();

        return Optional.of(new GenerationStub(merkez,
                builder -> builder.addPiece(new OrduBinasiParca(tur, merkez, tohum))));
    }

    @Override
    public StructureType<?> type() {
        return VoidDunyasi.ORDU_BINASI.get();
    }
}
