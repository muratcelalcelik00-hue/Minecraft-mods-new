package com.mrvoid.voiddunyasi.sinir;

import com.mrvoid.voiddunyasi.VoidDunyasi;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Abilities;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.portal.PortalInfo;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.common.util.ITeleporter;
import net.minecraftforge.event.entity.living.LivingAttackEvent;
import net.minecraftforge.event.entity.living.LivingEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;

import java.util.Set;
import java.util.function.Function;

/** Void dünyasının kenarından düşenleri boşluğa alır ve boşlukta askıda tutar. */
public class BoslukOlaylari {
    private static final double DUSUS_Y = -8.0D;
    private static final double VARIS_Y = 128.0D;
    private static final float NORMAL_UCUS_HIZI = 0.05F;

    @SubscribeEvent
    public void canliTick(LivingEvent.LivingTickEvent event) {
        LivingEntity canli = event.getEntity();
        Level level = canli.level();
        if (level.isClientSide()) {
            return;
        }
        if (level.dimension().equals(VoidDunyasi.VOID_BOYUTU)) {
            if (canli.getY() < DUSUS_Y) {
                bosluga(canli, (ServerLevel) level);
            }
        } else if (level.dimension().equals(VoidDunyasi.BOSLUK)) {
            if (canli instanceof ServerPlayer oyuncu) {
                oyuncuBoslukta(oyuncu);
            } else {
                canli.setNoGravity(true);
                canli.setDeltaMovement(Vec3.ZERO);
                if (canli instanceof Mob mob) {
                    mob.setNoAi(true);
                }
            }
        }
    }

    private static void bosluga(LivingEntity canli, ServerLevel kaynak) {
        ServerLevel bosluk = kaynak.getServer().getLevel(VoidDunyasi.BOSLUK);
        if (bosluk == null) {
            return;
        }
        double x = canli.getX();
        double z = canli.getZ();
        canli.resetFallDistance();

        if (canli instanceof ServerPlayer oyuncu) {
            oyuncu.teleportTo(bosluk, x, VARIS_Y, z, oyuncu.getYRot(), oyuncu.getXRot());
            oyuncu.resetFallDistance();
            return;
        }

        canli.changeDimension(bosluk, new ITeleporter() {
            @Override
            public PortalInfo getPortalInfo(Entity entity, ServerLevel hedef, Function<ServerLevel, PortalInfo> varsayilan) {
                return new PortalInfo(new Vec3(x, VARIS_Y, z), Vec3.ZERO, entity.getYRot(), entity.getXRot());
            }

            @Override
            public boolean playTeleportSound(ServerPlayer player, ServerLevel kaynakLevel, ServerLevel hedef) {
                return false;
            }
        });
    }

    private static void oyuncuBoslukta(ServerPlayer oyuncu) {
        if (oyuncu.isSpectator()) {
            return;
        }
        Abilities yetenek = oyuncu.getAbilities();
        boolean degisti = false;

        if (oyuncu.getInventory().hasAnyOf(Set.of(VoidDunyasi.ASA.get()))) {
            // Asa varsa: normal uçuş.
            if (!yetenek.mayfly || yetenek.getFlyingSpeed() != NORMAL_UCUS_HIZI) {
                yetenek.mayfly = true;
                yetenek.setFlyingSpeed(NORMAL_UCUS_HIZI);
                degisti = true;
            }
        } else {
            // Asa yoksa: olduğu yerde asılı, kıpırdayamaz.
            if (!yetenek.mayfly || !yetenek.flying || yetenek.getFlyingSpeed() != 0.0F) {
                yetenek.mayfly = true;
                yetenek.flying = true;
                yetenek.setFlyingSpeed(0.0F);
                oyuncu.setDeltaMovement(Vec3.ZERO);
                oyuncu.hurtMarked = true;
                degisti = true;
            }
        }

        if (degisti) {
            oyuncu.onUpdateAbilities();
        }
    }

    /** Boşlukta yalnızca /kill işler. */
    @SubscribeEvent
    public void saldiri(LivingAttackEvent event) {
        LivingEntity canli = event.getEntity();
        if (!canli.level().isClientSide()
                && canli.level().dimension().equals(VoidDunyasi.BOSLUK)
                && !event.getSource().is(DamageTypes.GENERIC_KILL)) {
            event.setCanceled(true);
        }
    }

    @SubscribeEvent
    public void boyutDegisti(PlayerEvent.PlayerChangedDimensionEvent event) {
        if (event.getFrom().equals(VoidDunyasi.BOSLUK) && !event.getTo().equals(VoidDunyasi.BOSLUK)
                && event.getEntity() instanceof ServerPlayer oyuncu) {
            yetenekleriGeriYukle(oyuncu);
        }
    }

    @SubscribeEvent
    public void yenidenDogdu(PlayerEvent.PlayerRespawnEvent event) {
        if (event.getEntity() instanceof ServerPlayer oyuncu
                && !oyuncu.level().dimension().equals(VoidDunyasi.BOSLUK)) {
            yetenekleriGeriYukle(oyuncu);
        }
    }

    private static void yetenekleriGeriYukle(ServerPlayer oyuncu) {
        Abilities yetenek = oyuncu.getAbilities();
        if (!oyuncu.isCreative() && !oyuncu.isSpectator()) {
            yetenek.mayfly = false;
            yetenek.flying = false;
        }
        // Boşlukta 0'a çekilmiş olabilir; Creative uçuşu da bozulmasın diye hız her durumda normale döner.
        yetenek.setFlyingSpeed(NORMAL_UCUS_HIZI);
        oyuncu.onUpdateAbilities();
    }
}
