package com.mrvoid.voiddunyasi;

import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.server.ServerLifecycleHooks;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Tuzağın merkezi denetimi. Her 20 tick'te bir, yalnızca void_dunyasi'nda çalışır;
 * askerler kendi başlarına tarama yapmaz.
 */
public class TuzakSistemi {
    private static final int ARALIK = 20;
    private static final double HEYKEL_MESAFE = 6.0D;
    private static final double UYANDIRMA_MESAFE = 24.0D;
    private static final double KOY_MESAFE = 16.0D;
    private static final int OYALAMA_SINIR = 100; // 5 sn
    private static final double ALARM_MESAFE = 192.0D;
    private static final int ALARM_ASKER = 80;

    private int sayac;
    /** Düşman UUID → köylülerin yakınında geçirdiği toplam tick. */
    private Map<UUID, Integer> oyalama = new HashMap<>();

    @SubscribeEvent
    public void sunucuTick(TickEvent.ServerTickEvent event) {
        if (event.phase != TickEvent.Phase.END || ++this.sayac < ARALIK) {
            return;
        }
        this.sayac = 0;

        MinecraftServer server = ServerLifecycleHooks.getCurrentServer();
        ServerLevel level = server == null ? null : server.getLevel(VoidDunyasi.VOID_BOYUTU);
        if (level == null) {
            return;
        }

        List<LivingEntity> dusmanlar = new ArrayList<>();
        for (Entity entity : level.getAllEntities()) {
            if (Dusman.mi(entity)) {
                dusmanlar.add((LivingEntity) entity);
            }
        }

        Map<UUID, Integer> yeniOyalama = new HashMap<>();
        for (LivingEntity dusman : dusmanlar) {
            this.denetle(level, dusman, yeniOyalama);
        }
        this.oyalama = yeniOyalama;
    }

    private void denetle(ServerLevel level, LivingEntity dusman, Map<UUID, Integer> yeniOyalama) {
        // Heykel tuzağı
        double uyandirmaKare = UYANDIRMA_MESAFE * UYANDIRMA_MESAFE;
        List<Asker> yakindakiler = level.getEntitiesOfClass(Asker.class,
                dusman.getBoundingBox().inflate(UYANDIRMA_MESAFE),
                asker -> asker.isAlive() && asker.distanceToSqr(dusman) <= uyandirmaKare);

        boolean tuzak = false;
        for (Asker asker : yakindakiler) {
            if (asker.durum() == Asker.Durum.HEYKEL
                    && asker.distanceToSqr(dusman) <= HEYKEL_MESAFE * HEYKEL_MESAFE) {
                tuzak = true;
                break;
            }
        }

        if (tuzak) {
            for (Asker asker : yakindakiler) {
                asker.uyandir(dusman);
            }
            alarm(level, dusman);
        } else {
            // Hedefini kaybetmiş uyanık askerler yakındaki düşmana yönelir.
            for (Asker asker : yakindakiler) {
                if (asker.durum() == Asker.Durum.UYANIK && asker.getTarget() == null) {
                    asker.uyandir(dusman);
                }
            }
        }

        // Oyalama: köylülerin yakınında toplam 5 sn.
        double koyKare = KOY_MESAFE * KOY_MESAFE;
        boolean koyluYakin = !level.getEntitiesOfClass(Villager.class,
                dusman.getBoundingBox().inflate(KOY_MESAFE),
                koylu -> koylu.distanceToSqr(dusman) <= koyKare).isEmpty();
        int sure = this.oyalama.getOrDefault(dusman.getUUID(), 0);
        if (koyluYakin) {
            sure += ARALIK;
            if (sure >= OYALAMA_SINIR) {
                alarm(level, dusman);
                sure = 0;
            }
        }
        yeniOyalama.put(dusman.getUUID(), sure);
    }

    /** Sessiz alarm: hedefin 192 blok çevresindeki en yakın 80 asker uyanır ve hedefe yürür. */
    public static int alarm(ServerLevel level, LivingEntity hedef) {
        double kare = ALARM_MESAFE * ALARM_MESAFE;
        List<Asker> askerler = level.getEntitiesOfClass(Asker.class,
                hedef.getBoundingBox().inflate(ALARM_MESAFE),
                asker -> asker.isAlive() && asker.distanceToSqr(hedef) <= kare);
        askerler.sort(Comparator.comparingDouble(asker -> asker.distanceToSqr(hedef)));
        int sayi = Math.min(ALARM_ASKER, askerler.size());
        for (int i = 0; i < sayi; i++) {
            askerler.get(i).uyandir(hedef);
        }
        return sayi;
    }

    // ---------------------------------------------------------------- debug komutları

    @SubscribeEvent
    public void komutlariKaydet(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("voidalarm")
                .requires(kaynak -> kaynak.hasPermission(2))
                .executes(ctx -> alarmKomutu(ctx.getSource())));

        event.getDispatcher().register(Commands.literal("voidsakin")
                .requires(kaynak -> kaynak.hasPermission(2))
                .executes(ctx -> sakinKomutu(ctx.getSource())));
    }

    private static int alarmKomutu(CommandSourceStack kaynak) {
        ServerLevel level = kaynak.getLevel();
        Vec3 konum = kaynak.getPosition();
        Player oyuncu = level.getNearestPlayer(konum.x, konum.y, konum.z, -1.0D, false);
        if (oyuncu == null) {
            kaynak.sendFailure(Component.translatable("komut.voiddunyasi.alarm_oyuncu_yok"));
            return 0;
        }
        int sayi = alarm(level, oyuncu);
        kaynak.sendSuccess(() -> Component.translatable("komut.voiddunyasi.alarm", sayi, oyuncu.getDisplayName()), true);
        return sayi;
    }

    private static int sakinKomutu(CommandSourceStack kaynak) {
        int sayi = 0;
        for (ServerLevel level : kaynak.getServer().getAllLevels()) {
            for (Asker asker : level.getEntities(VoidDunyasi.ASKER.get(),
                    a -> a.durum() == Asker.Durum.UYANIK)) {
                asker.donuseGec();
                sayi++;
            }
        }
        int toplam = sayi;
        kaynak.sendSuccess(() -> Component.translatable("komut.voiddunyasi.sakin", toplam), true);
        return toplam;
    }
}
