"""Strict JSON boundary for repository-owned master data."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


def _resolve_backend_root() -> Path:
    source_root = Path(__file__).resolve().parents[3]
    configured_alembic = os.environ.get("RBF_ALEMBIC_CONFIG")
    candidates = [
        source_root,
        Path(configured_alembic).resolve().parent if configured_alembic else None,
        Path.cwd().resolve(),
    ]
    for candidate in candidates:
        if candidate is not None and (candidate / "seeds" / "manifest.json").is_file():
            return candidate
    return source_root


BACKEND_ROOT = _resolve_backend_root()
MASTER_DATA_ROOT = BACKEND_ROOT / "seeds"
MASTER_DATA_MANIFEST_PATH = MASTER_DATA_ROOT / "manifest.json"
SHIP_SEED_PATH = MASTER_DATA_ROOT / "ships"

WeaponClassCode = Literal["light", "medium", "heavy"]
WeaponSlotCode = Literal[
    "weapon_front",
    "weapon_rear",
    "weapon_port",
    "weapon_starboard",
    "weapon_mortar",
    "weapon_special",
]
EXPECTED_WEAPON_SLOT_CODES = {
    "weapon_front",
    "weapon_rear",
    "weapon_port",
    "weapon_starboard",
    "weapon_mortar",
    "weapon_special",
}


class StrictSeedModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ManifestDocument(StrictSeedModel):
    path: str = Field(min_length=1)
    kind: Literal[
        "references",
        "roles",
        "fleets",
        "build_rules",
        "build_categories",
        "build_options",
        "ship_definitions",
        "ships",
    ]


class CatalogManifest(StrictSeedModel):
    schema_version: Literal[1]
    catalog: Literal["wosb-master-data"]
    documents: list[ManifestDocument] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_paths(self) -> "CatalogManifest":
        paths = [row.path for row in self.documents]
        if len(paths) != len(set(paths)):
            raise ValueError("manifest document paths must be unique")
        for path in paths:
            candidate = Path(path)
            if candidate.is_absolute() or ".." in candidate.parts or candidate.suffix != ".json":
                raise ValueError(f"unsafe manifest document path: {path}")
        return self


class ReferenceCatalogDocument(StrictSeedModel):
    schema_version: Literal[1]
    catalog: Literal["catalog-references"]
    items: dict[str, str]


class SiteRoleSeed(StrictSeedModel):
    code: str = Field(min_length=1, max_length=40)
    label: str = Field(min_length=1, max_length=80)
    rank: int = Field(ge=0)
    is_staff: bool
    can_manage_system: bool


class FleetRoleSeed(StrictSeedModel):
    code: str = Field(min_length=1, max_length=40)
    label: str = Field(min_length=1, max_length=80)
    rank: int = Field(ge=0)
    is_leadership: bool
    can_manage_fleet: bool
    can_manage_members: bool
    is_system: bool
    is_active: bool


class SquadRoleSeed(StrictSeedModel):
    code: str = Field(min_length=1, max_length=40)
    label: str = Field(min_length=1, max_length=80)
    rank: int = Field(ge=0)
    can_manage_roster: bool
    can_manage_events: bool


class RoleCatalogDocument(StrictSeedModel):
    schema_version: Literal[1]
    catalog: Literal["system-roles"]
    site_roles: list[SiteRoleSeed] = Field(min_length=1)
    fleet_roles: list[FleetRoleSeed] = Field(min_length=1)
    squad_roles: list[SquadRoleSeed] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_role_codes(self) -> "RoleCatalogDocument":
        expected_codes = {
            "site": {"user", "moderator", "admin"},
            "fleet": {"member", "fleet_lieutenant", "fleet_admiral"},
            "squad": {"member", "officer", "leader"},
        }
        for label, rows in (
            ("site", self.site_roles),
            ("fleet", self.fleet_roles),
            ("squad", self.squad_roles),
        ):
            codes = [row.code for row in rows]
            if len(codes) != len(set(codes)):
                raise ValueError(f"{label} role codes must be unique")
            if set(codes) != expected_codes[label]:
                raise ValueError(
                    f"{label} roles must define exactly {sorted(expected_codes[label])}"
                )
        return self


class FleetSeed(StrictSeedModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=120)
    focus: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1)
    standing_orders: str = Field(min_length=1)
    sort_order: int = Field(ge=0)
    is_active: bool = True


class FleetCatalogDocument(StrictSeedModel):
    schema_version: Literal[1]
    catalog: Literal["system-fleets"]
    legacy_slugs: list[str]
    items: list[FleetSeed] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_fleets(self) -> "FleetCatalogDocument":
        slugs = [row.slug for row in self.items]
        if len(slugs) != len(set(slugs)):
            raise ValueError("fleet slugs must be unique")
        if set(slugs) & set(self.legacy_slugs):
            raise ValueError("current fleet slugs cannot also be legacy slugs")
        return self


class BuildFeatureSeed(StrictSeedModel):
    code: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    label: str = Field(min_length=1, max_length=120)
    upgrade_slots_granted: int = Field(ge=0, le=8)
    stat_effects: dict[str, int | float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_stat_effects(self) -> "BuildFeatureSeed":
        for key in self.stat_effects:
            if not key.strip() or len(key) > 80 or not key.replace("_", "").isalnum():
                raise ValueError(f"invalid build feature effect key: {key}")
        return self


class ShipRateWeaponClassRuleSeed(StrictSeedModel):
    rate: int = Field(ge=1, le=7)
    weapon_class: WeaponClassCode


class BuildRuleCatalogDocument(StrictSeedModel):
    schema_version: Literal[1]
    catalog: Literal["build-rules"]
    build_features: list[BuildFeatureSeed] = Field(min_length=1)
    ship_rate_weapon_classes: list[ShipRateWeaponClassRuleSeed] = Field(min_length=7, max_length=7)

    @model_validator(mode="after")
    def validate_rules(self) -> "BuildRuleCatalogDocument":
        feature_codes = [row.code for row in self.build_features]
        if len(feature_codes) != len(set(feature_codes)):
            raise ValueError("build feature codes must be unique")
        if "research_upgrade_slot" not in feature_codes:
            raise ValueError("build rules must define research_upgrade_slot")
        rates = [row.rate for row in self.ship_rate_weapon_classes]
        if sorted(rates) != list(range(1, 8)):
            raise ValueError("ship rate weapon classes must define rates 1 through 7 exactly once")
        return self


class BuildCategorySeed(StrictSeedModel):
    key: str = Field(min_length=1, max_length=60)
    label: str = Field(min_length=1, max_length=80)
    sort_order: int = Field(ge=0)
    is_active: bool = True


class BuildCategoryDocument(StrictSeedModel):
    schema_version: Literal[1]
    catalog: Literal["build-categories"]
    items: list[BuildCategorySeed] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_categories(self) -> "BuildCategoryDocument":
        keys = [row.key for row in self.items]
        if len(keys) != len(set(keys)):
            raise ValueError("build category keys must be unique")
        return self


class WeaponPerformanceSeed(StrictSeedModel):
    base_damage: float = Field(ge=0)
    reload_seconds: float = Field(gt=0)


class BuildOptionSeed(StrictSeedModel):
    category: str = Field(min_length=1, max_length=60)
    seed_id: str = Field(min_length=1, max_length=160)
    name: str = Field(min_length=1, max_length=160)
    source: str = Field(min_length=1, max_length=500)
    notes: str | None = None
    image_url: str | None = None
    option_kind: str | None = Field(default=None, max_length=80)
    stat_effects: dict[str, int | float] = Field(default_factory=dict)
    allowed_slot_types: list[WeaponSlotCode] = Field(default_factory=list)
    weapon_class: WeaponClassCode | None = None
    weapon_caliber_inches: float | None = Field(default=None, ge=0)
    weapon_performance: WeaponPerformanceSeed | None = None
    is_active: bool = True


class BuildOptionDocument(StrictSeedModel):
    schema_version: Literal[1]
    catalog: str = Field(pattern=r"^build-options-")
    category: str = Field(min_length=1, max_length=60)
    aliases: dict[str, str] = Field(default_factory=dict)
    items: list[BuildOptionSeed] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_options(self) -> "BuildOptionDocument":
        if any(row.category != self.category for row in self.items):
            raise ValueError(f"all options must belong to category {self.category!r}")
        names = [row.name.casefold() for row in self.items]
        seed_ids = [row.seed_id.casefold() for row in self.items]
        if len(names) != len(set(names)):
            raise ValueError(f"option names must be unique in {self.category}")
        if len(seed_ids) != len(set(seed_ids)):
            raise ValueError(f"option seed_id values must be unique in {self.category}")
        return self


class WeaponClassSeed(StrictSeedModel):
    code: WeaponClassCode
    label: str = Field(min_length=1, max_length=80)
    rank: int = Field(ge=0)


class WeaponSlotTypeSeed(StrictSeedModel):
    code: WeaponSlotCode
    label: str = Field(min_length=1, max_length=80)
    sort_order: int = Field(ge=0)


class ShipWeaponMountSeed(StrictSeedModel):
    slot_type: WeaponSlotCode
    capacity: int = Field(ge=0, le=1000)
    max_weapon_class: WeaponClassCode | None = None
    max_caliber_inches: float | None = Field(default=None, ge=0)
    special_weapon_capacity: int = Field(default=0, ge=0, le=1000)

    @model_validator(mode="after")
    def validate_mount_rules(self) -> "ShipWeaponMountSeed":
        if self.special_weapon_capacity > self.capacity:
            raise ValueError("special_weapon_capacity cannot exceed mount capacity")
        if self.special_weapon_capacity and self.slot_type not in {
            "weapon_front",
            "weapon_rear",
            "weapon_special",
        }:
            raise ValueError("special weapons are only valid on bow, stern or dedicated mounts")
        if self.slot_type == "weapon_mortar":
            if self.max_weapon_class is not None:
                raise ValueError("mortar mounts cannot use a regular weapon class")
            if self.capacity > 0 and self.max_caliber_inches is None:
                raise ValueError("armed mortar mounts require max_caliber_inches")
        elif self.max_caliber_inches is not None:
            raise ValueError("max_caliber_inches is only valid on mortar mounts")
        if self.slot_type == "weapon_special":
            if self.max_weapon_class is not None:
                raise ValueError("dedicated special mounts cannot use a regular weapon class")
            if self.special_weapon_capacity != self.capacity:
                raise ValueError(
                    "dedicated special mounts must expose their full capacity to special weapons"
                )
        elif self.capacity > 0 and self.slot_type != "weapon_mortar":
            if self.max_weapon_class is None:
                raise ValueError("armed regular mounts require max_weapon_class")
        return self


class ShipUpgradeEffectOverrideSeed(StrictSeedModel):
    upgrade_seed_id: str = Field(min_length=1, max_length=160)
    stat_effects: dict[str, int | float] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_effects(self) -> "ShipUpgradeEffectOverrideSeed":
        if any(not key.strip() or len(key) > 80 for key in self.stat_effects):
            raise ValueError("ship upgrade effect keys must be non-empty and at most 80 characters")
        return self


class ShipMortarModificationSeed(StrictSeedModel):
    mortar_capacity: int = Field(gt=0, le=8)
    max_caliber_inches: float = Field(gt=0, le=20)
    broadside_capacity_delta: int = Field(le=0)
    durability_delta: int = Field(le=0)
    speed_pct: float = Field(default=0, gt=-100)
    maneuverability_delta: float = 0
    hold_capacity_pct: float = Field(default=0, gt=-100)
    crew_capacity_delta: int = Field(le=0)
    source: str = Field(min_length=1, max_length=500)


class ShipSeed(StrictSeedModel):
    seed_id: str = Field(min_length=1, max_length=160)
    name: str = Field(min_length=1, max_length=120)
    rate: int = Field(ge=1, le=7)
    ship_type: str = Field(min_length=1, max_length=80)
    durability: int = Field(gt=0)
    speed_min_knots: float = Field(ge=0)
    speed_knots: float = Field(ge=0)
    maneuverability: float = Field(ge=0)
    armor: float = Field(ge=0)
    hold_capacity: int = Field(gt=0)
    crew_capacity: int = Field(gt=0)
    sailor_minimum: int = Field(ge=0)
    displacement_tons: int = Field(ge=0)
    source: str = Field(min_length=1, max_length=240)
    image_url: str | None = Field(default=None, max_length=500)
    sail_slots: int = Field(default=1, ge=0, le=20)
    upgrade_slots: int = Field(default=5, ge=0, le=8)
    has_lantern: bool = True
    is_active: bool = True
    mortar_modification: ShipMortarModificationSeed | None
    upgrade_effect_overrides: list[ShipUpgradeEffectOverrideSeed] = Field(default_factory=list)
    weapon_mounts: list[ShipWeaponMountSeed] = Field(min_length=6, max_length=6)

    @model_validator(mode="after")
    def validate_ship_rules(self) -> "ShipSeed":
        if self.speed_knots < self.speed_min_knots:
            raise ValueError("speed_knots cannot be below speed_min_knots")
        if self.sailor_minimum > self.crew_capacity:
            raise ValueError("sailor_minimum cannot exceed crew_capacity")
        if self.ship_type != "Montgolfiere" and self.displacement_tons <= 0:
            raise ValueError("non-Montgolfiere ships require positive displacement_tons")
        if not self.source.startswith(("WoSB wiki", "WoSB in-game")):
            raise ValueError("source must identify an audited WoSB catalog")

        override_ids = [row.upgrade_seed_id.casefold() for row in self.upgrade_effect_overrides]
        if len(override_ids) != len(set(override_ids)):
            raise ValueError("ship upgrade override seed IDs must be unique")

        mounts = {mount.slot_type: mount for mount in self.weapon_mounts}
        if len(mounts) != len(self.weapon_mounts):
            raise ValueError("weapon mount slot types must be unique")
        if set(mounts) != EXPECTED_WEAPON_SLOT_CODES:
            missing = sorted(EXPECTED_WEAPON_SLOT_CODES - set(mounts))
            extra = sorted(set(mounts) - EXPECTED_WEAPON_SLOT_CODES)
            raise ValueError(f"weapon mounts must be explicit; missing={missing}, extra={extra}")
        if mounts["weapon_port"].capacity != mounts["weapon_starboard"].capacity:
            raise ValueError("port and starboard broadside capacities must match")
        if mounts["weapon_port"].max_weapon_class != mounts["weapon_starboard"].max_weapon_class:
            raise ValueError("port and starboard weapon classes must match")
        if self.mortar_modification is not None:
            modification = self.mortar_modification
            if mounts["weapon_mortar"].capacity > 0:
                raise ValueError(
                    "mortar modification is only supported for ships without a base mortar mount"
                )
            if mounts["weapon_port"].capacity + modification.broadside_capacity_delta < 0:
                raise ValueError("mortar modification cannot reduce broadside capacity below zero")
            if self.durability + modification.durability_delta <= 0:
                raise ValueError("mortar modification cannot reduce durability below one")
            if self.crew_capacity + modification.crew_capacity_delta <= 0:
                raise ValueError("mortar modification cannot reduce crew capacity below one")
        return self


class ShipDefinitionDocument(StrictSeedModel):
    schema_version: Literal[1]
    catalog: Literal["ship-definitions"]
    sources: dict[str, str]
    weapon_classes: list[WeaponClassSeed] = Field(min_length=3, max_length=3)
    weapon_slot_types: list[WeaponSlotTypeSeed] = Field(min_length=6, max_length=6)

    @model_validator(mode="after")
    def validate_definitions(self) -> "ShipDefinitionDocument":
        class_codes = [row.code for row in self.weapon_classes]
        if set(class_codes) != {"light", "medium", "heavy"} or len(class_codes) != 3:
            raise ValueError("weapon_classes must define light, medium and heavy exactly once")
        slot_codes = [row.code for row in self.weapon_slot_types]
        if set(slot_codes) != EXPECTED_WEAPON_SLOT_CODES or len(slot_codes) != 6:
            raise ValueError("weapon_slot_types must define every supported mount exactly once")
        return self


class ShipRateDocument(StrictSeedModel):
    schema_version: Literal[1]
    catalog: str = Field(pattern=r"^ships-rate-[1-7]$")
    rate: int = Field(ge=1, le=7)
    items: list[ShipSeed] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_rate(self) -> "ShipRateDocument":
        if self.catalog != f"ships-rate-{self.rate}":
            raise ValueError("ship catalog name must match its rate")
        if any(row.rate != self.rate for row in self.items):
            raise ValueError(f"all ships must have rate {self.rate}")
        return self


class ShipSeedDocument(StrictSeedModel):
    schema_version: Literal[1] = 1
    catalog: Literal["ships"] = "ships"
    sources: dict[str, str]
    weapon_classes: list[WeaponClassSeed]
    weapon_slot_types: list[WeaponSlotTypeSeed]
    ships: list[ShipSeed]

    @model_validator(mode="after")
    def validate_catalog_identity(self) -> "ShipSeedDocument":
        ship_names = [row.name.casefold() for row in self.ships]
        seed_ids = [row.seed_id.casefold() for row in self.ships]
        if len(ship_names) != len(set(ship_names)):
            raise ValueError("ship names must be unique")
        if len(seed_ids) != len(set(seed_ids)):
            raise ValueError("ship seed_id values must be unique")
        return self


class MasterDataCatalog(StrictSeedModel):
    manifest: CatalogManifest
    references: ReferenceCatalogDocument
    roles: RoleCatalogDocument
    fleets: FleetCatalogDocument
    build_rules: BuildRuleCatalogDocument
    build_categories: BuildCategoryDocument
    build_options: list[BuildOptionDocument]
    ships: ShipSeedDocument


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Master-data file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Master-data JSON is invalid at line {exc.lineno}, column {exc.colno}: {path}"
        ) from exc


def _validate(model, path: Path):
    try:
        return model.model_validate(_read_json(path))
    except ValidationError as exc:
        raise RuntimeError(f"Master-data catalog failed validation ({path}):\n{exc}") from exc


def _single(documents: list[object], kind: str):
    if len(documents) != 1:
        raise RuntimeError(f"Master-data manifest must contain exactly one {kind} document")
    return documents[0]


@lru_cache(maxsize=1)
def load_master_data_catalog(
    manifest_path: Path = MASTER_DATA_MANIFEST_PATH,
) -> MasterDataCatalog:
    manifest = _validate(CatalogManifest, manifest_path)
    root = manifest_path.parent.resolve()
    referenced_paths = {(root / entry.path).resolve() for entry in manifest.documents}
    discovered_paths = {
        path.resolve()
        for path in root.rglob("*.json")
        if path.resolve() != manifest_path.resolve()
    }
    if referenced_paths != discovered_paths:
        missing = sorted(str(path) for path in referenced_paths - discovered_paths)
        unlisted = sorted(str(path) for path in discovered_paths - referenced_paths)
        raise RuntimeError(
            f"Master-data manifest does not match the JSON tree; missing={missing}, unlisted={unlisted}"
        )

    model_by_kind = {
        "references": ReferenceCatalogDocument,
        "roles": RoleCatalogDocument,
        "fleets": FleetCatalogDocument,
        "build_rules": BuildRuleCatalogDocument,
        "build_categories": BuildCategoryDocument,
        "build_options": BuildOptionDocument,
        "ship_definitions": ShipDefinitionDocument,
        "ships": ShipRateDocument,
    }
    parsed: dict[str, list[object]] = {kind: [] for kind in model_by_kind}
    for entry in manifest.documents:
        path = (root / entry.path).resolve()
        if root not in path.parents:
            raise RuntimeError(f"Master-data path escapes catalog root: {entry.path}")
        parsed[entry.kind].append(_validate(model_by_kind[entry.kind], path))

    definitions = _single(parsed["ship_definitions"], "ship_definitions")
    ship_rates = sorted(parsed["ships"], key=lambda row: row.rate)
    if [row.rate for row in ship_rates] != list(range(1, 8)):
        raise RuntimeError("Master-data catalog must contain exactly one ship file per rate")
    ships = ShipSeedDocument(
        sources=definitions.sources,
        weapon_classes=definitions.weapon_classes,
        weapon_slot_types=definitions.weapon_slot_types,
        ships=[ship for document in ship_rates for ship in document.items],
    )

    option_documents = parsed["build_options"]
    categories = _single(parsed["build_categories"], "build_categories")
    category_keys = {row.key for row in categories.items if row.is_active}
    option_categories = {row.category for row in option_documents}
    if len(option_categories) != len(option_documents):
        raise RuntimeError("Build option categories must each have exactly one document")
    if category_keys != option_categories:
        raise RuntimeError(
            "Build category documents do not match the active category catalog: "
            f"categories={sorted(category_keys)}, options={sorted(option_categories)}"
        )

    return MasterDataCatalog(
        manifest=manifest,
        references=_single(parsed["references"], "references"),
        roles=_single(parsed["roles"], "roles"),
        fleets=_single(parsed["fleets"], "fleets"),
        build_rules=_single(parsed["build_rules"], "build_rules"),
        build_categories=categories,
        build_options=option_documents,
        ships=ships,
    )


def load_ship_seed_document() -> ShipSeedDocument:
    return load_master_data_catalog().ships


def load_ship_rate_document(path: Path) -> ShipRateDocument:
    return _validate(ShipRateDocument, path)


def ship_seed_rows() -> list[dict[str, object]]:
    return [row.model_dump(mode="json") for row in load_ship_seed_document().ships]
