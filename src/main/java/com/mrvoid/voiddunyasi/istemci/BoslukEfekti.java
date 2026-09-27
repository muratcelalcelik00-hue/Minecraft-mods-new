package com.mrvoid.voiddunyasi.istemci;

import net.minecraft.client.renderer.DimensionSpecialEffects;
import net.minecraft.world.phys.Vec3;

/** Boşluk: bulut yok, gökyüzü çizilmez, yıldız yok, sis her zaman zifiri siyah. */
public class BoslukEfekti extends DimensionSpecialEffects {

    public BoslukEfekti() {
        super(Float.NaN, false, SkyType.NONE, false, false);
    }

    @Override
    public Vec3 getBrightnessDependentFogColor(Vec3 renk, float parlaklik) {
        return Vec3.ZERO;
    }

    @Override
    public boolean isFoggyAt(int x, int y) {
        return false;
    }
}
