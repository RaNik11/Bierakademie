
"""Import Schnaps, Liköre und Kräuterschnäpse from the printed menu.

Source: Bierakademie in der Apothek, photograph IMG_2797.jpeg.
The printed menu is the source for prices, origins and alcohol content.
Manufacturer claims and product descriptions require separate verification.

The import can be repeated. Existing items and prices are not overwritten.
New items remain unpublished until the owner has checked their details.
"""

from decimal import Decimal

from django.db import transaction

from .models import Brand, MenuCategory, MenuGroup, MenuItem, MenuPrice


# Each row contains:
# (brand or None, product name, printed origin, strength, prices, note)
# Prices: ((size or serving, EUR), ...)
# If the producer is unclear in the printed menu, brand stays None.

SCHNAPS_DATA = {
    "Spirituosen": [
        ("Gordon", "Gin", "London", "37", (("2 cl", "3.50"), ("4 cl", "6.50")), "Druckkarte: Gordon Gin; genaue Marke später prüfen."),
        ("Gorbatschow", "Wodka", "Berlin", "37", (("2 cl", "3.50"), ("4 cl", "5.50")), "Druckkarte: Wodka Gorbatschow."),
        ("Gorroff", "Wodka (Roter)", "Essen", "16", (("2 cl", "3.00"), ("4 cl", "5.50")), "Markenschreibweise laut Druckkarte."),
        ("Gorroff", "Wodka (Schwarzer)", "Essen", "16", (("2 cl", "3.00"), ("4 cl", "5.50")), "Markenschreibweise laut Druckkarte."),
        ("Gorroff", "Wodka (Grüner)", "Essen", "17", (("2 cl", "3.00"), ("4 cl", "5.50")), "Markenschreibweise laut Druckkarte."),
        ("Stavros", "Ouzo", "Greek", "38", (("2 cl", "3.00"), ("4 cl", "5.50")), "Druckkarte: Greek (Herstellungsort nicht genauer angegeben)."),
        ("Mathis Bür", "Himbeergeist", "Gutach", "40", (("2 cl", "3.00"), ("4 cl", "5.50")), ""),
        (None, "Kirschwasser Schwarzwälder", "Düsseldorf", "40", (("2 cl", "3.00"), ("4 cl", "5.50")), "Hersteller unklar; Herkunft aus Druckkarte übernommen."),
        ("Brandstädter", "Obstler", "Gutach", "38", (("2 cl", "3.00"), ("4 cl", "5.50")), ""),
        ("Schwarzwaldhof", "Williams", "Ringelbach", "40", (("2 cl", "3.00"), ("4 cl", "5.50")), ""),
        ("Brandstädter", "Doppelkorn", "Steinhagen", "38", (("2 cl", "3.00"), ("4 cl", "5.50")), ""),
        (None, "Marillen select", "Schwarzwald", "40", (("2 cl", "3.00"), ("4 cl", "5.50")), "Hersteller in der Druckkarte nicht eindeutig benannt."),
        ("Cellini", "Grappa Destillato", "Italien", "38", (("2 cl", "3.00"), ("4 cl", "5.50")), ""),
        ("Cellini", "Grappa Invecchiata", "Italien", "38", (("2 cl", "3.00"), ("4 cl", "5.50")), ""),
        ("Sierra", "Tequila Silver", "Mexico", "38", (("2 cl", "3.50"), ("4 cl", "6.00")), ""),
        ("Sierra", "Tequila Reposado", "Mexico", "38", (("2 cl", "3.50"), ("4 cl", "6.00")), ""),
        (None, "Absinth 66 ★", "Magdeburg", "66", (("2 cl", "4.00"), ("4 cl", "7.50")), "Marke laut Druckkarte nicht eindeutig erkennbar."),
        ("Rialto", "Amaretto", "Lindenhof", "28", (("2 cl", "3.00"), ("4 cl", "5.50")), "Steht in der Druckkarte unter Spirituosen, obwohl es ein Likör ist."),
        (None, "Viagra Schnaps Spezial", "Bierakademie", "30", (("2 cl", "3.50"), ("4 cl", "6.00")), "Haus-Spezialität laut Druckkarte; Details beim Betreiber prüfen."),
    ],

    "Liköre": [
        ("Steinhauser", "Gletscherwasser", "Bodensee", "16", (("2 cl", "3.50"), ("4 cl", "6.00")), ""),
        ("Bols", "Banane", "Amsterdamm", "17", (("2 cl", "3.50"), ("4 cl", "6.00")), "Druckkarte schreibt den Ort 'Amsterdamm'."),
        ("Mangaroca", "Batida de Coco", "Brasilien", "16", (("2 cl", "3.50"), ("4 cl", "6.00")), ""),
        ("Malibu", "Coconut", "Karibik", "21", (("2 cl", "3.50"), ("4 cl", "6.00")), "Alkoholgehalt laut Druckkarte; Produktvariante vor Veröffentlichung prüfen."),
        ("Baileys", "Irish Cream", "Irland", "17", (("2 cl", "3.50"), ("4 cl", "6.00")), ""),
        (None, "Goldwasser", "Hardenberg", "40", (("2 cl", "4.00"), ("4 cl", "7.00")), "Hersteller nicht eindeutig in der Druckkarte genannt."),
        ("Eckes", "Edelkirsch", "Nordhausen", "20", (("2 cl", "3.50"), ("4 cl", "6.00")), ""),
        ("Kahlua", "Coffee Liqueur", "Mexico", "20", (("2 cl", "3.50"), ("4 cl", "6.00")), "Alkoholgehalt laut Druckkarte; vor Veröffentlichung prüfen."),
        ("Graziani", "Sambuca", "Italien", "40", (("2 cl", "3.00"), ("4 cl", "6.00")), ""),
        (None, "Pfefferminz", "Nordhausen", "18", (("2 cl", "3.00"), ("4 cl", "5.50")), "Hersteller in der Druckkarte nicht angegeben."),
    ],

    "Kräuterschnäpse": [
        ("Penninger", "Bärwurz", "Bayern", "40", (("2 cl", "3.50"), ("4 cl", "6.00")), ""),
        ("Jägermeister", "Kräuterlikör", "Wolfenbüttel", "35", (("Fläschchen 2 cl", "3.00"),), "Druckkarte: Jägermeister Fläschchen 2 cl; kein Preis für 4 cl angegeben."),
        ("Underberg", "Kräuterbitter", "Rheinberg", "44", (("Fläschchen 2 cl", "3.50"),), "Druckkarte: Underberg Fläschchen 2 cl; kein Preis für 4 cl angegeben."),
        ("Ramazzotti", "Amaro", "Milano", "30", (("2 cl", "3.00"), ("4 cl", "5.50")), ""),
        ("Averna", "Amaro", "Sicilia", "29", (("2 cl", "3.00"), ("4 cl", "5.50")), ""),
        ("Martini", "Bianco", "Torino", "15", (("2 cl", "3.00"), ("4 cl", "5.50")), "Druckkarte ordnet diesen Aperitif Kräuterschnäpsen zu."),
        ("Campari", "Tocco Rosso", "Milano", "25", (("2 cl", "3.50"), ("4 cl", "6.00")), "Name laut Druckkarte; genaue Produktvariante bitte prüfen."),
        ("Aperol", "Original", "Italien", "11", (("2 cl", "3.00"), ("4 cl", "5.50")), "Druckkarte ordnet diesen Aperitif Kräuterschnäpsen zu."),
    ],
}


