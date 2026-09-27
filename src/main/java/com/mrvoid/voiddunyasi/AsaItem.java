package com.mrvoid.voiddunyasi;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;

public class AsaItem extends Item {
    private static final int BEKLEME_TICK = 60; // 3 saniye
    private static final int ARAMA_YARICAPI = 8;

    public AsaItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide() || !(player instanceof ServerPlayer oyuncu)) {
            return InteractionResultHolder.sidedSuccess(stack, level.isClientSide());
        }

        ServerLevel kaynak = oyuncu.serverLevel();
        ResourceKey<Level> hedefKey = kaynak.dimension().equals(VoidDunyasi.VOID_BOYUTU)
                ? Level.OVERWORLD
                : VoidDunyasi.VOID_BOYUTU;
        ServerLevel hedef = oyuncu.server.getLevel(hedefKey);
        if (hedef == null) {
            oyuncu.displayClientMessage(Component.translatable("item.voiddunyasi.asa.boyut_yok"), true);
            return InteractionResultHolder.fail(stack);
        }

        BlockPos varis = guvenliKonum(hedef, oyuncu.getBlockX(), oyuncu.getBlockZ());

        yarikPartikulu(kaynak, oyuncu.getX(), oyuncu.getY(), oyuncu.getZ());

        oyuncu.resetFallDistance();
        oyuncu.teleportTo(hedef, varis.getX() + 0.5D, varis.getY(), varis.getZ() + 0.5D,
                oyuncu.getYRot(), oyuncu.getXRot());
        oyuncu.resetFallDistance();

        yarikPartikulu(hedef, varis.getX() + 0.5D, varis.getY(), varis.getZ() + 0.5D);

        oyuncu.getCooldowns().addCooldown(this, BEKLEME_TICK);
        return InteractionResultHolder.success(stack);
    }

    /** Siyah-mor yarık: dar ve uzun bir portal + mürekkep bulutu. Ses yok. */
    private static void yarikPartikulu(ServerLevel level, double x, double y, double z) {
        level.sendParticles(ParticleTypes.PORTAL, x, y + 1.0D, z, 90, 0.15D, 0.9D, 0.15D, 0.6D);
        level.sendParticles(ParticleTypes.SQUID_INK, x, y + 1.0D, z, 35, 0.1D, 0.8D, 0.1D, 0.02D);
    }

    /** Aynı X/Z'de (gerekirse yakında) en üstteki güvenli bloğun üstünü bulur. */
    private static BlockPos guvenliKonum(ServerLevel level, int x, int z) {
        for (int r = 0; r <= ARAMA_YARICAPI; r++) {
            for (int dx = -r; dx <= r; dx++) {
                for (int dz = -r; dz <= r; dz++) {
                    if (Math.max(Math.abs(dx), Math.abs(dz)) != r) {
                        continue;
                    }
                    BlockPos aday = yuzey(level, x + dx, z + dz);
                    if (guvenliMi(level, aday)) {
                        return aday;
                    }
                }
            }
        }
        return yuzey(level, x, z);
    }

    private static BlockPos yuzey(ServerLevel level, int x, int z) {
        level.getChunk(x >> 4, z >> 4); // chunk'ı yükle / üret ki yükseklik haritası doğru olsun
        int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING, x, z);
        y = Math.max(level.getMinBuildHeight() + 1, Math.min(y, level.getMaxBuildHeight() - 2));
        return new BlockPos(x, y, z);
    }

    private static boolean guvenliMi(ServerLevel level, BlockPos pos) {
        BlockPos alt = pos.below();
        BlockState zemin = level.getBlockState(alt);
        if (!zemin.getFluidState().isEmpty()
                || !zemin.isFaceSturdy(level, alt, Direction.UP)
                || zemin.is(Blocks.MAGMA_BLOCK)
                || zemin.is(BlockTags.CAMPFIRES)) {
            return false;
        }
        return bosMu(level, pos) && bosMu(level, pos.above());
    }

    private static boolean bosMu(ServerLevel level, BlockPos pos) {
        BlockState durum = level.getBlockState(pos);
        return durum.getFluidState().isEmpty()
                && !durum.is(BlockTags.FIRE)
                && durum.getCollisionShape(level, pos).isEmpty();
    }
}
