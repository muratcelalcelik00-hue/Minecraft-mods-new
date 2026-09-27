package com.mrvoid.voiddunyasi.sinir;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mrvoid.voiddunyasi.VoidDunyasi;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.levelgen.FlatLevelSource;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.event.level.ChunkEvent;
import net.minecraftforge.event.level.LevelEvent;
import net.minecraftforge.event.server.ServerStoppedEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;

import java.util.List;

/** Sınır yarıçapının yüklenmesi, komutlar ve genişleyen sınırın içine giren boş chunk'ların doldurulması. */
public class SinirOlaylari {

    /** Overworld yüklenir yüklenmez (hiçbir chunk üretilmeden önce) yarıçapı statik alana al. */
    @SubscribeEvent
    public void dunyaYuklendi(LevelEvent.Load event) {
        if (event.getLevel() instanceof ServerLevel level && level.dimension().equals(Level.OVERWORLD)) {
            SinirVerisi.al(level);
        }
    }

    @SubscribeEvent
    public void sunucuDurdu(ServerStoppedEvent event) {
        SinirVerisi.yaricap = SinirVerisi.VARSAYILAN;
    }

    @SubscribeEvent
    public void komutlariKaydet(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("voidgenislet")
                .requires(kaynak -> kaynak.hasPermission(2))
                .then(Commands.argument("miktar", IntegerArgumentType.integer(1))
                        .executes(ctx -> genislet(ctx.getSource(), IntegerArgumentType.getInteger(ctx, "miktar")))));

        event.getDispatcher().register(Commands.literal("voidsinir")
                .executes(ctx -> {
                    int r = SinirVerisi.al(ctx.getSource().getServer()).deger();
                    ctx.getSource().sendSuccess(() -> Component.translatable("komut.voiddunyasi.sinir", r), false);
                    return r;
                }));
    }

    private static int genislet(CommandSourceStack kaynak, int miktar) {
        SinirVerisi veri = SinirVerisi.al(kaynak.getServer());
        veri.ayarla((int) Math.min((long) veri.deger() + miktar, SinirVerisi.EN_BUYUK));
        int yeni = veri.deger();
        kaynak.sendSuccess(() -> Component.translatable("komut.voiddunyasi.genislet", yeni), true);
        return yeni;
    }

    /**
     * Eskiden sınır dışında kaldığı için boş üretilmiş sütunlar artık sınırın içindeyse
     * flat katmanlarla doldurulur. Bu chunk'lara yapı eklenmez.
     */
    @SubscribeEvent
    public void chunkYuklendi(ChunkEvent.Load event) {
        if (!(event.getLevel() instanceof ServerLevel level)
                || !level.dimension().equals(VoidDunyasi.VOID_BOYUTU)
                || !(event.getChunk() instanceof LevelChunk chunk)) {
            return;
        }

        long r = SinirVerisi.yaricap;
        int minX = chunk.getPos().getMinBlockX();
        int minZ = chunk.getPos().getMinBlockZ();
        int minY = level.getMinBuildHeight();
        List<BlockState> katmanlar = null;
        boolean degisti = false;
        BlockPos.MutableBlockPos konum = new BlockPos.MutableBlockPos();

        for (int x = 0; x < 16; x++) {
            for (int z = 0; z < 16; z++) {
                int dx = minX + x;
                int dz = minZ + z;
                if (!SinirVerisi.icinde(dx, dz, r) || !chunk.getBlockState(konum.set(dx, minY, dz)).isAir()) {
                    continue;
                }
                if (katmanlar == null) {
                    katmanlar = katmanlariAl(level);
                }
                for (int i = 0; i < katmanlar.size(); i++) {
                    chunk.setBlockState(konum.set(dx, minY + i, dz), katmanlar.get(i), false);
                }
                degisti = true;
            }
        }

        if (degisti) {
            chunk.setUnsaved(true);
        }
    }

    private static List<BlockState> katmanlariAl(ServerLevel level) {
        if (level.getChunkSource().getGenerator() instanceof FlatLevelSource flat) {
            List<BlockState> katmanlar = flat.settings().getLayers();
            if (!katmanlar.isEmpty()) {
                return katmanlar;
            }
        }
        BlockState madde = VoidDunyasi.BILINMEYEN_MADDE.get().defaultBlockState();
        BlockState[] varsayilan = new BlockState[61];
        varsayilan[0] = Blocks.BEDROCK.defaultBlockState();
        for (int i = 1; i < varsayilan.length; i++) {
            varsayilan[i] = madde;
        }
        return List.of(varsayilan);
    }
}
