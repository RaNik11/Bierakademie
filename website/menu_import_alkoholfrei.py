"""
Bierakademie — Import alkoholfreier Getränke.

Quellen:
- IMG_2801: Alkoholfreie Getränke und Säfte
- IMG_2796: Alkoholfreie Schnäpse und Cocktails

Importiert:
- 24 Menüpositionen
- 49 Preisvarianten
- 4 Menügruppen

Bestehende Artikel und Preise werden nicht überschrieben.
Neue Artikel bleiben bis zur Prüfung unveröffentlicht.
"""

from decimal import Decimal

from django.db import transaction

from .models import (
    Brand,
    MenuCategory,
    MenuGroup,
    MenuItem,
    MenuPrice,
)


# ==================================================
# DATENFORMAT
# ==================================================
#
# (
#     Hersteller oder None,
#     Produktname,
#     Herkunft laut Druckkarte,
#     Alkoholgehalt oder None,
#     Beschreibung aus der Druckkarte,
#     Zusatzstoffcodes,
#     ((Menge, Preis), ...)
# )
#
# None bei Alkoholgehalt bedeutet:
# Die Druckkarte nennt keinen konkreten Wert.
#
# "Kurz" und "Lang" werden NICHT in Liter umgerechnet.
# ==================================================


ALKOHOLFREI_DATA = {

    # ==================================================
    # 01 — ALKOHOLFREIE GETRÄNKE
    # 10 Positionen / 22 Preisvarianten
    # ==================================================

    "Alkoholfreie Getränke": [

        (
            "Coca-Cola",
            "Original",
            "Berlin",
            None,
            "Coca Cola laut Druckkarte.",
            "1,3",
            (
                ("0,2 l", "2.80"),
                ("0,4 l", "3.70"),
            ),
        ),

        (
            "Fanta",
            "Fanta",
            "Berlin",
            None,
            "",
            "1",
            (
                ("0,2 l", "2.80"),
                ("0,4 l", "3.70"),
            ),
        ),

        (
            "Coca-Cola",
            "Zero",
            "Berlin",
            None,
            "Coca Cola Zero laut Druckkarte.",
            "1,3,9",
            (
                ("0,2 l", "2.80"),
                ("0,4 l", "3.70"),
            ),
        ),

        (
            None,
            "Spezi",
            "Berlin",
            None,
            "Mischgetränk aus Cola und Fanta.",
            "1,3",
            (
                ("0,2 l", "2.80"),
                ("0,4 l", "3.70"),
            ),
        ),

        (
            "effect",
            "Energy Drink",
            "Paderborn",
            None,
            "Energy Drink effect.",
            "1,3",
            (
                ("0,2 l", "3.50"),
                ("0,4 l", "4.50"),
            ),
        ),

        (
            "Schweppes",
            "Bitter Lemon",
            "Kreuztal",
            None,
            "",
            "2,5",
            (
                ("0,2 l", "3.00"),
                ("0,4 l", "4.00"),
            ),
        ),

        (
            "Schweppes",
            "Tonic Water",
            "Kreuztal",
            None,
            "",
            "2,5",
            (
                ("0,2 l", "3.00"),
                ("0,4 l", "4.00"),
            ),
        ),

        (
            "Silber Brunnen",
            "Zitronenlimonade",
            "Reutlingen",
            None,
            "Herstellerbezeichnung laut Druckkarte.",
            "1",
            (
                ("0,2 l", "2.50"),
                ("0,4 l", "3.20"),
            ),
        ),

        (
            None,
            "Sprudelwasser filtriert",
            "Bierakademie",
            None,
            "Filtriertes Wasser mit Kohlensäure. "
            "Auch als 1,0-l-Flasche erhältlich.",
            "",
            (
                ("0,2 l", "2.50"),
                ("0,4 l", "3.20"),
                ("1,0 l Flasche", "6.00"),
            ),
        ),

        (
            None,
            "Stilles Wasser filtriert",
            "Bierakademie",
            None,
            "Filtriertes stilles Wasser. "
            "Auch als 1,0-l-Flasche erhältlich.",
            "",
            (
                ("0,2 l", "1.50"),
                ("0,4 l", "2.00"),
                ("1,0 l Flasche", "4.00"),
            ),
        ),
    ],

    # ==================================================
    # 02 — SÄFTE & SAFTSCHORLEN
    # 5 Positionen / 10 Preisvarianten
    # ==================================================

    "Säfte & Saftschorlen": [

        (
            None,
            "Orangensaft",
            "Bad Boll",
            None,
            "100 % Frucht laut Druckkarte.",
            "",
            (
                ("0,2 l", "3.50"),
                ("0,4 l", "5.00"),
            ),
        ),

        (
            None,
            "Apfelsaft",
            "Bad Boll",
            None,
            "100 % Frucht laut Druckkarte.",
            "",
            (
                ("0,2 l", "3.50"),
                ("0,4 l", "5.00"),
            ),
        ),

        (
            None,
            "Johannisbeer-Nektar",
            "Bad Boll",
            None,
            "Fruchtgehalt 33 %; Direktsaft "
            "laut Druckkarte.",
            "",
            (
                ("0,2 l", "3.50"),
                ("0,4 l", "5.00"),
            ),
        ),

        (
            "Kumpf",
            "Kirsch-Nektar",
            "Bad Boll",
            None,
            "Fruchtgehalt 50 %; Direktsaft "
            "laut Druckkarte.",
            "",
            (
                ("0,2 l", "3.50"),
                ("0,4 l", "5.00"),
            ),
        ),

        (
            None,
            "Alle Saftschorlen",
            "",
            None,
            "Alle Säfte sind auch als Saftschorle "
            "erhältlich.",
            "",
            (
                ("0,2 l", "3.00"),
                ("0,4 l", "3.80"),
            ),
        ),
    ],

    # ==================================================
    # 03 — ALKOHOLFREIE SCHNÄPSE
    # 4 Positionen / 8 Preisvarianten
    # ==================================================

    "Alkoholfreie Schnäpse": [

        (
            "Monin",
            "Aperol (alkoholfrei)",
            "Italien",
            "0.0",
            "Druckkarte: Aperol Monin. "
            "Genaue Produktbezeichnung prüfen.",
            "",
            (
                ("2 cl", "3.00"),
                ("4 cl", "5.00"),
            ),
        ),

        (
            "Rabenhorst",
            "Cranberry",
            "Unkel / Rhein",
            "0.0",
            "100 % Fruchtgehalt laut Druckkarte.",
            "",
            (
                ("2 cl", "3.00"),
                ("4 cl", "5.00"),
            ),
        ),

        (
            "Bols",
            "Cranberry",
            "Amsterdam",
            "0.0",
            "Cranberry Bols laut Druckkarte.",
            "",
            (
                ("2 cl", "3.00"),
                ("4 cl", "5.00"),
            ),
        ),

        (
            None,
            "Sangrita Ricante",
            "Mexico",
            "0.0",
            "Produktbezeichnung laut Druckkarte.",
            "",
            (
                ("2 cl", "3.00"),
                ("4 cl", "5.00"),
            ),
        ),
    ],

    # ==================================================
    # 04 — ALKOHOLFREIE COCKTAILS
    # 5 Positionen / 9 Preisvarianten
    # ==================================================

    "Alkoholfreie Cocktails": [

        (
            "Monin",
            "Campari-Cocktail (alkoholfrei)",
            "Italien",
            "0.0",
            "Druckkarte: Campari Monin. "
            "Wahlweise mit Soda, Tonic Water, "
            "Bitter Lemon oder Fanta. "
            "Es handelt sich laut Karte um "
            "eine alkoholfreie Variante.",
            "",
            (
                ("Kurz", "4.00"),
                ("Lang", "6.50"),
            ),
        ),

        (
            "Monin",
            "Aperol Spritz (alkoholfrei)",
            "Italien / Esslingen",
            "0.0",
            "Druckkarte: Aperol Spritz Monin "
            "mit Sekt Sparkling Rosé und Sprudel. "
            "Nur Lang-Preis angegeben.",
            "",
            (
                ("Lang", "6.50"),
            ),
        ),

        (
            "Bols",
            "Cranberry-Cocktail",
            "Amsterdam",
            "0.0",
            "Cranberry Bols mit Kirschnektar "
            "und Sprudel.",
            "",
            (
                ("Kurz", "4.00"),
                ("Lang", "6.50"),
            ),
        ),

        (
            "Benvenuti",
            "Amaretto-Cocktail (alkoholfrei)",
            "Saarbrücken",
            "0.0",
            "Amaretto Benvenuti mit Apfelsaft "
            "und Sprudel.",
            "",
            (
                ("Kurz", "4.00"),
                ("Lang", "6.50"),
            ),
        ),

        (
            None,
            "Grenadine Granatapfel",
            "Erding",
            "0.0",
            "Mit Orangensaft und Soda.",
            "",
            (
                ("Kurz", "4.00"),
                ("Lang", "6.50"),
            ),
        ),
    ],
}


