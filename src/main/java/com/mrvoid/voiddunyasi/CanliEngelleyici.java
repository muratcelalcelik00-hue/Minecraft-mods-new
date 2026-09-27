package com.mrvoid.voiddunyasi;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraftforge.event.entity.EntityJoinLevelEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.registries.ForgeRegistries;

/**
 * Void boyutunda köylüler ve bu modun canlıları dışında hiçbir canlının dünyaya girmesine izin vermez.
 * Oyuncular, eşyalar, mermiler vb. {@link Mob} olmadığından etkilenmez.
 */
public class CanliEngelleyici {

    @SubscribeEvent(priority = EventPriority.HIGH)
    public void canliKatiliyor(EntityJoinLevelEvent event) {
        if (event.getLevel().isClientSide() || !event.getLevel().dimension().equals(VoidDunyasi.VOID_BOYUTU)) {
            return;
        }

        Entity entity = event.getEntity();
        if (!(entity instanceof Mob) || entity.getType() == EntityType.VILLAGER) {
            return;
        }

        // Tuzak testi için bilerek düşman yapılmış canlılar (etiketler NBT'den bu olaydan önce yüklenir).
        if (entity.getTags().contains(Dusman.ETIKET)) {
            return;
        }

        ResourceLocation id = ForgeRegistries.ENTITY_TYPES.getKey(entity.getType());
        if (id != null && VoidDunyasi.MODID.equals(id.getNamespace())) {
            return;
        }

        event.setCanceled(true);
    }
}
