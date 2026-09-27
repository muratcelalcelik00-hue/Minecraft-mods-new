package com.mrvoid.voiddunyasi;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

import java.util.EnumSet;

/**
 * Sessiz, hasar almayan, itilmeyen asker.
 * HEYKEL: evinde hareketsiz durur. UYANIK: hedefine yürür ve saldırır. DONUS: evine yürür, varınca HEYKEL olur.
 */
public class Asker extends PathfinderMob {

    public enum Durum { HEYKEL, UYANIK, DONUS }

    /** Hedefsiz UYANIK asker bu kadar tick sonra geri döner (10 sn). */
    private static final int HEDEFSIZ_SINIR = 200;
    /** Eve yol bulamayan asker bu kadar tick sonra doğrudan evine yerleşir (60 sn). */
    private static final int DONUS_SINIR = 1200;
    /** Yol en fazla bu kadar tick'te bir yenilenir. */
    private static final int YOL_YENILEME = 10;

    private Durum durum = Durum.HEYKEL;
    private BlockPos ev;
    private float evYaw;
    private int hedefsizSure;
    private int donusSure;

    public Asker(EntityType<? extends Asker> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder ozellikler() {
        return Mob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 20.0D)
                .add(Attributes.MOVEMENT_SPEED, 0.32D)
                .add(Attributes.ATTACK_DAMAGE, 8.0D)
                .add(Attributes.FOLLOW_RANGE, 64.0D)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0D);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(1, new SaldiriHedefi(this));
        this.goalSelector.addGoal(2, new EveDonus(this));
    }

    // ---------------------------------------------------------------- durum

    public Durum durum() {
        return this.durum;
    }

    /** Askeri UYANIK yapar ve hedefini verir. */
    public void uyandir(LivingEntity hedef) {
        this.durum = Durum.UYANIK;
        this.hedefsizSure = 0;
        this.setTarget(hedef);
    }

    /** Hedefi bırakıp evine dönmeye başlar. */
    public void donuseGec() {
        this.durum = Durum.DONUS;
        this.donusSure = 0;
        this.setTarget(null);
        this.getNavigation().stop();
    }

    private void eveYerles() {
        this.getNavigation().stop();
        this.setTarget(null);
        if (this.ev != null) {
            this.moveTo(this.ev.getX() + 0.5D, this.ev.getY(), this.ev.getZ() + 0.5D, this.evYaw, 0.0F);
            this.setYHeadRot(this.evYaw);
            this.setYBodyRot(this.evYaw);
        }
        this.durum = Durum.HEYKEL;
    }

    @Override
    public void aiStep() {
        if (!this.level().isClientSide()) {
            this.durumGuncelle();
        }
        if (this.durum == Durum.HEYKEL) {
            this.xxa = 0.0F;
            this.yya = 0.0F;
            this.zza = 0.0F;
            this.setJumping(false);
        }
        super.aiStep();
    }

    private void durumGuncelle() {
        if (this.ev == null) {
            this.ev = this.blockPosition();
            this.evYaw = this.getYRot();
        }

        switch (this.durum) {
            case HEYKEL -> {
                this.getNavigation().stop();
                if (this.getTarget() != null) {
                    this.setTarget(null);
                }
                this.setYRot(this.evYaw);
                this.setYHeadRot(this.evYaw);
                this.setYBodyRot(this.evYaw);
            }
            case UYANIK -> {
                LivingEntity hedef = this.getTarget();
                if (hedef != null && (!hedef.isAlive() || hedef.level() != this.level() || !Dusman.mi(hedef))) {
                    this.setTarget(null);
                    hedef = null;
                }
                if (hedef != null) {
                    this.hedefsizSure = 0;
                } else if (++this.hedefsizSure >= HEDEFSIZ_SINIR) {
                    this.donuseGec();
                }
            }
            case DONUS -> {
                if (++this.donusSure >= DONUS_SINIR) {
                    this.eveYerles();
                }
            }
        }
    }

    // ---------------------------------------------------------------- kayıt

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putString("Durum", this.durum.name());
        if (this.ev != null) {
            tag.putInt("EvX", this.ev.getX());
            tag.putInt("EvY", this.ev.getY());
            tag.putInt("EvZ", this.ev.getZ());
            tag.putFloat("EvYaw", this.evYaw);
        }
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        try {
            this.durum = Durum.valueOf(tag.getString("Durum"));
        } catch (IllegalArgumentException e) {
            this.durum = Durum.HEYKEL;
        }
        if (tag.contains("EvX")) {
            this.ev = new BlockPos(tag.getInt("EvX"), tag.getInt("EvY"), tag.getInt("EvZ"));
            this.evYaw = tag.getFloat("EvYaw");
        }
    }

    // ---------------------------------------------------------------- değişmeyen davranışlar

    /** Yalnızca /kill (ve dünya dışı) gibi dokunulmazlığı delen hasarlar işler. */
    @Override
    public boolean hurt(DamageSource source, float amount) {
        if (source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            return super.hurt(source, amount);
        }
        return false;
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    protected void pushEntities() {
    }

    @Override
    protected void doPush(Entity entity) {
    }

    @Override
    public boolean isSilent() {
        return true;
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return null;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return null;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return null;
    }

    @Override
    protected InteractionResult mobInteract(Player player, InteractionHand hand) {
        return InteractionResult.PASS;
    }

    @Override
    public boolean canBeLeashed(Player player) {
        return false;
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    public boolean shouldShowName() {
        return false;
    }

    // ---------------------------------------------------------------- hedefler (goal)

    /** Yalnızca UYANIK'ta: hedefe yürü, menzildeyse vur. Yol en fazla 10 tick'te bir yenilenir. */
    private static final class SaldiriHedefi extends Goal {
        private final Asker asker;
        private int yolSayaci;
        private int saldiriBekleme;

        SaldiriHedefi(Asker asker) {
            this.asker = asker;
            this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK));
        }

        private boolean gecerli() {
            LivingEntity hedef = this.asker.getTarget();
            return this.asker.durum == Durum.UYANIK && hedef != null && hedef.isAlive();
        }

        @Override
        public boolean canUse() {
            return this.gecerli();
        }

        @Override
        public boolean canContinueToUse() {
            return this.gecerli();
        }

        @Override
        public void start() {
            this.yolSayaci = 0;
        }

        @Override
        public void stop() {
            this.asker.getNavigation().stop();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            LivingEntity hedef = this.asker.getTarget();
            if (hedef == null) {
                return;
            }
            this.asker.getLookControl().setLookAt(hedef, 30.0F, 30.0F);

            if (--this.yolSayaci <= 0) {
                this.yolSayaci = YOL_YENILEME;
                this.asker.getNavigation().moveTo(hedef, 1.0D);
            }

            if (this.saldiriBekleme > 0) {
                this.saldiriBekleme--;
            }
            double menzil = this.asker.getBbWidth() * 2.0F * this.asker.getBbWidth() * 2.0F + hedef.getBbWidth();
            if (this.saldiriBekleme <= 0
                    && this.asker.distanceToSqr(hedef) <= menzil
                    && this.asker.getSensing().hasLineOfSight(hedef)) {
                this.saldiriBekleme = 20;
                this.asker.swing(InteractionHand.MAIN_HAND);
                this.asker.doHurtTarget(hedef);
            }
        }
    }

    /** Yalnızca DONUS'ta: evine yürür; 1.5 blok yakına varınca tam yerine oturup HEYKEL olur. */
    private static final class EveDonus extends Goal {
        private final Asker asker;
        private int yolSayaci;

        EveDonus(Asker asker) {
            this.asker = asker;
            this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            return this.asker.durum == Durum.DONUS && this.asker.ev != null;
        }

        @Override
        public boolean canContinueToUse() {
            return this.canUse();
        }

        @Override
        public void start() {
            this.yolSayaci = 0;
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            BlockPos ev = this.asker.ev;
            double x = ev.getX() + 0.5D;
            double y = ev.getY();
            double z = ev.getZ() + 0.5D;
            if (this.asker.distanceToSqr(x, y, z) <= 1.5D * 1.5D) {
                this.asker.eveYerles();
                return;
            }
            if (--this.yolSayaci <= 0) {
                this.yolSayaci = YOL_YENILEME;
                this.asker.getNavigation().moveTo(x, y, z, 1.0D);
            }
        }
    }
}