# ==================================================
# VALIDIERUNG
# ==================================================

EXPECTED_COUNTS = {
    "Alkoholfreie Getränke": 10,
    "Säfte & Saftschorlen": 5,
    "Alkoholfreie Schnäpse": 4,
    "Alkoholfreie Cocktails": 5,
}


def validate_alkoholfrei_data():

    if set(ALKOHOLFREI_DATA) != set(EXPECTED_COUNTS):
        raise ValueError(
            "Die erwarteten Menügruppen stimmen "
            "nicht überein."
        )

    seen = set()
    price_count = 0

    for group_name, expected in EXPECTED_COUNTS.items():

        products = ALKOHOLFREI_DATA[group_name]

        if len(products) != expected:
            raise ValueError(
                f"{group_name}: {expected} Positionen "
                f"erwartet, {len(products)} gefunden."
            )

        for row in products:

            (
                brand,
                name,
                location,
                alcohol,
                note,
                additive_codes,
                prices,
            ) = row

            identity = (
                group_name,
                brand,
                name,
            )

            if identity in seen:
                raise ValueError(
                    f"Doppelte Position: {identity}"
                )

            seen.add(identity)

            if not name.strip() or not prices:
                raise ValueError(
                    f"Name oder Preise fehlen: {identity}"
                )

            if alcohol is not None:

                strength = Decimal(alcohol)

                if not Decimal("0") <= strength <= Decimal("100"):
                    raise ValueError(
                        f"Ungültiger Alkoholgehalt: {identity}"
                    )

            sizes = set()

            for size, amount in prices:

                if size in sizes:
                    raise ValueError(
                        f"Doppelte Größe: {identity} / {size}"
                    )

                if not size.strip() or Decimal(amount) <= 0:
                    raise ValueError(
                        f"Ungültiger Preis: {identity}"
                    )

                sizes.add(size)
                price_count += 1

    if len(seen) != 24:
        raise ValueError(
            f"24 Positionen erwartet, {len(seen)} gefunden."
        )

    if price_count != 49:
        raise ValueError(
            f"49 Preisvarianten erwartet, "
            f"{price_count} gefunden."
        )


