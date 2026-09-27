package com.mrvoid.voiddunyasi;

import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.properties.NoteBlockInstrument;
import net.minecraft.world.level.material.MapColor;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

@Mod(VoidDunyasi.MODID)
public class VoidDunyasi {
    public static final String MODID = "voiddunyasi";

    public static final ResourceKey<Level> VOID_BOYUTU =
            ResourceKey.create(Registries.DIMENSION, new ResourceLocation(MODID, "void_dunyasi"));

    public static final DeferredRegister<Block> BLOCKS = DeferredRegister.create(ForgeRegistries.BLOCKS, MODID);
    public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(ForgeRegistries.ITEMS, MODID);
    public static final DeferredRegister<SoundEvent> SOUNDS = DeferredRegister.create(ForgeRegistries.SOUND_EVENTS, MODID);
    public static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, MODID);

    public static final RegistryObject<Block> BILINMEYEN_MADDE = BLOCKS.register("bilinmeyen_madde",
            () -> new Block(BlockBehaviour.Properties.of()
                    .mapColor(MapColor.COLOR_PURPLE)
                    .instrument(NoteBlockInstrument.BASEDRUM)
                    .requiresCorrectToolForDrops()
                    .strength(1.5F, 6.0F)
                    .sound(SoundType.STONE)));

    public static final RegistryObject<Item> BILINMEYEN_MADDE_ITEM = ITEMS.register("bilinmeyen_madde",
            () -> new BlockItem(BILINMEYEN_MADDE.get(), new Item.Properties()));

    public static final RegistryObject<Item> ASA = ITEMS.register("asa",
            () -> new AsaItem(new Item.Properties().stacksTo(1)));

    // Biyom müziğini susturmak için içi boş ses olayı (sounds.json'da ses dosyası yok).
    public static final RegistryObject<SoundEvent> SESSIZLIK = SOUNDS.register("sessizlik",
            () -> SoundEvent.createVariableRangeEvent(new ResourceLocation(MODID, "sessizlik")));

    public static final RegistryObject<CreativeModeTab> SEKME = TABS.register("sekme",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.voiddunyasi"))
                    .icon(() -> new ItemStack(ASA.get()))
                    .displayItems((parametreler, cikti) -> {
                        cikti.accept(ASA.get());
                        cikti.accept(BILINMEYEN_MADDE_ITEM.get());
                    })
                    .build());

    public VoidDunyasi() {
        IEventBus modBus = FMLJavaModLoadingContext.get().getModEventBus();
        BLOCKS.register(modBus);
        ITEMS.register(modBus);
        SOUNDS.register(modBus);
        TABS.register(modBus);

        MinecraftForge.EVENT_BUS.register(new CanliEngelleyici());
    }
}
