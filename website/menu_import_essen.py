"""Import the priced cold dishes from Bierakademie's printed menu.

Source: IMG_2803.jpeg, 'Kalte Speisen — nach Tagesangebot'.
Only seven dishes carry prices. The unpriced 'Mezze Teller' component
list is stored as group information, not as a priced product.

This importer does not overwrite existing records or prices.
All new dishes remain unpublished until the owner checks the menu.
"""

from decimal import Decimal

from django.db import transaction

from .models import MenuGroup, MenuItem, MenuPrice


# Each entry: (name, ingredients printed on menu, printed note, EUR price).
# Allergen fields stay empty: the printed menu does not give a complete
# product-specific allergen declaration for these seven dishes.

FOOD_ITEMS = [
    (
        "Wurstsalat",
        "Emmentaler, Lyoner, Zwiebeln, Radieschen, Petersilie, "
        "rote Paprika, Sellerie und Bauerngurken.",
        "",
        "7.00",
    ),
    (
        "Landjäger Delikatesse",
        "Schweinefleisch, Rindfleisch und Brot.",
        "Eine geräucherte Spitzenqualität (laut Druckkarte).",
        "2.00",
    ),
    ("Großer Veganer Teller", "", "Nach Tagesangebot.", "11.00"),
    ("Veganer Teller", "", "Nach Tagesangebot.", "8.50"),
    ("Großer Vegetarischer Teller", "", "Nach Tagesangebot.", "11.00"),
    ("Vegetarischer Teller", "", "Nach Tagesangebot.", "8.50"),
    (
        "Mezze Großer Spezialteller",
        "6 Fleischbällchen, geräucherte Giganten Bohnen, Kartoffelsalat, "
        "Pikantiki, Salat, Tzatziki und Brot.",
        "",
        "11.00",
    ),
]


MEZZE_GROUP_DESCRIPTION = (
    "Mezze Teller — Zusammenstellung laut gedruckter Karte "
    "(kein eigener Preis angegeben):\n"
    "1. Im Backofen geräucherte Giganten Bohnen.\n"
    "2. Fleischbällchen.\n"
    "3. Tzatziki (A3).\n"
    "4. Pikantiki: Salat mit Weißkraut, Karotten, Petersilie, "
    "roter, gelber und grüner Paprika, Sellerie und Olivenöl.\n"
    "5. Gegrillter Auberginen Salat: Aubergine 75 %, Sojaöl, "
    "gegrillte Paprika, Essig, Knoblauch und Meersalz (E202).\n"
    "6. Taramas: Fischrogencreme mit Olivenöl und Zitrone "
    "(A2, Z1, Z5).\n"
    "7. Weichkäse mit Oregano und Olivenöl (A3).\n"
    "8. Tirokafteri: würziger Fetakäse mit gegrillten "
    "Peperoni (A3).\n"
    "9. Gefüllte Weinblätter: mit Reis gefüllte Weinblätter, "
    "Zwiebeln und Zitronensoße (A12, Z2, Z5, Z7, Z8).\n\n"
    "Die A-/Z-Codes stammen aus der Druckkarte. "
    "Die vollständige Zuordnung der Allergene und Zusatzstoffe "
    "zu verkauften Gerichten muss vom Betreiber geprüft werden."
)


def validate_food_data():
    if len(FOOD_ITEMS) != 7:
        raise ValueError("Erwartet: sieben Gerichte mit gedrucktem Preis.")

    names = set()
    for name, ingredients, note, price in FOOD_ITEMS:
        if not name.strip() or name in names:
            raise ValueError(f"Fehlender oder doppelter Name: {name!r}")
        names.add(name)
        if Decimal(price) <= 0:
            raise ValueError(f"Ungültiger Preis für {name}: {price}")


@transaction.atomic
def import_essen_menu():
    validate_food_data()

    group = MenuGroup.objects.get(
        category__slug="essen",
        name="Kalte Speisen",
    )

    # Preserve descriptions already edited by an administrator.
    if not group.description:
        group.description = MEZZE_GROUP_DESCRIPTION
        group.save(update_fields=["description"])

    created_items = 0
    existing_items = 0
    created_prices = 0
    existing_prices = 0

    print("\nKalte Speisen — nach Tagesangebot")

    for position, (name, ingredients, note, price_eur) in enumerate(
        FOOD_ITEMS, start=1
    ):
        item, is_new = MenuItem.objects.get_or_create(
            group=group,
            brand=None,
            name=name,
            defaults={
                "ingredients": ingredients,
                "printed_note": note,
                "allergen_codes": "",
                "additive_codes": "",
                "sort_order": position,
                "is_available": True,
                "is_published": False,
            },
        )

        created_items += int(is_new)
        existing_items += int(not is_new)

        # 'Standard' is a technical variant label, not a claimed volume.
        _, is_new_price = MenuPrice.objects.get_or_create(
            item=item,
            size_label="Standard",
            defaults={
                "price_eur": Decimal(price_eur),
                "sort_order": 1,
                "is_available": True,
            },
        )
        created_prices += int(is_new_price)
        existing_prices += int(not is_new_price)

        print(f"  {'+' if is_new else '='} {name} | {price_eur} €")

    print("\n" + "=" * 52)
    print("BIERAKADEMIE — KALTE SPEISEN IMPORT")
    print(f"Neue Gerichte:            {created_items}")
    print(f"Vorhandene Gerichte:      {existing_items}")
    print(f"Neue Preisvarianten:      {created_prices}")
    print(f"Vorhandene Preisvarianten: {existing_prices}")
    print("Preise laut Druckkarte:  7")
    print("=" * 52)
    print("Mezze Teller (ohne Einzelpreis) als Gruppeninfo gespeichert,")
    print("sofern die Gruppenbeschreibung vorher leer war.")
    print("Bestehende Preise wurden nicht überschrieben.")
    print("Allergene/Zusatzstoffe vor Veröffentlichung prüfen.")
    print("Neue Gerichte bleiben unveröffentlicht.")