# ==================================================
# DATENBANKIMPORT
# ==================================================

@transaction.atomic
def import_alkoholfrei_menu():

    validate_alkoholfrei_data()

    category = MenuCategory.objects.get(
        slug="alkoholfrei"
    )

    # Allgemeiner Hinweis aus der Druckkarte.
    # Keine automatische Zuordnung zu einzelnen Produkten.

    if not category.notice:

        category.notice = (
            "Die gedruckte Karte enthält den allgemeinen "
            "Hinweis 'enthält Farbstoff: Zuckerkulör'. "
            "Die genaue Zuordnung zu einzelnen Produkten "
            "muss geprüft werden."
        )

        category.save(
            update_fields=["notice"]
        )

    counts = {
        "brands": 0,
        "items": 0,
        "existing_items": 0,
        "prices": 0,
        "existing_prices": 0,
    }

    for group_name, products in ALKOHOLFREI_DATA.items():

        group = MenuGroup.objects.get(
            category=category,
            name=group_name,
        )

        print(
            f"\n{group_name}: {len(products)} Positionen"
        )

        for order, row in enumerate(
            products,
            start=1,
        ):

            (
                brand_name,
                name,
                location,
                alcohol,
                note,
                additive_codes,
                prices,
            ) = row

            brand = None

            # --------------------------------------
            # HERSTELLER
            # --------------------------------------

            if brand_name:

                brand, created_brand = (
                    Brand.objects.get_or_create(
                        name=brand_name
                    )
                )

                counts["brands"] += int(created_brand)

            # --------------------------------------
            # MENÜPOSITION
            # --------------------------------------

            item, created_item = (
                MenuItem.objects.get_or_create(
                    group=group,
                    brand=brand,
                    name=name,
                    defaults={
                        "production_location": location,
                        "alcohol_percent": (
                            Decimal(alcohol)
                            if alcohol is not None
                            else None
                        ),
                        "printed_note": note,
                        "additive_codes": additive_codes,
                        "sort_order": order,
                        "is_available": True,
                        "is_published": False,
                    },
                )
            )

            if created_item:
                counts["items"] += 1
                marker = "+"
            else:
                counts["existing_items"] += 1
                marker = "="

            # --------------------------------------
            # PREISVARIANTEN
            # --------------------------------------

            for price_order, (
                size,
                amount,
            ) in enumerate(
                prices,
                start=1,
            ):

                price, created_price = (
                    MenuPrice.objects.get_or_create(
                        item=item,
                        size_label=size,
                        defaults={
                            "price_eur": Decimal(amount),
                            "sort_order": price_order,
                            "is_available": True,
                        },
                    )
                )

                if created_price:
                    counts["prices"] += 1
                else:
                    counts["existing_prices"] += 1

            # --------------------------------------
            # TERMINALAUSGABE
            # --------------------------------------

            display_name = (
                f"{brand_name} — {name}"
                if brand_name
                else name
            )

            display_prices = ", ".join(
                f"{size}: {amount} €"
                for size, amount in prices
            )

            print(
                f"  {marker} {display_name} "
                f"| {display_prices}"
            )

    # ==================================================
    # ERGEBNIS
    # ==================================================

    print("\n" + "=" * 54)
    print("BIERAKADEMIE — ALKOHOLFREI IMPORT")
    print("=" * 54)

    print(
        f"Neue Marken:              {counts['brands']}"
    )

    print(
        f"Neue Positionen:          {counts['items']}"
    )

    print(
        f"Bereits vorhandene:       {counts['existing_items']}"
    )

    print(
        f"Neue Preisvarianten:      {counts['prices']}"
    )

    print(
        f"Vorhandene Preise:        {counts['existing_prices']}"
    )

    print("-" * 54)

    print(
        "Positionen laut Druckkarte: 24"
    )

    print(
        "Preisvarianten laut Karte: 49"
    )

    print(
        f"Gruppen im Import:         {len(ALKOHOLFREI_DATA)}"
    )

    print("=" * 54)

    print(
        "\nHinweise:"
        "\n- Wasser mit eigener 1,0-l-Flaschenpreisvariante."
        "\n- Alkoholfreier Aperol Spritz nur als Lang."
        "\n- Kurz und Lang ohne erfundene Milliliterangaben."
        "\n- Bestehende Preise wurden nicht verändert."
        "\n- Neue Produkte bleiben unveröffentlicht."
    )

    print(
        "\nImport abgeschlossen."
    )