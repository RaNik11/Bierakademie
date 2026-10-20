
"""
Bierakademie — Initial menu structure.

Creates the menu categories and groups based on the
printed menu of Bierakademie in der Apothek.

Safe to run repeatedly: existing entries are not overwritten.
Products and prices are imported separately.
"""

from django.db import transaction

from .models import MenuCategory, MenuGroup


# ==================================================
# MENU STRUCTURE
# ==================================================

MENU_STRUCTURE = (

    # --------------------------------------------------
    # 01 — BIER
    # --------------------------------------------------

    (
        "bier",
        "Bier",
        "UNSER HERZSTÜCK",
        (
            (
                "Bier vom Fass",
                "Frisch gezapft",
                MenuGroup.Theme.GREEN,
            ),
            (
                "Helle Biere aus der Flasche",
                "Klassiker",
                MenuGroup.Theme.LIGHT,
            ),
            (
                "Hefe und Naturtrüb",
                "Naturtrüb",
                MenuGroup.Theme.LIGHT,
            ),
            (
                "Flaschenbiere Kristall",
                "Klar & frisch",
                MenuGroup.Theme.LIGHT,
            ),
            (
                "Flaschenbiere",
                "Große Auswahl",
                MenuGroup.Theme.BOTTLES,
            ),
            (
                "Flaschenbiere Dunkel",
                "Malzig",
                MenuGroup.Theme.LIGHT,
            ),
            (
                "Spezielle Biere Hilzenbecks",
                "Besondere Spezialitäten",
                MenuGroup.Theme.RED,
            ),
            (
                "Holzfassgereifter Bock",
                "Limitierte Spezialität",
                MenuGroup.Theme.RED,
            ),
            (
                "Starkbiere aus der Flasche",
                "Kräftig & charaktervoll",
                MenuGroup.Theme.RED,
            ),
            (
                "Alkoholfreie Flaschenbiere",
                "Ohne Alkohol",
                MenuGroup.Theme.LIGHT,
            ),
        ),
    ),

    # --------------------------------------------------
    # 02 — SPIRITUOSEN
    # --------------------------------------------------

    (
        "spirituosen",
        "Spirituosen",
        "KLASSIKER & SPEZIALITÄTEN",
        (
            (
                "Spirituosen",
                "Schnaps",
                MenuGroup.Theme.GREEN,
            ),
            (
                "Liköre",
                "Süß & aromatisch",
                MenuGroup.Theme.LIGHT,
            ),
            (
                "Kräuterschnäpse",
                "Kräuter & Bitter",
                MenuGroup.Theme.LIGHT,
            ),
            (
                "Whiskey",
                "Amerika, Irland & Deutschland",
                MenuGroup.Theme.RED,
            ),
            (
                "Scotch Whisky",
                "Schottische Whiskys",
                MenuGroup.Theme.RED,
            ),
            (
                "Rum",
                "Internationale Rumsorten",
                MenuGroup.Theme.GREEN,
            ),
            (
                "Weinbrand & Cognac",
                "Edle Brände",
                MenuGroup.Theme.LIGHT,
            ),
        ),
    ),

    # --------------------------------------------------
    # 03 — ALKOHOLFREI
    # --------------------------------------------------

    (
        "alkoholfrei",
        "Alkoholfrei",
        "ERFRISCHUNG & VIELFALT",
        (
            (
                "Alkoholfreie Getränke",
                "Softdrinks & Wasser",
                MenuGroup.Theme.GREEN,
            ),
            (
                "Säfte & Saftschorlen",
                "Fruchtig",
                MenuGroup.Theme.LIGHT,
            ),
            (
                "Alkoholfreie Schnäpse",
                "Ohne Alkohol",
                MenuGroup.Theme.LIGHT,
            ),
            (
                "Alkoholfreie Cocktails",
                "Kurz & Lang",
                MenuGroup.Theme.RED,
            ),
        ),
    ),

    # --------------------------------------------------
    # 04 — WEIN & SEKT
    # --------------------------------------------------

    (
        "wein",
        "Wein & Sekt",
        "WEIN & PRICKELNDES",
        (
            (
                "Weine & Weinschorle",
                "Unsere Weinauswahl",
                MenuGroup.Theme.GREEN,
            ),
            (
                "Aperitifs & Weincocktails",
                "Zum Genießen",
                MenuGroup.Theme.LIGHT,
            ),
            (
                "Sekt",
                "Prickelnd",
                MenuGroup.Theme.LIGHT,
            ),
            (
                "Flaschen Champagner / Sekt",
                "Besondere Momente",
                MenuGroup.Theme.RED,
            ),
            (
                "Alkoholfreie Weine & Weinschorle",
                "Alkoholfrei genießen",
                MenuGroup.Theme.LIGHT,
            ),
        ),
    ),

    # --------------------------------------------------
    # 05 — KAFFEE & TEE
    # --------------------------------------------------

    (
        "kaffee",
        "Kaffee & Tee",
        "WARM & GEMÜTLICH",
        (
            (
                "Teebeutel & loser Tee",
                "Teeauswahl",
                MenuGroup.Theme.GREEN,
            ),
            (
                "Kaffee",
                "Kaffeeklassiker",
                MenuGroup.Theme.LIGHT,
            ),
        ),
    ),

    # --------------------------------------------------
    # 06 — ESSEN
    # --------------------------------------------------

    (
        "essen",
        "Essen",
        "KALTE KÜCHE",
        (
            (
                "Kalte Speisen",
                "Nach Tagesangebot",
                MenuGroup.Theme.GREEN,
            ),
        ),
    ),

    # --------------------------------------------------
    # 07 — ZIGARREN
    # --------------------------------------------------

    (
        "zigarren",
        "Zigarren",
        "AUS UNSEREM HUMIDOR",
        (
            (
                "Zigarren & Zigarillos",
                "Auswahl vor Ort",
                MenuGroup.Theme.RED,
            ),
        ),
    ),
)


# ==================================================
# DATABASE INITIALIZATION
# ==================================================

@transaction.atomic
def create_menu_structure():

    created_categories = 0
    created_groups = 0

    for category_order, data in enumerate(
        MENU_STRUCTURE,
        start=1,
    ):

        slug, name, subtitle, groups = data

        category, category_created = (
            MenuCategory.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "subtitle": subtitle,
                    "sort_order": category_order,
                    "is_visible": True,
                },
            )
        )

        if category_created:
            created_categories += 1

        print(f"\n{category_order:02d} — {category.name}")

        for group_order, group_data in enumerate(
            groups,
            start=1,
        ):

            group_name, eyebrow, theme = group_data

            group, group_created = (
                MenuGroup.objects.get_or_create(
                    category=category,
                    name=group_name,
                    defaults={
                        "eyebrow": eyebrow,
                        "theme": theme,
                        "sort_order": group_order,
                        "is_visible": True,
                    },
                )
            )

            if group_created:
                created_groups += 1
                status = "+"
            else:
                status = "="

            print(
                f"  {status} {group_order:02d}. {group.name}"
            )

    print("\n" + "=" * 48)

    print("BIERAKADEMIE — MENÜSTRUKTUR")

    print(
        f"Neue Kategorien: {created_categories}"
    )

    print(
        f"Neue Gruppen:    {created_groups}"
    )

    print(
        f"Kategorien gesamt: {MenuCategory.objects.count()}"
    )

    print(
        f"Gruppen gesamt:    {MenuGroup.objects.count()}"
    )

    print("=" * 48)

    print(
        "\nFertig! Die Menüstruktur ist in der "
        "Datenbank gespeichert."
    )


# ==================================================
# END
# ==================================================
