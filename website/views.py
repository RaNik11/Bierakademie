from django.db.models import Prefetch
from django.http import HttpResponseForbidden
from django.shortcuts import render

from .models import (
    MenuCategory,
    MenuGroup,
    MenuItem,
    MenuPrice,
)


# Keep the existing public card until imported data and prices are approved.
# After verification, switch this to True to enable the new public menu.
ENABLE_DYNAMIC_PUBLIC_MENU = False


# ==================================================
# MENU DATA
# ==================================================

def build_menu_sections(include_unpublished=False):
    """
    Builds the menu hierarchy:

    Category
        Group
            Item
                Price variants

    Public visitors receive only published and available
    products.

    Staff preview can include unpublished products and
    unavailable price variants for verification.
    """

    # ----------------------------------------------
    # PRICES
    # ----------------------------------------------

    prices = MenuPrice.objects.order_by(
        "sort_order",
        "id",
    )

    if not include_unpublished:
        prices = prices.filter(is_available=True)

    # ----------------------------------------------
    # ITEMS
    # ----------------------------------------------

    items = (
        MenuItem.objects
        .select_related("brand", "group", "group__category")
        .order_by("sort_order", "id")
    )

    if not include_unpublished:
        items = items.filter(
            is_published=True,
            is_available=True,
        )

    items = items.prefetch_related(
        Prefetch(
            "prices",
            queryset=prices,
            to_attr="menu_prices",
        )
    )

    # ----------------------------------------------
    # GROUPS
    # ----------------------------------------------

    groups = (
        MenuGroup.objects
        .filter(is_visible=True)
        .order_by("sort_order", "id")
        .prefetch_related(
            Prefetch(
                "items",
                queryset=items,
                to_attr="menu_items",
            )
        )
    )

    # ----------------------------------------------
    # CATEGORIES
    # ----------------------------------------------

    categories = (
        MenuCategory.objects
        .filter(is_visible=True)
        .order_by("sort_order", "id")
        .prefetch_related(
            Prefetch(
                "groups",
                queryset=groups,
                to_attr="menu_groups",
            )
        )
    )

    # ----------------------------------------------
    # PREPARE TEMPLATE STRUCTURE
    # ----------------------------------------------

    sections = []

    for category in categories:

        category_groups = []

        for group in category.menu_groups:

            group_items = list(group.menu_items)

            if not group_items:
                continue

            category_groups.append({
                "group": group,
                "items": group_items,
            })

        # Cigars are an informational section.
        # There is no specific printed product list.

        if not category_groups and category.slug != "zigarren":
            continue

        sections.append({
            "category": category,
            "groups": category_groups,
        })

    return sections


def separate_new_items(sections):
    """Show marked items in one top-level section, without duplication.

    Keep the standard category / group order, and drop groups that are now
    empty. Works on the already-prefetched objects, without extra queries.
    """
    new_items = []
    ordinary_sections = []

    for section in sections:
        regular_groups = []
        for entry in section["groups"]:
            regular_items = []
            for item in entry["items"]:
                if item.is_new:
                    new_items.append(item)
                else:
                    regular_items.append(item)
            if regular_items:
                regular_groups.append({"group": entry["group"], "items": regular_items})

        if regular_groups or section["category"].slug == "zigarren":
            ordinary_sections.append({
                "category": section["category"],
                "groups": regular_groups,
            })

    return ordinary_sections, new_items


# ==================================================
# HOME
# ==================================================

def home(request):
    return render(
        request,
        "website/home.html",
    )


# ==================================================
# DRINKS
# ==================================================

def drinks(request):

    # Staff users can preview the full imported catalogue.
    # A normal visitor cannot enable this by adding ?preview=1.

    preview_requested = (
        request.GET.get("preview") == "1"
        or request.resolver_match.url_name == "drinks_preview"
    )

    is_preview = (
        preview_requested
        and request.user.is_authenticated
        and request.user.is_staff
    )

    # The preview may expose draft products and unverified prices.
    # Never serve it to a non-staff visitor, even by direct URL.
    if preview_requested and not is_preview:
        return HttpResponseForbidden("Die interne Menü-Vorschau ist nur für Mitarbeiter verfügbar.")

    menu_sections = build_menu_sections(
        include_unpublished=is_preview
    )

    item_count = sum(
        len(group_data["items"])
        for section in menu_sections
        for group_data in section["groups"]
    )

    new_items = []
    if is_preview or ENABLE_DYNAMIC_PUBLIC_MENU:
        menu_sections, new_items = separate_new_items(menu_sections)

    context = {
        "menu_sections": menu_sections,
        "new_items": new_items,
        "menu_preview": is_preview,
        "menu_item_count": item_count,
    }

    template_name = (
        "website/drinks_preview.html"
        if is_preview or ENABLE_DYNAMIC_PUBLIC_MENU
        else "website/drinks.html"
    )

    return render(
        request,
        template_name,
        context,
    )


# ==================================================
# ABOUT
# ==================================================

def about(request):
    return render(
        request,
        "website/about.html",
    )


# ==================================================
# GALLERY
# ==================================================

def gallery(request):
    return render(
        request,
        "website/gallery.html",
    )


# ==================================================
# CONTACT
# ==================================================

def contact(request):
    return render(
        request,
        "website/contact.html",
    )

# ==================================================
# IMPRESSUM
# ==================================================

def impressum(request):
    return render(
        request,
        "website/impressum.html",
    )

# ==================================================
# DATENSCHUTZ
# ==================================================

def datenschutz(request):
    return render(
        request,
        "website/datenschutz.html",
    )
