
"""Import the 26 whisky/whiskey-page listings from Bierakademie's printed menu.

Source: photographs IMG_2798.jpeg and IMG_2799.jpeg, October 2026.
All prices and strengths reproduce the printed menu, not vendor verification.
The importer adds missing objects only and never overwrites existing prices.
New menu items are unpublished until reviewed.
"""

from decimal import Decimal

from django.db import transaction

from .models import Brand, MenuCategory, MenuGroup, MenuItem, MenuPrice


# Each row:
# (brand, item name, origin printed on menu, ABV %, 2-cl price,
#  4-cl price, additional note)
# A few liqueurs are intentionally kept in the whiskey-page groups,
# matching the printed menu rather than guessing another category.

WHISKY_DATA = {
    "Whiskey": [
        ("Jack Daniel's", "Gentleman Jack", "Tennessee", "40.0", "4.50", "7.50", "Gedruckt: Gentleman Jack Daniels."),
        ("Jack Daniel's", "Nr. 7", "Tennessee", "40.0", "4.00", "6.50", "Gedruckt: Jack Nr. 7."),
        ("Wild Turkey", "Honey Whiskey", "USA", "35.0", "4.00", "6.50", ""),
        ("Bulleit", "95 Rye Frontier Whiskey", "USA", "45.0", "4.50", "6.50", ""),
        ("Woodford Reserve", "Straight Bourbon", "Kentucky", "45.0", "4.50", "7.50", ""),
        ("Jim Beam", "Bourbon Whiskey", "Kentucky", "40.0", "4.00", "6.50", ""),
        ("Slyrs", "Single Malt Whisky", "Bayern", "43.0", "6.00", "11.00", ""),
        ("Tecker", "Malt Whisky Sherry Single", "Deutschland", "43.0", "6.50", "11.00", ""),
        ("Tecker", "Sherry Cask Matured Single Malt", "Deutschland", "43.0", "6.50", "11.00", ""),
        ("Tecker", "Aged 5 Years", "Deutschland", "40.0", "5.00", "8.00", ""),
        ("Connemara", "Peated Single Malt Whiskey", "Irland", "40.0", "5.00", "8.00", ""),
        ("Irish Mist", "Ireland's Legendary Honey Liqueur", "Irland", "35.0", "4.50", "7.00", "Likör; in der gedruckten Karte unter Whiskey aufgeführt."),
        ("Redbreast", "Single Pot Still", "Irland", "40.0", "6.00", "11.00", ""),
        ("Bushmills", "Single Malt Whiskey", "Irland", "40.0", "4.00", "7.00", ""),
        ("Southern Comfort", "Original", "New Orleans", "35.0", "4.00", "7.00", "Likör; in der gedruckten Karte unter Whiskey aufgeführt."),
    ],
    "Scotch Whisky": [
        ("Aberlour", "Speyside Single Malt Whisky", "Scotch", "40.0", "5.00", "8.00", ""),
        ("Talisker", "Single Malt", "Scotch", "46.0", "5.00", "8.00", ""),
        ("Ardbeg", "Islay Single Malt", "Scotch", "46.0", "6.00", "10.00", ""),
        ("Highland Park", "Single Malt", "Scotch", "40.0", "6.00", "10.00", ""),
        ("Drambuie", "The Isle of Skye Liqueur", "Scotch", "40.0", "4.00", "7.00", "Likör; in der gedruckten Karte unter Whiskey aufgeführt."),
        ("Cardhu", "Single Malt", "Scotch", "40.0", "5.00", "8.00", ""),
        ("Johnnie Walker", "Gold Label Reserve", "Scotch", "40.0", "5.50", "9.00", ""),
        ("Johnnie Walker", "Red Label Reserve", "Scotch", "40.0", "4.00", "7.00", "Bezeichnung aus der gedruckten Karte; Produktname später prüfen."),
        ("Chivas Regal", "Blended Whisky", "Scotch", "40.0", "5.00", "8.00", ""),
        ("Dimple", "Golden Selection Blended Whisky", "Scotch", "40.0", "5.00", "8.00", ""),
        ("Ballantine's", "Finest Blended Whisky", "Scotch", "40.0", "4.00", "7.00", ""),
    ],
}

MIXER_NOTE = (
    "Zu jedem Mischgetränk wird 1,00 € zusätzlich berechnet "
    "(laut gedruckter Getränkekarte)."
)


def validate_whisky_data():
    if sum(map(len, WHISKY_DATA.values())) != 26:
        raise ValueError("Die Druckkarte muss genau 26 Positionen enthalten.")

    expected_groups = {"Whiskey", "Scotch Whisky"}
    if set(WHISKY_DATA) != expected_groups:
        raise ValueError("Unerwartete Whisky-Gruppen.")

    seen = set()
    for group_name, products in WHISKY_DATA.items():
        for brand, name, origin, strength, price_2cl, price_4cl, note in products:
            identity = (group_name, brand, name)
            if identity in seen:
                raise ValueError(f"Doppelte Position: {identity}")
            seen.add(identity)

            if not all((brand.strip(), name.strip(), origin.strip())):
                raise ValueError(f"Fehlender Name oder Herkunft: {identity}")
            if not Decimal("0") <= Decimal(strength) <= Decimal("100"):
                raise ValueError(f"Ungültiger Alkoholgehalt: {identity}")
            if Decimal(price_2cl) <= 0 or Decimal(price_4cl) <= 0:
                raise ValueError(f"Ungültiger Preis: {identity}")


@transaction.atomic
def import_whisky_menu():
    validate_whisky_data()

    category = MenuCategory.objects.get(slug="spirituosen")
    if not category.notice:
        category.notice = MIXER_NOTE
        category.save(update_fields=["notice"])

    counts = dict(brands=0, items=0, prices=0, existing_items=0, existing_prices=0)

    for group_name, products in WHISKY_DATA.items():
        group = MenuGroup.objects.get(category=category, name=group_name)
        print(f"\n{group_name}: {len(products)} Positionen")

        for order, (brand_name, name, origin, strength, p2, p4, note) in enumerate(products, start=1):
            brand, new_brand = Brand.objects.get_or_create(name=brand_name)
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

            for price_order, (size, amount) in enumerate((("2 cl", p2), ("4 cl", p4)), start=1):
                _, new_price = MenuPrice.objects.get_or_create(
                    item=item,
                    size_label=size,
                    defaults={
                        "price_eur": Decimal(amount),
                        "sort_order": price_order,
                        "is_available": True,
                    },
                )
                counts["prices" if new_price else "existing_prices"] += 1

            print(f"  {'+' if new_item else '='} {brand_name} — {name} | 2 cl: {p2} €, 4 cl: {p4} €")

    print("\n" + "=" * 50)
    print("BIERAKADEMIE — WHISKEY / SCOTCH IMPORT")
    print(f"Neue Marken:            {counts['brands']}")
    print(f"Neue Positionen:        {counts['items']}")
    print(f"Vorhandene Positionen:  {counts['existing_items']}")
    print(f"Neue Preisvarianten:    {counts['prices']}")
    print(f"Vorhandene Preise:      {counts['existing_prices']}")
    print(f"Positionen in Druckkarte: {sum(map(len, WHISKY_DATA.values()))}")
    print("=" * 50)
    print("Bestehende Einträge/Preise wurden nicht überschrieben.")
    print("Neue Positionen bleiben bis zur Prüfung unveröffentlicht.")
