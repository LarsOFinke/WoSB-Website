package eu.royalblackwater.api.masterdata;

import eu.royalblackwater.api.audit.AuditService;
import eu.royalblackwater.api.contract.*;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.AuthenticatedUser;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.CONFLICT;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class MasterDataMutationService {
    private final JdbcQueryService jdbc;
    private final MasterDataQueryService queries;
    private final ReferenceDataSeeder seeder;
    private final AuditService audit;
    private final Clock clock;

    public MasterDataMutationService(JdbcQueryService jdbc, MasterDataQueryService queries,
            ReferenceDataSeeder seeder, AuditService audit, Clock clock) {
        this.jdbc=jdbc; this.queries=queries; this.seeder=seeder; this.audit=audit; this.clock=clock;
    }

    @Transactional
    public MasterDataCategoryRead createCategory(AuthenticatedUser actor, MasterDataCategoryCreate input) {
        long id=jdbc.insertReturningId("""
                insert into build_item_categories(key,label,sort_order,is_active,is_seed_overridden,created_at,updated_at)
                values(:key,:label,:sort,:active,false,:now,:now) returning id
                """,Map.of("key",input.key(),"label",input.label(),"sort",value(input.sortOrder(),0L),
                        "active",value(input.isActive(),true),"now",now()));
        audit.record(actor,"master_data_category",id,"create","Created master-data category",Set.of("key","label"));
        return queries.category(id);
    }

    @Transactional
    public MasterDataCategoryRead updateCategory(AuthenticatedUser actor,long id,MasterDataCategoryUpdate input) {
        require("build_item_categories",id);
        jdbc.update("""
                update build_item_categories set label=:label,sort_order=:sort,is_active=:active,
                    is_seed_overridden=case when seed_key is null then false else true end,updated_at=:now where id=:id
                """,Map.of("id",id,"label",input.label(),"sort",value(input.sortOrder(),0L),
                        "active",value(input.isActive(),true),"now",now()));
        audit.record(actor,"master_data_category",id,"update","Updated master-data category",Set.of("label","sort_order","is_active"));
        return queries.category(id);
    }

    @Transactional
    public void deleteCategory(AuthenticatedUser actor,long id) {
        require("build_item_categories",id);
        if (jdbc.count("select count(*) from build_item_options where category_id=:id",Map.of("id",id))>0)
            throw new ResponseStatusException(CONFLICT,"Category still contains options.");
        jdbc.update("delete from build_item_categories where id=:id",Map.of("id",id));
        audit.record(actor,"master_data_category",id,"delete","Deleted custom master-data category",Set.of());
    }

    @Transactional
    public MasterDataCategoryRead restoreCategory(AuthenticatedUser actor,long id) {
        requireSeeded("build_item_categories",id);
        jdbc.update("update build_item_categories set is_seed_overridden=false where id=:id",Map.of("id",id));
        seeder.synchronize(false);
        audit.record(actor,"master_data_category",id,"restore_seed","Restored seeded category",Set.of("seed"));
        return queries.category(id);
    }

    @Transactional
    public MasterDataOptionRead createOption(AuthenticatedUser actor,MasterDataOptionCreate input) {
        long id=writeOption(null,input.categoryId(),input.name(),input.source(),input.notes(),input.imageUrl(),input.optionKind(),
                input.weaponClass(),input.weaponCaliberInches(),input.sortOrder(),input.isActive());
        replaceOptionChildren(id,input.allowedSlotTypes(),input.statEffects(),input.weaponPerformance());
        audit.record(actor,"master_data_option",id,"create","Created master-data option",Set.of("category","name"));
        return queries.option(id);
    }

    @Transactional
    public MasterDataOptionRead updateOption(AuthenticatedUser actor,long id,MasterDataOptionUpdate input) {
        require("build_item_options",id);
        writeOption(id,input.categoryId(),input.name(),input.source(),input.notes(),input.imageUrl(),input.optionKind(),
                input.weaponClass(),input.weaponCaliberInches(),input.sortOrder(),input.isActive());
        replaceOptionChildren(id,input.allowedSlotTypes(),input.statEffects(),input.weaponPerformance());
        jdbc.update("update build_item_options set is_seed_overridden=seed_key is not null where id=:id",Map.of("id",id));
        audit.record(actor,"master_data_option",id,"update","Updated master-data option",Set.of("catalog"));
        return queries.option(id);
    }

    @Transactional
    public void deleteOption(AuthenticatedUser actor,long id) {
        require("build_item_options",id);
        long references=jdbc.count("""
                select (select count(*) from build_slot_items where option_id=:id)
                     +(select count(*) from build_inventory_items where option_id=:id)
                     +(select count(*) from build_weapon_items where option_id=:id)
                     +(select count(*) from ship_upgrade_effect_overrides where option_id=:id)
                """,Map.of("id",id));
        if (references>0) throw new ResponseStatusException(CONFLICT,"Option is still referenced.");
        jdbc.update("delete from build_item_options where id=:id",Map.of("id",id));
        audit.record(actor,"master_data_option",id,"delete","Deleted custom master-data option",Set.of());
    }

    @Transactional
    public MasterDataOptionRead restoreOption(AuthenticatedUser actor,long id) {
        requireSeeded("build_item_options",id);
        jdbc.update("update build_item_options set is_seed_overridden=false where id=:id",Map.of("id",id));
        seeder.synchronize(false);
        audit.record(actor,"master_data_option",id,"restore_seed","Restored seeded option",Set.of("seed"));
        return queries.option(id);
    }

    @Transactional
    public MasterDataShipRead createShip(AuthenticatedUser actor,MasterDataShipCreate input) {
        long id=writeShip(null,input);
        replaceShipChildren(id,input.weaponMounts(),input.mortarModification(),input.upgradeEffectOverrides());
        audit.record(actor,"master_data_ship",id,"create","Created ship",Set.of("name","rate"));
        return queries.ship(id);
    }

    @Transactional
    public MasterDataShipRead updateShip(AuthenticatedUser actor,long id,MasterDataShipUpdate input) {
        require("ships",id);
        long updated=jdbc.update("""
                update ships set name=:name,rate=:rate,ship_type=:type,durability=:durability,
                    speed_min_knots=:speedMin,speed_knots=:speed,maneuverability=:maneuver,armor=:armor,
                    hold_capacity=:hold,crew_capacity=:crew,sailor_minimum=:sailors,displacement_tons=:displacement,
                    source=:source,image_url=:image,sail_slots=:sails,upgrade_slots=:upgrades,has_lantern=:lantern,
                    is_active=:active,is_seed_overridden=seed_key is not null,updated_at=:now where id=:id
                """,shipParameters(id,input.name(),input.rate(),input.shipType(),input.durability(),input.speedMinKnots(),
                        input.speedKnots(),input.maneuverability(),input.armor(),input.holdCapacity(),input.crewCapacity(),
                        input.sailorMinimum(),input.displacementTons(),input.source(),input.imageUrl(),input.sailSlots(),
                        input.upgradeSlots(),input.hasLantern(),input.isActive()));
        if(updated!=1) throw new ResponseStatusException(NOT_FOUND,"Ship not found.");
        replaceShipChildren(id,input.weaponMounts(),input.mortarModification(),input.upgradeEffectOverrides());
        audit.record(actor,"master_data_ship",id,"update","Updated ship",Set.of("catalog"));
        return queries.ship(id);
    }

    @Transactional
    public void deleteShip(AuthenticatedUser actor,long id) {
        require("ships",id);
        if(jdbc.count("select count(*) from builds where ship_id=:id",Map.of("id",id))>0)
            throw new ResponseStatusException(CONFLICT,"Ship is still referenced by builds.");
        jdbc.update("delete from ships where id=:id",Map.of("id",id));
        audit.record(actor,"master_data_ship",id,"delete","Deleted custom ship",Set.of());
    }

    @Transactional
    public MasterDataShipRead restoreShip(AuthenticatedUser actor,long id) {
        requireSeeded("ships",id);
        jdbc.update("update ships set is_seed_overridden=false where id=:id",Map.of("id",id));
        seeder.synchronize(false);
        audit.record(actor,"master_data_ship",id,"restore_seed","Restored seeded ship",Set.of("seed"));
        return queries.ship(id);
    }

    @Transactional
    public MasterDataSeedRestoreSummary restoreAll(AuthenticatedUser actor) {
        ReferenceDataSeeder.SeedResult result=seeder.synchronize(true);
        audit.record(actor,"master_data","all","restore_seed","Restored all seed-managed master data",Set.of("seed"));
        long total=result.categories()+result.options()+result.ships();
        return new MasterDataSeedRestoreSummary(result.categories(),true,result.options(),result.overridesDiscarded(),result.ships(),total);
    }

    private long writeOption(Long id,long category,String name,String source,String notes,String image,String kind,
            String weaponClass,Double caliber,Long sort,Boolean active) {
        require("build_item_categories",category);
        Long classId=lookup("weapon_classes",weaponClass);
        Map<String,Object> params=SqlParameters.ofNullable("id",id,"category",category,"name",name,"source",source,
                "notes",notes,"image",image,"kind",kind,"class",classId,"caliber",caliber,
                "sort",value(sort,0L),"active",value(active,true),"now",now());
        if(id==null) return jdbc.insertReturningId("""
                insert into build_item_options(category_id,name,source,notes,image_url,option_kind,weapon_class_id,
                    weapon_caliber_inches,sort_order,is_active,is_seed_overridden,created_at,updated_at)
                values(:category,:name,:source,:notes,:image,:kind,:class,:caliber,:sort,:active,false,:now,:now) returning id
                """,params);
        jdbc.update("""
                update build_item_options set category_id=:category,name=:name,source=:source,notes=:notes,
                    image_url=:image,option_kind=:kind,weapon_class_id=:class,weapon_caliber_inches=:caliber,
                    sort_order=:sort,is_active=:active,updated_at=:now where id=:id
                """,params);
        return id;
    }

    private void replaceOptionChildren(long id,List<String> slots,Map<String,Double> effects,MasterDataWeaponPerformance performance) {
        jdbc.update("delete from build_item_effects where option_id=:id",Map.of("id",id));
        for(Map.Entry<String,Double> effect:value(effects,Map.<String,Double>of()).entrySet())
            jdbc.update("insert into build_item_effects(option_id,effect_key,effect_value) values(:id,:key,:value)",
                    Map.of("id",id,"key",effect.getKey(),"value",effect.getValue()));
        jdbc.update("delete from build_item_option_slot_types where option_id=:id",Map.of("id",id));
        for(String slot:value(slots,List.<String>of())) jdbc.update("""
                insert into build_item_option_slot_types(option_id,slot_type_id)
                select :id,id from weapon_slot_types where code=:code
                """,Map.of("id",id,"code",slot));
        jdbc.update("delete from weapon_performance_profiles where option_id=:id",Map.of("id",id));
        if(performance!=null) jdbc.update("insert into weapon_performance_profiles(option_id,base_damage,reload_seconds) values(:id,:damage,:reload)",
                Map.of("id",id,"damage",performance.baseDamage(),"reload",performance.reloadSeconds()));
    }

    private long writeShip(Long id,MasterDataShipCreate input) {
        Map<String,Object> params=shipParameters(id,input.name(),input.rate(),input.shipType(),input.durability(),input.speedMinKnots(),
                input.speedKnots(),input.maneuverability(),input.armor(),input.holdCapacity(),input.crewCapacity(),input.sailorMinimum(),
                input.displacementTons(),input.source(),input.imageUrl(),input.sailSlots(),input.upgradeSlots(),input.hasLantern(),input.isActive());
        return jdbc.insertReturningId("""
                insert into ships(name,rate,ship_type,durability,speed_min_knots,speed_knots,maneuverability,armor,
                    hold_capacity,crew_capacity,sailor_minimum,displacement_tons,source,image_url,sail_slots,upgrade_slots,
                    has_lantern,is_active,is_seed_overridden,created_at,updated_at)
                values(:name,:rate,:type,:durability,:speedMin,:speed,:maneuver,:armor,:hold,:crew,:sailors,:displacement,
                    :source,:image,:sails,:upgrades,:lantern,:active,false,:now,:now) returning id
                """,params);
    }

    private Map<String,Object> shipParameters(Long id,String name,long rate,String type,Long durability,Double speedMin,Double speed,
            Double maneuver,Double armor,Long hold,Long crew,Long sailors,Long displacement,String source,String image,
            Long sails,Long upgrades,Boolean lantern,Boolean active) {
        return SqlParameters.ofNullable("id",id,"name",name,"rate",rate,"type",type,"durability",value(durability,0L),
                "speedMin",value(speedMin,0D),"speed",value(speed,0D),"maneuver",value(maneuver,0D),"armor",value(armor,0D),
                "hold",value(hold,0L),"crew",value(crew,0L),"sailors",value(sailors,0L),"displacement",value(displacement,0L),
                "source",source,"image",image,"sails",value(sails,0L),"upgrades",value(upgrades,0L),
                "lantern",value(lantern,false),"active",value(active,true),"now",now());
    }

    private void replaceShipChildren(long id,List<MasterDataShipMount> mounts,MasterDataShipMortarModification mortar,
            List<MasterDataShipUpgradeOverride> overrides) {
        jdbc.update("delete from ship_weapon_mounts where ship_id=:id",Map.of("id",id));
        for(MasterDataShipMount mount:value(mounts,List.<MasterDataShipMount>of())) jdbc.update("""
                insert into ship_weapon_mounts(ship_id,slot_type_id,capacity,special_weapon_capacity,max_weapon_class_id,max_caliber_inches)
                select :ship,slot.id,:capacity,:special,wc.id,:caliber from weapon_slot_types slot
                left join weapon_classes wc on wc.code=:class where slot.code=:slot
                """,SqlParameters.ofNullable("ship",id,"capacity",value(mount.capacity(),0L),"special",value(mount.specialWeaponCapacity(),0L),
                        "class",mount.maxWeaponClass(),"caliber",mount.maxCaliberInches(),"slot",mount.slotType()));
        jdbc.update("delete from ship_mortar_modifications where ship_id=:id",Map.of("id",id));
        if(mortar!=null) jdbc.update("""
                insert into ship_mortar_modifications(ship_id,mortar_capacity,max_caliber_inches,broadside_capacity_delta,
                    durability_delta,speed_pct,maneuverability_delta,hold_capacity_pct,crew_capacity_delta,source)
                values(:id,:capacity,:caliber,:broadside,:durability,:speed,:maneuver,:hold,:crew,:source)
                """,Map.of("id",id,"capacity",mortar.mortarCapacity(),"caliber",mortar.maxCaliberInches(),
                        "broadside",mortar.broadsideCapacityDelta(),"durability",mortar.durabilityDelta(),"speed",value(mortar.speedPct(),0D),
                        "maneuver",value(mortar.maneuverabilityDelta(),0D),"hold",value(mortar.holdCapacityPct(),0D),
                        "crew",mortar.crewCapacityDelta(),"source",mortar.source()));
        jdbc.update("delete from ship_upgrade_effect_overrides where ship_id=:id",Map.of("id",id));
        for(MasterDataShipUpgradeOverride override:value(overrides,List.<MasterDataShipUpgradeOverride>of()))
            for(Map.Entry<String,Double> effect:value(override.statEffects(),Map.<String,Double>of()).entrySet())
                jdbc.update("""
                        insert into ship_upgrade_effect_overrides(ship_id,option_id,effect_key,effect_value,created_at,updated_at)
                        values(:ship,:option,:key,:value,:now,:now)
                        """,Map.of("ship",id,"option",override.optionId(),"key",effect.getKey(),"value",effect.getValue(),"now",now()));
    }

    private void require(String table,long id) {
        if(!Set.of("build_item_categories","build_item_options","ships").contains(table)) throw new IllegalArgumentException();
        if(jdbc.count("select count(*) from "+table+" where id=:id",Map.of("id",id))==0)
            throw new ResponseStatusException(NOT_FOUND,"Master-data record not found.");
    }
    private void requireSeeded(String table,long id) {
        require(table,id);
        if(jdbc.count("select count(*) from "+table+" where id=:id and seed_key is not null",Map.of("id",id))==0)
            throw new ResponseStatusException(CONFLICT,"Custom records cannot be restored from seed data.");
    }
    private Long lookup(String table,String code) {
        if(code==null||code.isBlank()) return null;
        if(!"weapon_classes".equals(table)) throw new IllegalArgumentException();
        return jdbc.optional("select id from weapon_classes where code=:code",Map.of("code",code))
                .map(row->((Number)row.get("id")).longValue()).orElseThrow(()->new ResponseStatusException(CONFLICT,"Unknown weapon class."));
    }
    private LocalDateTime now(){ return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    private static <T>T value(T value,T fallback){ return value==null?fallback:value; }
}