# The printed page says +1,00 EUR for each mixed drink.
# This rule is already stored in MenuCategory.notice by the whisky importer.
# It must not be added automatically to product prices.


def validate_schnaps_data():
    expected_groups = {
        "Spirituosen": 19,
        "Liköre": 10,
        "Kräuterschnäpse": 8,
    }

    if set(SCHNAPS_DATA) != set(expected_groups):
        raise ValueError(
            "Die erwarteten Menügruppen stimmen nicht überein."
        )

    seen = set()
    total_prices = 0

    for group_name, expected_items in expected_groups.items():
        products = SCHNAPS_DATA[group_name]

        if len(products) != expected_items:
            raise ValueError(
                f"{group_name}: {expected_items} Positionen erwartet."
            )

        for brand, name, origin, strength, prices, note in products:
            key = (group_name, brand, name)

            if key in seen:
                raise ValueError(f"Doppelte Position: {key}")

            seen.add(key)

            if not name.strip() or not origin.strip() or not prices:
                raise ValueError(f"Fehlende Angaben: {key}")

            if not Decimal("0") <= Decimal(strength) <= Decimal("100"):
                raise ValueError(
                    f"Ungültiger Alkoholgehalt: {key}"
                )

            sizes = set()

            for size, price in prices:
                if (
                    size in sizes
                    or not size.strip()
                    or Decimal(price) <= 0
                ):
                    raise ValueError(
                        f"Ungültige Preisvariante: {key}: {size}"
                    )

                sizes.add(size)
                total_prices += 1

    if len(seen) != 37 or total_prices != 72:
        raise ValueError(
            "Erwartet: 37 Positionen und 72 Preisvarianten."
        )


@transaction.atomic
def import_schnaps_menu():
    validate_schnaps_data()

    category = MenuCategory.objects.get(
        slug="spirituosen"
    )

    counts = {
        "brands": 0,
        "items": 0,
        "existing_items": 0,
        "prices": 0,
        "existing_prices": 0,
    }

    for group_name, products in SCHNAPS_DATA.items():
        group = MenuGroup.objects.get(
            category=category,
            name=group_name,
        )

        print(
            f"\n{group_name}: {len(products)} Positionen"
        )

        for order, row in enumerate(products, start=1):
            (
                brand_name,
                name,
                origin,
                strength,
                prices,
                note,
            ) = row

            brand = None

            if brand_name:
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

            counts[
                "items" if new_item else "existing_items"
            ] += 1

            for price_order, (size, amount) in enumerate(
                prices,
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
                f"  {'+' if new_item else '='} "
                f"{display_name} | {display_prices}"
            )

    print("\n" + "=" * 50)
    print("BIERAKADEMIE — SCHNAPS / LIKÖRE / KRÄUTER")
    print(f"Neue Marken:              {counts['brands']}")
    print(f"Neue Positionen:          {counts['items']}")
    print(f"Bereits vorhanden:        {counts['existing_items']}")
    print(f"Neue Preisvarianten:      {counts['prices']}")
    print(f"Vorhandene Preise:        {counts['existing_prices']}")
    print("Einträge der gedruckten Karte: 37")
    print("Preisvarianten laut Karte:     72")
    print("=" * 50)

    print(
        "Jägermeister/Underberg: nur Fläschchen 2 cl, "
        "keine 4-cl-Preise."
    )
    print(
        "Preise und Alkoholgehalte vor Veröffentlichung bestätigen."
    )
    print(
        "Neue Positionen bleiben unveröffentlicht."
    )
