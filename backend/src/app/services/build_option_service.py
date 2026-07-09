from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import BuildItemCategory, BuildItemOption
from app.schemas import BuildItemCategoryRead, BuildItemOptionRead, BuildOptionsCatalog
from app.services.build_stat_service import stat_definitions_for_api


def list_build_options(db: Session) -> BuildOptionsCatalog:
    categories = list(
        db.scalars(
            select(BuildItemCategory)
            .where(BuildItemCategory.is_active.is_(True))
            .order_by(BuildItemCategory.sort_order, BuildItemCategory.label)
        ).all()
    )
    options = list(
        db.scalars(
            select(BuildItemOption)
            .options(selectinload(BuildItemOption.effects))
            .join(BuildItemOption.category)
            .where(BuildItemOption.is_active.is_(True), BuildItemCategory.is_active.is_(True))
            .order_by(BuildItemCategory.sort_order, func.lower(BuildItemOption.name))
        ).unique().all()
    )

    grouped: dict[str, list[BuildItemOptionRead]] = {category.key: [] for category in categories}
    for option in options:
        grouped.setdefault(option.category.key, []).append(
            BuildItemOptionRead(
                id=option.id,
                category_key=option.category.key,
                name=option.name,
                source=option.source,
                notes=option.notes,
                option_kind=option.option_kind,
                allowed_slot_types=option.allowed_slots,
                weapon_caliber_inches=option.weapon_caliber_inches,
                stat_effects=option.stat_effects,
                sort_order=option.sort_order,
                created_at=option.created_at,
                updated_at=option.updated_at,
            )
        )

    return BuildOptionsCatalog(
        categories=[BuildItemCategoryRead.model_validate(category) for category in categories],
        options=grouped,
        stat_definitions=stat_definitions_for_api(),
    )
