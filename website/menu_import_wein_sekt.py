"""Import Wein & Sekt from the printed Bierakademie menu (IMG_2795–2796).

Printed prices and descriptions are preliminary and must be confirmed.
Existing menu items and price variants are never overwritten.
All new items remain unpublished pending review.
"""

from decimal import Decimal

from django.db import transaction

from .models import Brand, MenuCategory, MenuGroup, MenuItem, MenuPrice


# Row layout:
# (brand or None, product name, printed origin, alcohol % or None,
#  printed note, ((serving size, EUR), ...), allergen code or "")
# Missing percentage / allergen code means "not specified on printed page".

WEIN_SEKT_DATA = {
    "Weine & Weinschorle": [
        (
            "Schloss Affaltrach", "Schwäbischer Landwein", "Obersulm", "11",
            "Trocken.", (("0,25 l", "5.00"),), "14",
        ),
        (
            None, "Gr. Merlot Rotwein Agioritiko", "Alepohori, Griechenland", "12.5",
            "Trocken. Schreibweise wie in der Druckkarte.",
            (("0,25 l", "5.00"),), "14",
        ),
        (
            "Apelia", "Rotwein", "Oreokastro, Griechenland", "11",
            "Lieblich, vollmundig.", (("0,25 l", "5.00"),), "14",
        ),
        (
            None, "Mavrodaphne Likörwein", "Chalkidiki, Griechenland", "15",
            "Lieblich; laut Druckkarte mit lorbeer-würzigem Aroma. "
            "Die Herkunftsangabe bitte später prüfen.",
            (("0,25 l", "5.70"),), "",
        ),
        (
            "Schloss Affaltrach", "Rosé-Schillerwein", "Obersulm, Deutschland", "12",
            "Trocken. Druckkarte: Rose- Schillerwein.",
            (("0,25 l", "5.00"),), "14",
        ),
        (
            None, "Riesling Weißwein", "Heilbronn-Staufenberg", "12",
            "Trocken.", (("0,25 l", "5.00"),), "14",
        ),
        (
            "Malamatina", "Retsina", "Griechenland", "11",
            "Harziger Weißwein. Druckkarte enthält außerdem eine "
            "nicht zur Veröffentlichung geeignete Gesundheitsbehauptung.",
            (("0,25 l", "5.00"), ("0,50 l", "7.00")), "14",
        ),
        (
            None, "Weinschorle Weiß / Rot / Rosé", "", None,
            "Drei Sorten zur Auswahl, gleicher Preis laut Druckkarte.",
            (("0,25 l", "4.00"),), "14",
        ),
        (
            None, "Mavrodaphne Schorle", "", None,
            "Mischgetränk auf Basis von Mavrodaphne.",
            (("0,25 l", "4.50"),), "14",
        ),
    ],

    "Aperitifs & Weincocktails": [
        (
            None, "Aperol Spritz mit Sekt Yescovino", "", None,
            "Mit Sekt Yescovino laut Druckkarte.",
            (("0,25 l", "6.50"),), "14",
        ),
        (
            None, "Hugo", "", None, "",
            (("0,25 l", "6.50"),), "14",
        ),
        (
            None, "Korea", "", None,
            "Hausgetränk laut Druckkarte; Zusammensetzung noch klären.",
            (("0,25 l", "4.50"),), "14",
        ),
        (
            None, "Glühwein", "", None,
            "Das ganze Jahr erhältlich, selbstgemacht aus Weinen "
            "(laut Druckkarte).",
            (("0,2 l", "4.30"),), "14",
        ),
    ],

    "Sekt": [
        (
            "Yescovino", "Sekt", "Italien", "10",
            "Halbtrocken.", (("0,25 l", "5.50"),), "14",
        ),
        (
            None, "Sektschorle Yescovino", "Italien", None,
            "Mit Sekt Yescovino.", (("0,25 l", "4.50"),), "14",
        ),
        (
            "Yescovino", "Prosecco", "Italien", None,
            "Halbtrocken laut Druckkarte.",
            (("0,25 l", "5.50"),), "14",
        ),
        (
            None, "Proseccoschorle", "Italien", None,
            "Mit Prosecco.", (("0,25 l", "4.50"),), "14",
        ),
    ],

    "Flaschen Champagner / Sekt": [
        (
            "Fürst Metternich", "Sekt", "Wiesbaden", "12",
            "Auch als 0,2-l-Portion erhältlich.",
            (("0,75 l", "35.00"), ("0,2 l", "6.00")), "",
        ),
        (
            "Etienne Dumont", "Champagner Brut", "Frankreich", "12",
            "Druckkarte: Champagner Etienne Dumont Brut.",
            (("0,75 l", "55.00"),), "",
        ),
    ],

    "Alkoholfreie Weine & Weinschorle": [
        (
            "Carl Jung", "Merlot Rotwein (vegan, alkoholfrei)", "Rüdesheim", "0",
            "Rotwein, vegan laut Druckkarte.",
            (("0,25 l", "5.50"),), "",
        ),
        (
            None, "Schorle Merlot Carl Jung", "Rüdesheim", "0",
            "Alkoholfreie Weinschorle mit Carl Jung Merlot.",
            (("0,25 l", "4.50"),), "",
        ),
        (
            None, "Sekt Sparkling Rosé (alkoholfrei)", "Esslingen", "0",
            "Hersteller in Druckkarte nicht eindeutig angegeben.",
            (("0,25 l", "6.00"),), "",
        ),
        (
            None, "Sekt Schorle Sparkling Rosé", "Esslingen", "0",
            "Alkoholfreie Sektschorle.",
            (("0,25 l", "4.50"),), "",
        ),
    ],
}


