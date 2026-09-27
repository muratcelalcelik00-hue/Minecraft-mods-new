package com.mrvoid.voiddunyasi;

import com.mrvoid.voiddunyasi.yapi.OrduBinasi;
import com.mrvoid.voiddunyasi.yapi.OrduBinasiParca;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.properties.NoteBlockInstrument;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceType;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;
import net.minecraftforge.common.ForgeSpawnEggItem;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
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
    public static final DeferredRegister<EntityType<?>> ENTITIES = DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, MODID);
    public static final DeferredRegister<StructureType<?>> STRUCTURE_TYPES = DeferredRegister.create(Registries.STRUCTURE_TYPE, MODID);
    public static final DeferredRegister<StructurePieceType> STRUCTURE_PIECES = DeferredRegister.create(Registries.STRUCTURE_PIECE, MODID);

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

    // Bedrock gibi: kırılamaz, patlamaya dayanıklı, piston itemez.
    public static final RegistryObject<Block> MUHUR = BLOCKS.register("muhur",
            () -> new Block(BlockBehaviour.Properties.of()
                    .mapColor(MapColor.COLOR_BLACK)
                    .instrument(NoteBlockInstrument.BASEDRUM)
                    .strength(-1.0F, 3600000.0F)
                    .noLootTable()
                    .isValidSpawn((durum, seviye, konum, tip) -> false)
                    .pushReaction(PushReaction.BLOCK)));

    public static final RegistryObject<Item> MUHUR_ITEM = ITEMS.register("muhur",
            () -> new BlockItem(MUHUR.get(), new Item.Properties()));

    public static final RegistryObject<EntityType<Asker>> ASKER = ENTITIES.register("asker",
            () -> EntityType.Builder.of(Asker::new, MobCategory.MISC)
                    .sized(0.6F, 1.95F)
                    .fireImmune()
                    .clientTrackingRange(8)
                    .build("asker"));

    public static final RegistryObject<Item> ASKER_YUMURTASI = ITEMS.register("asker_spawn_egg",
            () -> new ForgeSpawnEggItem(ASKER, 0x2B2C30, 0x0C0C0E, new Item.Properties()));

    public static final RegistryObject<StructureType<OrduBinasi>> ORDU_BINASI = STRUCTURE_TYPES.register("ordu_binasi",
            () -> () -> OrduBinasi.CODEC);

    public static final RegistryObject<StructurePieceType> ORDU_BINASI_PARCA = STRUCTURE_PIECES.register("ordu_binasi_parca",
            () -> (StructurePieceType.ContextlessType) OrduBinasiParca::new);

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
                        cikti.accept(MUHUR_ITEM.get());
                        cikti.accept(ASKER_YUMURTASI.get());
                    })
                    .build());

    public VoidDunyasi() {
        IEventBus modBus = FMLJavaModLoadingContext.get().getModEventBus();
        BLOCKS.register(modBus);
        ITEMS.register(modBus);
        SOUNDS.register(modBus);
        TABS.register(modBus);
        ENTITIES.register(modBus);
        STRUCTURE_TYPES.register(modBus);
        STRUCTURE_PIECES.register(modBus);
        modBus.addListener(this::ozellikKaydet);

        MinecraftForge.EVENT_BUS.register(new CanliEngelleyici());
    }

    private void ozellikKaydet(EntityAttributeCreationEvent event) {
        event.put(ASKER.get(), Asker.ozellikler().build());
    }
}
