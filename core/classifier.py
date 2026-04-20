from typing import List, Tuple, Optional
from config import ItemCategory, SecondaryTag, CATEGORY_NAMES, TAG_NAMES, CATEGORY_EXAMPLES


def classify_item(
    category: str,
    secondary_tags: List[str] = None,
    user_description: str = None,
) -> Tuple[ItemCategory, List[SecondaryTag]]:
    cat = ItemCategory(category) if category in [c.value for c in ItemCategory] else ItemCategory.BOX_PANEL
    tags = []
    if secondary_tags:
        for tag in secondary_tags:
            if tag in [t.value for t in SecondaryTag]:
                tags.append(SecondaryTag(tag))
    return cat, tags


def get_category_description(category: ItemCategory) -> str:
    examples = CATEGORY_EXAMPLES.get(category, "")
    name = CATEGORY_NAMES.get(category, "")
    return f"{name}: {examples}"


def get_tag_description(tag: SecondaryTag) -> str:
    return TAG_NAMES.get(tag, tag.value)


def get_all_categories() -> List[Tuple[ItemCategory, str]]:
    return [(cat, CATEGORY_NAMES[cat]) for cat in ItemCategory]


def get_all_tags() -> List[Tuple[SecondaryTag, str]]:
    return [(tag, TAG_NAMES[tag]) for tag in SecondaryTag]


def get_tags_for_category(category: ItemCategory) -> List[SecondaryTag]:
    return list(SecondaryTag)