EXPECTED_GROUP_COUNTS = {
    "Weine & Weinschorle": 9,
    "Aperitifs & Weincocktails": 4,
    "Sekt": 4,
    "Flaschen Champagner / Sekt": 2,
    "Alkoholfreie Weine & Weinschorle": 4,
}


def validate_wein_sekt_data():
    if set(WEIN_SEKT_DATA) != set(EXPECTED_GROUP_COUNTS):
        raise ValueError(
            "Die erwarteten Wein/Sekt-Gruppen stimmen nicht überein."
        )

    seen = set()
    total_prices = 0

    for group_name, expected_count in EXPECTED_GROUP_COUNTS.items():
        entries = WEIN_SEKT_DATA[group_name]

        if len(entries) != expected_count:
            raise ValueError(
                f"{group_name}: {expected_count} Einträge erwartet."
            )

        for brand, name, origin, alcohol, note, prices, allergen_codes in entries:
            identity = (group_name, brand, name)

            if identity in seen:
                raise ValueError(f"Doppelte Position: {identity}")

            seen.add(identity)

            if not name.strip() or not prices:
                raise ValueError(f"Name oder Preis fehlt: {identity}")

            if alcohol is not None:
                strength = Decimal(alcohol)

                if not Decimal("0") <= strength <= Decimal("100"):
                    raise ValueError(
                        f"Ungültiger Alkoholgehalt: {identity}"
                    )

            sizes = set()

            for size, amount in prices:
                if (
                    size in sizes
                    or not size.strip()
                    or Decimal(amount) <= 0
                ):
                    raise ValueError(
                        f"Ungültige Preisvariante: {identity} / {size}"
                    )

                sizes.add(size)
                total_prices += 1

    if len(seen) != 23 or total_prices != 25:
        raise ValueError(
            "Erwartet: 23 Positionen und 25 Preisvarianten."
        )


@transaction.atomic
def import_wein_sekt_menu():
    validate_wein_sekt_data()

    category = MenuCategory.objects.get(slug="wein")

    if not category.notice:
        category.notice = (
            "Unsere Weine sind laut Druckkarte auch als Weinschorle erhältlich. "
            "Die Druckkarte enthält außerdem einen allgemeinen Hinweis zu "
            "Farbstoff Zuckerkulör; eine Zuordnung zu bestimmten Artikeln fehlt."
        )

        category.save(update_fields=["notice"])

    counts = {
        "brands": 0,
        "items": 0,
        "existing_items": 0,
        "prices": 0,
        "existing_prices": 0,
    }

    for group_name, entries in WEIN_SEKT_DATA.items():
        group = MenuGroup.objects.get(
            category=category,
            name=group_name,
        )

        print(f"\n{group_name}: {len(entries)} Positionen")

        for order, entry in enumerate(entries, start=1):
            (
                brand_name,
                name,
                origin,
                alcohol,
                note,
                prices,
                allergen_codes,
            ) = entry

            brand = None

            if brand_name:
                brand, created_brand = Brand.objects.get_or_create(
                    name=brand_name
                )

                counts["brands"] += int(created_brand)

            item, created_item = MenuItem.objects.get_or_create(
                group=group,
                brand=brand,
                name=name,
                defaults={
                    "production_location": origin,
                    "alcohol_percent": (
                        Decimal(alcohol)
                        if alcohol is not None
                        else None
                    ),
                    "printed_note": note,
                    "allergen_codes": allergen_codes,
                    "sort_order": order,
                    "is_available": True,
                    "is_published": False,
                },
            )

            counts[
                "items" if created_item else "existing_items"
            ] += 1

            for price_order, (size, amount) in enumerate(
                prices,
                start=1,
            ):
                _, created_price = MenuPrice.objects.get_or_create(
                    item=item,
                    size_label=size,
                    defaults={
                        "price_eur": Decimal(amount),
                        "sort_order": price_order,
                        "is_available": True,
                    },
                )

                counts[
                    "prices" if created_price else "existing_prices"
                ] += 1

            full_name = (
                f"{brand_name} — {name}"
                if brand_name
                else name
            )

            formatted_prices = ", ".join(
                f"{size}: {Decimal(amount):.2f} €"
                for size, amount in prices
            )

            print(
                f"  {'+' if created_item else '='} "
                f"{full_name} | {formatted_prices}"
            )

    print("\n" + "=" * 50)
    print("BIERAKADEMIE — WEIN & SEKT IMPORT")

    print(f"Neue Marken:             {counts['brands']}")
    print(f"Neue Positionen:         {counts['items']}")
    print(f"Bereits vorhanden:       {counts['existing_items']}")
    print(f"Neue Preisvarianten:     {counts['prices']}")
    print(f"Vorhandene Preise:       {counts['existing_prices']}")

    print("Positionen in Druckkarte: 23")
    print("Preisvarianten:           25")

    print("=" * 50)

    print("Bestehende Preise bleiben unverändert.")
    print("Neue Positionen bleiben vorerst unveröffentlicht.")
    print("Alkoholgehalte und Allergene bei Leerfeldern noch prüfen.")