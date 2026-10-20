"""
Bierakademie — Import Kaffee & Tee.

Quelle: gedruckte Getränkekarte, Seite Heißgetränke.

8 Teepositionen
2 Kaffeepositionen
10 Preisvarianten

Mengen sind in der Druckkarte nicht angegeben.
Bestehende Produkte und Preise werden nicht überschrieben.
Neue Produkte bleiben bis zur Prüfung unveröffentlicht.
"""

from decimal import Decimal

from django.db import transaction

from .models import MenuCategory, MenuGroup, MenuItem, MenuPrice


# ==================================================
# DATEN
# ==================================================
#
# (
#     Produktname,
#     Beschreibung aus der Papierkarte,
#     Preis in EUR,
# )
#
# Keine erfundenen Hersteller, Füllmengen oder
# Alkoholgehalte.
# ==================================================


KAFFEE_TEE_DATA = {

    "Teebeutel & loser Tee": [

        (
            "Sunshine Tee",
            "Loser Tee aus verschiedenen Sommerfrüchten "
            "vom Teehaus Weirich.",
            "4.50",
        ),

        (
            "Kamillentee",
            "Teebeutel.",
            "3.00",
        ),

        (
            "Pfefferminztee",
            "Teebeutel.",
            "3.00",
        ),

        (
            "Grüner Tee",
            "Teebeutel.",
            "3.00",
        ),

        (
            "Hagebuttentee",
            "Teebeutel.",
            "3.00",
        ),

        (
            "Schwarztee",
            "Teebeutel.",
            "3.00",
        ),

        (
            "Früchtetee",
            "Teebeutel.",
            "3.00",
        ),

        (
            "Minze-Ingwer Tee",
            "Teebeutel.",
            "3.00",
        ),
    ],

    "Kaffee": [

        (
            "Tasse Kaffee",
            "",
            "3.50",
        ),

        (
            "Espresso",
            "",
            "3.50",
        ),
    ],
}


# ==================================================
# VALIDIERUNG
# ==================================================


EXPECTED_COUNTS = {
    "Teebeutel & loser Tee": 8,
    "Kaffee": 2,
}


def validate_kaffee_tee_data():

    if set(KAFFEE_TEE_DATA) != set(EXPECTED_COUNTS):
        raise ValueError(
            "Die erwarteten Menügruppen stimmen nicht überein."
        )

    seen = set()
    price_count = 0

    for group_name, expected in EXPECTED_COUNTS.items():

        products = KAFFEE_TEE_DATA[group_name]

        if len(products) != expected:
            raise ValueError(
                f"{group_name}: {expected} Positionen erwartet, "
                f"{len(products)} gefunden."
            )

        for name, description, amount in products:

            identity = (group_name, name)

            if identity in seen:
                raise ValueError(
                    f"Doppelte Position: {identity}"
                )

            seen.add(identity)

            if not name.strip():
                raise ValueError(
                    f"Produktname fehlt: {identity}"
                )

            if Decimal(amount) <= 0:
                raise ValueError(
                    f"Ungültiger Preis: {identity}"
                )

            price_count += 1

    if len(seen) != 10 or price_count != 10:
        raise ValueError(
            "Erwartet: 10 Positionen und 10 Preisvarianten."
        )


# ==================================================
# IMPORT
# ==================================================


@transaction.atomic
def import_kaffee_tee_menu():

    validate_kaffee_tee_data()

    category = MenuCategory.objects.get(
        slug="kaffee"
    )

    new_items = 0
    existing_items = 0

    new_prices = 0
    existing_prices = 0

    for group_name, products in KAFFEE_TEE_DATA.items():

        group = MenuGroup.objects.get(
            category=category,
            name=group_name,
        )

        print(
            f"\n{group_name}: {len(products)} Positionen"
        )

        for order, (
            name,
            description,
            amount,
        ) in enumerate(products, start=1):

            # --------------------------------------
            # PRODUCT
            # --------------------------------------

            item, created_item = MenuItem.objects.get_or_create(
                group=group,
                brand=None,
                name=name,
                defaults={
                    "production_location": "",
                    "alcohol_percent": None,
                    "printed_note": description,
                    "sort_order": order,
                    "is_available": True,
                    "is_published": False,
                },
            )

            if created_item:
                new_items += 1
                marker = "+"
            else:
                existing_items += 1
                marker = "="

            # --------------------------------------
            # PRICE
            # --------------------------------------

            # "Standard" is a database label only.
            # No volume was printed in the source menu.

            _, created_price = MenuPrice.objects.get_or_create(
                item=item,
                size_label="Standard",
                defaults={
                    "price_eur": Decimal(amount),
                    "sort_order": 1,
                    "is_available": True,
                },
            )

            if created_price:
                new_prices += 1
            else:
                existing_prices += 1

            print(
                f"  {marker} {name} | {amount} €"
            )

    # ==================================================
    # RESULT
    # ==================================================

    print("\n" + "=" * 50)
    print("BIERAKADEMIE — KAFFEE & TEE IMPORT")
    print("=" * 50)

    print(f"Neue Positionen:        {new_items}")
    print(f"Vorhandene Positionen:  {existing_items}")
    print(f"Neue Preisvarianten:    {new_prices}")
    print(f"Vorhandene Preise:      {existing_prices}")

    print("-" * 50)

    print("Teepositionen laut Karte:    8")
    print("Kaffeepositionen laut Karte: 2")
    print("Preisvarianten laut Karte:  10")

    print("=" * 50)

    print(
        "\nHinweise:"
        "\n- Keine erfundenen Füllmengen."
        "\n- Keine Hersteller ohne eindeutige Zuordnung."
        "\n- Bestehende Preise bleiben unverändert."
        "\n- Neue Produkte bleiben unveröffentlicht."
    )

    print("\nImport abgeschlossen.")