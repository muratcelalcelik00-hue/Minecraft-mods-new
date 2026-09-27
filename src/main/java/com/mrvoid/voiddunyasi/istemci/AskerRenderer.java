package com.mrvoid.voiddunyasi.istemci;

import com.mrvoid.voiddunyasi.Asker;
import com.mrvoid.voiddunyasi.VoidDunyasi;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.resources.ResourceLocation;

public class AskerRenderer extends HumanoidMobRenderer<Asker, HumanoidModel<Asker>> {
    private static final ResourceLocation TEKSTUR =
            new ResourceLocation(VoidDunyasi.MODID, "textures/entity/asker.png");

    public AskerRenderer(EntityRendererProvider.Context context) {
        super(context, new HumanoidModel<>(context.bakeLayer(ModelLayers.PLAYER)), 0.5F);
    }

    @Override
    public ResourceLocation getTextureLocation(Asker asker) {
        return TEKSTUR;
    }

    @Override
    protected boolean shouldShowName(Asker asker) {
        return false;
    }
}
