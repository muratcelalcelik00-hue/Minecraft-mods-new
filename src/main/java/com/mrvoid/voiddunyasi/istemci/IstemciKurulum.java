package com.mrvoid.voiddunyasi.istemci;

import com.mrvoid.voiddunyasi.VoidDunyasi;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

@Mod.EventBusSubscriber(modid = VoidDunyasi.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class IstemciKurulum {
    private IstemciKurulum() {
    }

    @SubscribeEvent
    public static void rendererKaydet(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(VoidDunyasi.ASKER.get(), AskerRenderer::new);
    }
}
