package eu.royalblackwater.api.masterdata.service;

import eu.royalblackwater.api.audit.service.AuditService;
import eu.royalblackwater.api.dto.*;
import eu.royalblackwater.api.dto.MasterDataCategoryCreate;
import eu.royalblackwater.api.dto.MasterDataCategoryRead;
import eu.royalblackwater.api.dto.MasterDataCategoryUpdate;
import eu.royalblackwater.api.dto.MasterDataOptionCreate;
import eu.royalblackwater.api.dto.MasterDataOptionRead;
import eu.royalblackwater.api.dto.MasterDataOptionUpdate;
import eu.royalblackwater.api.dto.MasterDataSeedRestoreSummary;
import eu.royalblackwater.api.dto.MasterDataShipCreate;
import eu.royalblackwater.api.dto.MasterDataShipMortarModification;
import eu.royalblackwater.api.dto.MasterDataShipMount;
import eu.royalblackwater.api.dto.MasterDataShipRead;
import eu.royalblackwater.api.dto.MasterDataShipUpdate;
import eu.royalblackwater.api.dto.MasterDataShipUpgradeOverride;
import eu.royalblackwater.api.dto.MasterDataWeaponPerformance;
import eu.royalblackwater.api.masterdata.mapper.MasterDataDtoMapper;
import eu.royalblackwater.api.masterdata.repository.MasterDataRepository;
import eu.royalblackwater.api.masterdata.repository.queries.MasterDataMutationQueries;
import eu.royalblackwater.api.persistence.SqlParameters;
import eu.royalblackwater.api.security.model.AuthenticatedUser;
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
    private final MasterDataRepository repository;
    private final MasterDataQueryService queries;
    private final ReferenceDataSeeder seeder;
    private final AuditService audit;
    private final Clock clock;
    private final MasterDataDtoMapper mapper;

    public MasterDataMutationService(MasterDataRepository repository, MasterDataQueryService queries,
            ReferenceDataSeeder seeder, AuditService audit, Clock clock, MasterDataDtoMapper mapper) {
        this.repository=repository; this.queries=queries; this.seeder=seeder; this.audit=audit; this.clock=clock;
        this.mapper = mapper;
    }

    @Transactional
    public MasterDataCategoryRead createCategory(AuthenticatedUser actor, MasterDataCategoryCreate input) {
        long id=repository.insertReturningId(MasterDataMutationQueries.CREATE_CATEGORY_INSERT_01,Map.of("key",input.key(),"label",input.label(),"sort",value(input.sortOrder(),0L),
                        "active",value(input.isActive(),true),"now",now()));
        audit.record(actor,"master_data_category",id,"create","Created master-data category",Set.of("key","label"));
        return queries.category(id);
    }

    @Transactional
    public MasterDataCategoryRead updateCategory(AuthenticatedUser actor,long id,MasterDataCategoryUpdate input) {
        require("build_item_categories",id);
        repository.update(MasterDataMutationQueries.UPDATE_CATEGORY_UPDATE_01,Map.of("id",id,"label",input.label(),"sort",value(input.sortOrder(),0L),
                        "active",value(input.isActive(),true),"now",now()));
        audit.record(actor,"master_data_category",id,"update","Updated master-data category",Set.of("label","sort_order","is_active"));
        return queries.category(id);
    }

    @Transactional
    public void deleteCategory(AuthenticatedUser actor,long id) {
        require("build_item_categories",id);
        if (repository.count(MasterDataMutationQueries.DELETE_CATEGORY_SELECT_01,Map.of("id",id))>0)
            throw new ResponseStatusException(CONFLICT,"Category still contains options.");
        repository.update(MasterDataMutationQueries.DELETE_CATEGORY_DELETE_01,Map.of("id",id));
        audit.record(actor,"master_data_category",id,"delete","Deleted custom master-data category",Set.of());
    }

    @Transactional
    public MasterDataCategoryRead restoreCategory(AuthenticatedUser actor,long id) {
        requireSeeded("build_item_categories",id);
        repository.update(MasterDataMutationQueries.RESTORE_CATEGORY_UPDATE_01,Map.of("id",id));
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
        repository.update(MasterDataMutationQueries.UPDATE_OPTION_UPDATE_01,Map.of("id",id));
        audit.record(actor,"master_data_option",id,"update","Updated master-data option",Set.of("catalog"));
        return queries.option(id);
    }

    @Transactional
    public void deleteOption(AuthenticatedUser actor,long id) {
        require("build_item_options",id);
        long references=repository.count(MasterDataMutationQueries.DELETE_OPTION_SELECT_01,Map.of("id",id));
        if (references>0) throw new ResponseStatusException(CONFLICT,"Option is still referenced.");
        repository.update(MasterDataMutationQueries.DELETE_OPTION_DELETE_01,Map.of("id",id));
        audit.record(actor,"master_data_option",id,"delete","Deleted custom master-data option",Set.of());
    }

    @Transactional
    public MasterDataOptionRead restoreOption(AuthenticatedUser actor,long id) {
        requireSeeded("build_item_options",id);
        repository.update(MasterDataMutationQueries.RESTORE_OPTION_UPDATE_01,Map.of("id",id));
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
        long updated=repository.update(MasterDataMutationQueries.UPDATE_SHIP_UPDATE_01,shipParameters(id,input.name(),input.rate(),input.shipType(),input.durability(),input.speedMinKnots(),
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
        if(repository.count(MasterDataMutationQueries.DELETE_SHIP_SELECT_01,Map.of("id",id))>0)
            throw new ResponseStatusException(CONFLICT,"Ship is still referenced by builds.");
        repository.update(MasterDataMutationQueries.DELETE_SHIP_DELETE_01,Map.of("id",id));
        audit.record(actor,"master_data_ship",id,"delete","Deleted custom ship",Set.of());
    }

    @Transactional
    public MasterDataShipRead restoreShip(AuthenticatedUser actor,long id) {
        requireSeeded("ships",id);
        repository.update(MasterDataMutationQueries.RESTORE_SHIP_UPDATE_01,Map.of("id",id));
        seeder.synchronize(false);
        audit.record(actor,"master_data_ship",id,"restore_seed","Restored seeded ship",Set.of("seed"));
        return queries.ship(id);
    }

    @Transactional
    public MasterDataSeedRestoreSummary restoreAll(AuthenticatedUser actor) {
        ReferenceDataSeeder.SeedResult result=seeder.synchronize(true);
        audit.record(actor,"master_data","all","restore_seed","Restored all seed-managed master data",Set.of("seed"));
        return mapper.seedRestore(result.categories(), result.options(), result.overridesDiscarded(), result.ships());
    }

    private long writeOption(Long id,long category,String name,String source,String notes,String image,String kind,
            String weaponClass,Double caliber,Long sort,Boolean active) {
        require("build_item_categories",category);
        Long classId=lookup("weapon_classes",weaponClass);
        Map<String,Object> params=SqlParameters.ofNullable("id",id,"category",category,"name",name,"source",source,
                "notes",notes,"image",image,"kind",kind,"class",classId,"caliber",caliber,
                "sort",value(sort,0L),"active",value(active,true),"now",now());
        if(id==null) return repository.insertReturningId(MasterDataMutationQueries.WRITE_OPTION_INSERT_01,params);
        repository.update(MasterDataMutationQueries.WRITE_OPTION_UPDATE_01,params);
        return id;
    }

    private void replaceOptionChildren(long id,List<String> slots,Map<String,Double> effects,MasterDataWeaponPerformance performance) {
        repository.update(MasterDataMutationQueries.REPLACE_OPTION_CHILDREN_DELETE_01,Map.of("id",id));
        for(Map.Entry<String,Double> effect:value(effects,Map.<String,Double>of()).entrySet())
            repository.update(MasterDataMutationQueries.REPLACE_OPTION_CHILDREN_INSERT_01,
                    Map.of("id",id,"key",effect.getKey(),"value",effect.getValue()));
        repository.update(MasterDataMutationQueries.REPLACE_OPTION_CHILDREN_DELETE_02,Map.of("id",id));
        for(String slot:value(slots,List.<String>of())) repository.update(MasterDataMutationQueries.REPLACE_OPTION_CHILDREN_INSERT_02,Map.of("id",id,"code",slot));
        repository.update(MasterDataMutationQueries.REPLACE_OPTION_CHILDREN_DELETE_03,Map.of("id",id));
        if(performance!=null) repository.update(MasterDataMutationQueries.REPLACE_OPTION_CHILDREN_INSERT_03,
                Map.of("id",id,"damage",performance.baseDamage(),"reload",performance.reloadSeconds()));
    }

    private long writeShip(Long id,MasterDataShipCreate input) {
        Map<String,Object> params=shipParameters(id,input.name(),input.rate(),input.shipType(),input.durability(),input.speedMinKnots(),
                input.speedKnots(),input.maneuverability(),input.armor(),input.holdCapacity(),input.crewCapacity(),input.sailorMinimum(),
                input.displacementTons(),input.source(),input.imageUrl(),input.sailSlots(),input.upgradeSlots(),input.hasLantern(),input.isActive());
        return repository.insertReturningId(MasterDataMutationQueries.WRITE_SHIP_INSERT_01,params);
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
        repository.update(MasterDataMutationQueries.REPLACE_SHIP_CHILDREN_DELETE_01,Map.of("id",id));
        for(MasterDataShipMount mount:value(mounts,List.<MasterDataShipMount>of())) repository.update(MasterDataMutationQueries.REPLACE_SHIP_CHILDREN_INSERT_01,SqlParameters.ofNullable("ship",id,"capacity",value(mount.capacity(),0L),"special",value(mount.specialWeaponCapacity(),0L),
                        "class",mount.maxWeaponClass(),"caliber",mount.maxCaliberInches(),"slot",mount.slotType()));
        repository.update(MasterDataMutationQueries.REPLACE_SHIP_CHILDREN_DELETE_02,Map.of("id",id));
        if(mortar!=null) repository.update(MasterDataMutationQueries.REPLACE_SHIP_CHILDREN_INSERT_02,Map.of("id",id,"capacity",mortar.mortarCapacity(),"caliber",mortar.maxCaliberInches(),
                        "broadside",mortar.broadsideCapacityDelta(),"durability",mortar.durabilityDelta(),"speed",value(mortar.speedPct(),0D),
                        "maneuver",value(mortar.maneuverabilityDelta(),0D),"hold",value(mortar.holdCapacityPct(),0D),
                        "crew",mortar.crewCapacityDelta(),"source",mortar.source()));
        repository.update(MasterDataMutationQueries.REPLACE_SHIP_CHILDREN_DELETE_03,Map.of("id",id));
        for(MasterDataShipUpgradeOverride override:value(overrides,List.<MasterDataShipUpgradeOverride>of()))
            for(Map.Entry<String,Double> effect:value(override.statEffects(),Map.<String,Double>of()).entrySet())
                repository.update(MasterDataMutationQueries.REPLACE_SHIP_CHILDREN_INSERT_03,Map.of("ship",id,"option",override.optionId(),"key",effect.getKey(),"value",effect.getValue(),"now",now()));
    }

    private void require(String table,long id) {
        if(!Set.of("build_item_categories","build_item_options","ships").contains(table)) throw new IllegalArgumentException();
        if(repository.count(MasterDataMutationQueries.REQUIRE_SELECT_01+table+MasterDataMutationQueries.REQUIRE_WHERE_01,Map.of("id",id))==0)
            throw new ResponseStatusException(NOT_FOUND,"Master-data record not found.");
    }
    private void requireSeeded(String table,long id) {
        require(table,id);
        if(repository.count(MasterDataMutationQueries.REQUIRE_SELECT_01+table+MasterDataMutationQueries.REQUIRE_SEEDED_WHERE_01,Map.of("id",id))==0)
            throw new ResponseStatusException(CONFLICT,"Custom records cannot be restored from seed data.");
    }
    private Long lookup(String table,String code) {
        if(code==null||code.isBlank()) return null;
        if(!"weapon_classes".equals(table)) throw new IllegalArgumentException();
        return repository.optional(MasterDataMutationQueries.LOOKUP_SELECT_01,Map.of("code",code))
                .map(row->((Number)row.get("id")).longValue()).orElseThrow(()->new ResponseStatusException(CONFLICT,"Unknown weapon class."));
    }
    private LocalDateTime now(){ return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    private static <T>T value(T value,T fallback){ return value==null?fallback:value; }
}
