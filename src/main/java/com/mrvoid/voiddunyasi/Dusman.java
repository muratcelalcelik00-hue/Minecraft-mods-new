package com.mrvoid.voiddunyasi;

import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;

import java.util.Set;

/** Askerlerin kimi düşman saydığını belirleyen tek yer. */
public final class Dusman {
    public static final String ETIKET = "voiddunyasi_dusman";

    private Dusman() {
    }

    /**
     * Düşman: Survival/Adventure'daki, envanterinde (offhand dahil) Asa olmayan oyuncu
     * ya da "voiddunyasi_dusman" etiketli canlı. Asa taşıyan, Creative/Spectator oyuncular,
     * köylüler ve askerler asla düşman değildir.
     */
    public static boolean mi(Entity entity) {
        if (!(entity instanceof LivingEntity canli) || !canli.isAlive()) {
            return false;
        }
        if (entity instanceof Asker || entity.getType() == EntityType.VILLAGER) {
            return false;
        }
        if (entity instanceof Player oyuncu) {
            return !oyuncu.isCreative()
                    && !oyuncu.isSpectator()
                    && !oyuncu.getInventory().hasAnyOf(Set.of(VoidDunyasi.ASA.get()));
        }
        return entity.getTags().contains(ETIKET);
    }
}
