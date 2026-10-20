
"""Import Rum and Weinbrand/Cognac from the printed Bierakademie menu.

Source: printed drinks menu, IMG_2800.jpeg (October 2026).
Prices, ABV and origins are copied from the printed menu and need
owner confirmation before publication.

Safe to run again: existing products and price variants are preserved.
New products remain unpublished.
"""

from decimal import Decimal

from django.db import transaction

from .models import Brand, MenuCategory, MenuGroup, MenuItem, MenuPrice


# Row format:
# (brand, product, origin on printed menu, ABV, 2 cl EUR, 4 cl EUR, note)
# Some obvious spelling differences are normalized in the database,
# while the original print spelling remains documented in the note.

RUM_COGNAC_DATA = {
    "Rum": [
        (
            "Ron Zacapa", "Solera Gran Reserva", "Guatemala", "40.0",
            "6.50", "11.00", "",
        ),
        (
            "Don Papa", "Small Batch", "Philippinen", "40.0",
            "5.50", "9.00", "Druckkarte: 'Smoll Batch'.",
        ),
        (
            "Matusalem", "Gran Reserva", "Kuba", "40.0",
            "5.50", "9.00",
            "Druckkarte: 'Metusalem Gran Reserva'. Herkunft und genaue "
            "Produktvariante bitte vor Veröffentlichung prüfen.",
        ),
        (
            "Belmont Estate", "Coconut Rum", "Jamaika", "40.0",
            "4.50", "8.00", "",
        ),
        (
            "Legendario", "Elixir", "Kuba", "34.0",
            "5.00", "8.00", "",
        ),
        (
            "Centenario", "Aged 7 Years", "Costa Rica", "40.0",
            "5.50", "9.00", "",
        ),
        (
            "Pampero", "Aniversario Reserva Exclusiva", "Venezuela", "40.0",
            "5.50", "8.00", "",
        ),
        (
            "Havana Club", "7 Years", "Havana", "40.0",
            "5.50", "8.00", "",
        ),
        (
            "Havana Club", "3 Years", "Havana", "40.0",
            "5.00", "7.50", "",
        ),
        (
            "Captain Morgan", "Rum (Sorte prüfen)", "Jamaika", "35.0",
            "4.50", "7.00",
            "Auf der Druckkarte steht nur 'Captain Morgan'. "
            "Genaue Produktvariante vor Veröffentlichung prüfen.",
        ),
        (
            "Bacardi", "White Rum", "Puerto Rico", "37.0",
            "4.00", "7.00",
            "Druckkarte: 'Baccardi White Rum'. "
            "Genaue Produktvariante vor Veröffentlichung prüfen.",
        ),
        (
            "Stroh", "Rum 80", "Österreich", "80.0",
            "5.00", "8.00", "",
        ),
    ],
    "Weinbrand & Cognac": [
        (
            "Metaxa", "Grand Very Old", "Griechenland / Samos", "40.0",
            "6.50", "11.00", "Laut Druckkarte: von Muskattrauben.",
        ),
        (
            "Metaxa", "7 Sterne", "Griechenland / Samos", "40.0",
            "4.50", "7.50", "Laut Druckkarte: Aromenvielfalt.",
        ),
        (
            "Metaxa", "3 Sterne", "Griechenland / Samos", "40.0",
            "4.00", "7.00", "Laut Druckkarte: vollmundig.",
        ),
        (
            "Hennessy", "Very Special", "Frankreich", "40.0",
            "6.50", "11.00", "",
        ),
        (
            "Asbach", "Uralt", "Rüdesheim", "36.0",
            "4.50", "7.50",
            "Laut Druckkarte: gereift in Limousin-Eichenfässern.",
        ),
        (
            "Chantré", "Weinbrand (Sorte prüfen)",
            "Frankreich / Eltville", "36.0", "4.00", "7.00",
            "Druckkarte: 'Chantré', weicher, runder Geschmack. "
            "Die Herkunftsangabe 'Frankreich / Eltville' ist "
            "widersprüchlich und muss geprüft werden.",
        ),
    ],
}


def validate_rum_cognac_data():
    expected_counts = {"Rum": 12, "Weinbrand & Cognac": 6}

    for group_name, expected in expected_counts.items():
        if len(RUM_COGNAC_DATA.get(group_name, [])) != expected:
            raise ValueError(
                f"{group_name}: {expected} Positionen erwartet."
            )

    if set(RUM_COGNAC_DATA) != set(expected_counts):
        raise ValueError("Unbekannte oder fehlende Menügruppe.")

    seen = set()

    for group_name, entries in RUM_COGNAC_DATA.items():
        for brand, name, origin, strength, price_2, price_4, note in entries:
            identity = (group_name, brand, name)

            if identity in seen:
                raise ValueError(f"Doppelte Position: {identity}")

            seen.add(identity)

            if not brand.strip() or not name.strip() or not origin.strip():
                raise ValueError(f"Fehlende Stammdaten: {identity}")

            abv = Decimal(strength)

            if not Decimal("0") <= abv <= Decimal("100"):
                raise ValueError(f"Ungültiger Alkoholgehalt: {identity}")

            if Decimal(price_2) <= 0 or Decimal(price_4) <= 0:
                raise ValueError(f"Ungültiger Preis: {identity}")


@transaction.atomic
def import_rum_cognac_menu():
    validate_rum_cognac_data()

    category = MenuCategory.objects.get(slug="spirituosen")

    counts = {
        "brands": 0,
        "items": 0,
        "prices": 0,
        "existing_items": 0,
        "existing_prices": 0,
    }

    for group_name, entries in RUM_COGNAC_DATA.items():
        group = MenuGroup.objects.get(
            category=category,
            name=group_name,
        )

        print(f"\n{group_name}: {len(entries)} Positionen")

        for order, row in enumerate(entries, start=1):
            brand_name, name, origin, strength, price_2, price_4, note = row

            brand, new_brand = Brand.objects.get_or_create(
                name=brand_name
            )

            counts["brands"] += int(new_brand)

            item, new_item = MenuItem.objects.get_or_create(
                group=group,
                brand=brand,
                name=name,
                defaults={
                    "production_location": origin,
                    "alcohol_percent": Decimal(strength),
                    "printed_note": note,
                    "sort_order": order,
                    "is_available": True,
                    "is_published": False,
                },
            )

            counts["items" if new_item else "existing_items"] += 1

            for price_order, (size, amount) in enumerate(
                (
                    ("2 cl", price_2),
                    ("4 cl", price_4),
                ),
                start=1,
            ):
                _, new_price = MenuPrice.objects.get_or_create(
                    item=item,
                    size_label=size,
                    defaults={
                        "price_eur": Decimal(amount),
                        "sort_order": price_order,
                        "is_available": True,
                    },
                )

                counts[
                    "prices" if new_price else "existing_prices"
                ] += 1

            marker = "+" if new_item else "="

            print(
                f"  {marker} {brand_name} — {name} "
                f"| 2 cl: {price_2} €, 4 cl: {price_4} €"
            )

    print("\n" + "=" * 51)
    print("BIERAKADEMIE — RUM / WEINBRAND & COGNAC")
    print("=" * 51)

    print(f"Neue Marken:              {counts['brands']}")
    print(f"Neue Positionen:          {counts['items']}")
    print(f"Vorhandene Positionen:    {counts['existing_items']}")
    print(f"Neue Preisvarianten:      {counts['prices']}")
    print(f"Vorhandene Preise:        {counts['existing_prices']}")
    print("Positionen in Druckkarte: 18")

    print("=" * 51)
    print("Bestehende Preise wurden nicht überschrieben.")
    print("Neue Produkte bleiben unveröffentlicht.")
    print("Bitte Druckkarten-Schreibweisen und unklare Sorten prüfen.")
