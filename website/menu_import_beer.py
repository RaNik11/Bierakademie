
"""
Bierakademie — Import der Bierkarte.

Quelle:
Gedruckte Bierakademie-Getränkekarte, Fotos IMG_2792–2794.

Importiert:
- 50 Bierpositionen
- Marken
- Herstellungsorte laut Karte
- Alkoholgehalt
- Preisvarianten
- Hinweise aus der gedruckten Karte

Offizielle Herstellerbeschreibungen und Logos folgen später.

Der Import überschreibt bestehende Preise nicht.
Alle importierten Positionen bleiben zunächst unveröffentlicht.
"""

from decimal import Decimal

from django.db import transaction

from .models import Brand, MenuGroup, MenuItem, MenuPrice


# ==================================================
# FORMAT
# ==================================================
#
# (
#     Hersteller oder None,
#     Produktname,
#     Herkunft laut Karte,
#     Alkoholgehalt,
#     Hinweis aus Papierkarte,
#     ((Menge, Preis), ...)
# )
#
# Alle Preise in EUR.
# Fehlender Alkoholgehalt: None.
# ==================================================


BEER_DATA = {

    # ==================================================
    # BIER VOM FASS — 6
    # ==================================================

    "Bier vom Fass": [

        (
            "Paulaner", "Hefe", "München", "5.4",
            "Hefeweizen.",
            (("0,33 l", "3.70"), ("0,5 l", "4.50")),
        ),

        (
            "Hirsch", "Gold, Halbe", "Wurmlingen", "5.2",
            "Helles Bier.",
            (("0,33 l", "3.70"), ("0,5 l", "4.50")),
        ),

        (
            "Bitburger", "Pils", "Bitburg", "4.9",
            "Pils.",
            (("0,33 l", "3.70"),),
        ),

        (
            None, "Russ Mixbier", "München", None,
            "Hefeweizen mit Sprudel, süß oder sauer.",
            (("0,33 l", "3.50"), ("0,5 l", "4.00")),
        ),

        (
            None, "Radler Mixbier", "Wurmlingen", None,
            "Helles mit Sprudel, süß oder sauer.",
            (("0,33 l", "3.50"), ("0,5 l", "4.00")),
        ),

        (
            None, "Cola Weizen Mixbier", "München", None,
            "Hefeweizen mit Cola.",
            (("0,33 l", "3.50"), ("0,5 l", "4.00")),
        ),
    ],

    # ==================================================
    # HELLE BIERE — 5
    # ==================================================

    "Helle Biere aus der Flasche": [

        (
            "Gold Ochsen", "Original", "Ulm", "5.1",
            "Ulms flüssiges Gold.",
            (("0,5 l", "3.80"),),
        ),

        (
            "Benediktiner", "Helles", "Ettal", "5.0",
            "Lagerbier.",
            (("0,5 l", "4.00"),),
        ),

        (
            "Hirsch", "Helles", "Wurmlingen", "4.8",
            "Mild, süffig.",
            (("0,5 l", "4.00"),),
        ),

        (
            "Stuttgarter", "Bügel Premium", "Stuttgart", "5.5",
            "Süffig, erfrischend.",
            (("0,5 l", "4.00"),),
        ),

        (
            "Augustiner", "Edelstoff", "München", "5.6",
            "Exportbier.",
            (("0,5 l", "4.00"),),
        ),
    ],

    # ==================================================
    # HEFE UND NATURTRÜB — 7
    # ==================================================

    "Hefe und Naturtrüb": [

        (
            "Schneider", "Hefe TAP 1", "Kelheim", "5.2",
            "Bayerische Edelreifung.",
            (("0,5 l", "4.00"),),
        ),

        (
            "Schneider", "Original TAP 7", "Kelheim", "5.2",
            "Leicht, dunkel.",
            (("0,5 l", "4.00"),),
        ),

        (
            "Paulaner", "Hefe", "München", "5.4",
            "Naturtrüb.",
            (("0,5 l", "4.00"),),
        ),

        (
            "Huber", "Hefe Original", "Freising", "5.4",
            "Goldgelb.",
            (("0,5 l", "4.00"),),
        ),

        (
            "Erdinger", "Hefe", "Erding", "5.3",
            "Weißbier.",
            (("0,5 l", "4.00"),),
        ),

        (
            "Franziskaner", "Hefe", "München", "5.0",
            "Naturtrüb.",
            (("0,5 l", "4.00"),),
        ),

        (
            "Hirsch", "Zwickl Unfiltriert", "Wurmlingen", "5.2",
            "Naturtrüb.",
            (("0,5 l", "4.00"),),
        ),
    ],

    # ==================================================
    # KRISTALL — 5
    # ==================================================

    "Flaschenbiere Kristall": [

        (
            "Schneider", "Kristall TAP 2", "Kelheim", "4.9",
            "Kristallklar.",
            (("0,5 l", "4.00"),),
        ),

        (
            "Erdinger", "Kristall", "Erding", "5.3",
            "Spritzig.",
            (("0,5 l", "4.00"),),
        ),

        (
            "Sanwald", "Kristall", "Stuttgart", "5.2",
            "Kristallklar.",
            (("0,5 l", "4.00"),),
        ),

        (
            "Weihenstephan", "Kristall", "Freising", "5.4",
            "La Brillanz.",
            (("0,5 l", "4.00"),),
        ),

        (
            "Maisel's", "Kristall", "Bayreuth", "5.0",
            "Prickelnde Erfrischung.",
            (("0,5 l", "4.00"),),
        ),
    ],

    # ==================================================
    # FLASCHENBIERE — 9
    # ==================================================

    "Flaschenbiere": [

        (
            "Gruibinger", "Brunnenbier", "Gruibingen", "5.1",
            "Naturtrüb.",
            (("0,33 l", "3.70"),),
        ),

        (
            "Rothaus", "Tannenzäpfle Pils", "Schwarzwald", "5.1",
            "Das badische Kultbier.",
            (("0,33 l", "3.60"),),
        ),

        (
            "Jever", "Pils", "Jever", "4.9",
            "Friesisch herb.",
            (("0,33 l", "3.60"),),
        ),

        (
            "Beck's", "Pils", "Bremen", "4.9",
            "Mit weichem Brauwasser.",
            (("0,33 l", "3.60"),),
        ),

        (
            "Hirsch", "Goldstoff Bügelflasche", "Wurmlingen", "5.2",
            "Zarte Hopfennote.",
            (("0,33 l", "3.70"),),
        ),

        (
            "Wulle", "Bügelflasche", "Stuttgart", "5.0",
            "Wir wollen Wulle.",
            (("0,33 l", "3.70"),),
        ),

        (
            "Diebels", "Alt", "Issum", "4.9",
            "Würziger Abgang.",
            (("0,33 l", "3.70"),),
        ),

        (
            "König", "Pilsner", "Duisburg", "4.9",
            "Das König der Biere.",
            (("0,33 l", "3.70"),),
        ),

        (
            "Desperados", "Original", "Holland", "5.9",
            "Mit Tequila-Aroma.",
            (("0,33 l", "4.70"),),
        ),
    ],

    # ==================================================
    # DUNKLE BIERE — 3
    # ==================================================

    "Flaschenbiere Dunkel": [

        (
            "Franziskaner", "Dunkel", "München", "5.0",
            "Hefetrüb.",
            (("0,5 l", "4.00"),),
        ),

        (
            "Erdinger", "Dunkel", "Erding", "5.3",
            "Dunkelbraun.",
            (("0,5 l", "4.00"),),
        ),

        (
            "Hirsch", "Dunkel Hefe", "Wurmlingen", "5.4",
            "Mild gehopft.",
            (("0,5 l", "4.00"),),
        ),
    ],

    # ==================================================
    # SPEZIELLE BIERE — 1
    # ==================================================

    "Spezielle Biere Hilzenbecks": [

        (
            None, "Schottenbock", "Gruibingen", "9.1",
            "Ein Jahr im Whiskyfass gereift. "
            "Bierspezialität mit feinen Whiskyaromen. "
            "Flaschengröße bitte beim Betreiber prüfen.",
            (("Größe noch prüfen", "22.00"),),
        ),
    ],

    # ==================================================
    # HOLZFASSGEREIFTER BOCK — 1
    # ==================================================

    "Holzfassgereifter Bock": [

        (
            "Hirsch",
            "Premium Silver Label — Jahrgangsbieredition 2019",
            "Wurmlingen",
            "7.4",
            "25-Jahr-Edition. Neun Monate im Madeira-Eichenfass "
            "gelagert. Kastanienbraunes Bockbier.",
            (("0,75 l", "25.00"),),
        ),
    ],

    # ==================================================
    # STARKBIERE — 9
    # ==================================================

    "Starkbiere aus der Flasche": [

        (
            "Schneider", "Aventinus Eisbock", "Kelheim", "12.0",
            "Würzige Pflaumennoten, ein Hauch Bittermandel "
            "und Marzipan. Dunkle, mahagoniähnliche Farbe.",
            (("0,33 l", "7.30"),),
        ),

        (
            "Camba", "Black Shark", "Bayern", "8.5",
            "Duft nach Rhabarber, Stachelbeere und Pfirsich. "
            "Röstaromen, Kaffee und Bitterschokolade.",
            (("0,33 l", "7.30"),),
        ),

        (
            "Camba", "Imperial IPA", "Bayern", "8.9",
            "Ausgeprägte Hopfenaromen mit Limetten- und "
            "Zitrusnoten. Kräftige, ausbalancierte Hopfenbittere.",
            (("0,33 l", "7.30"),),
        ),

        (
            "Schneider",
            "Aventinus Doppelbock TAP 6",
            "Kelheim",
            "8.2",
            "Intensiver Weizenbock mit dunkler Rubinfarbe "
            "und fester weißer Schaumkrone.",
            (("0,5 l", "5.80"),),
        ),

        (
            "Schneider", "Hopfenweiße TAP 5", "Kelheim", "8.2",
            "Klassisches Weizendoppelbockbier. Blumig, herb, "
            "mit malzaromatischer Süße und Aromahopfen.",
            (("0,5 l", "5.80"),),
        ),

        (
            "Andechser", "Doppelbock", "Andechs", "7.1",
            "Weiche Röstnoten und ein Hauch Dörrobst. "
            "Dunkler Bock.",
            (("0,5 l", "5.80"),),
        ),

        (
            "Andechser", "Bergbock Hell", "Andechs", "6.9",
            "Klargoldenes Klosterbier mit kräftigem Malz "
            "und blumigen Hopfenaromen.",
            (("0,5 l", "5.80"),),
        ),

        (
            "Paulaner", "Salvator", "München", "7.9",
            "Bernsteinfarbener Doppelbock nach bayerischer "
            "Brautradition mit vollmundigem Geschmack.",
            (("0,5 l", "5.80"),),
        ),

        (
            "Weihenstephan", "Korbinian", "Freising", "7.4",
            "Dunkelhellbrauner Doppelbock mit fruchtigen "
            "Nuancen und feinen Malzaromen.",
            (("0,5 l", "5.80"),),
        ),
    ],

    # ==================================================
    # ALKOHOLFREIE BIERE — 4
    # ==================================================

    "Alkoholfreie Flaschenbiere": [

        (
            "Schneider", "Hefe Alkoholfrei", "Kelheim", "0.5",
            "Isotonisch, vitaminhaltig.",
            (("0,5 l", "4.00"),),
        ),

        (
            "Benediktiner", "Hefe Alkoholfrei", "Ettal", "0.5",
            "Kalorienreduziert.",
            (("0,5 l", "4.00"),),
        ),

        (
            "Bitburger", "0,0", "Bitburg", "0.0",
            "Mit Ettaler Kellerhefe laut gedruckter Karte.",
            (("0,33 l", "3.60"),),
        ),

        (
            "Beck's", "Blue", "Bremen", "0.5",
            "Erfrischend.",
            (("0,33 l", "3.60"),),
        ),
    ],
}


# ==================================================
# VALIDATION
# ==================================================

def validate_beer_data():

    rows = sum(len(items) for items in BEER_DATA.values())

    if rows != 50:
        raise ValueError(
            f"50 Bierpositionen erwartet, gefunden: {rows}"
        )

    seen = set()

    for group_name, items in BEER_DATA.items():

        if not items:
            raise ValueError(f"Leere Menügruppe: {group_name}")

        for brand, name, location, alcohol, note, prices in items:

            key = (group_name, brand, name)

            if key in seen:
                raise ValueError(f"Doppelte Importposition: {key}")

            seen.add(key)

            if not name.strip():
                raise ValueError(f"Produktname fehlt: {group_name}")

            if not prices:
                raise ValueError(f"Preis fehlt: {name}")

            for size, amount in prices:

                if not size.strip():
                    raise ValueError(f"Größe fehlt: {name}")

                if Decimal(amount) <= 0:
                    raise ValueError(f"Ungültiger Preis: {name}")


# ==================================================
# DATABASE IMPORT
# ==================================================

@transaction.atomic
def import_beer_menu():

    validate_beer_data()

    created_brands = 0
    created_items = 0
    created_prices = 0

    existing_items = 0
    existing_prices = 0

    for group_name, items in BEER_DATA.items():

        group = MenuGroup.objects.get(
            category__slug="bier",
            name=group_name,
        )

        print(f"\n{group_name}")

        for position, row in enumerate(items, start=1):

            (
                brand_name,
                product_name,
                location,
                alcohol,
                printed_note,
                prices,
            ) = row

            brand = None

            # --------------------------------------
            # BRAND
            # --------------------------------------

            if brand_name:

                brand, brand_created = (
                    Brand.objects.get_or_create(
                        name=brand_name
                    )
                )

                if brand_created:
                    created_brands += 1

            # --------------------------------------
            # MENU ITEM
            # --------------------------------------

            item, item_created = (
                MenuItem.objects.get_or_create(
                    group=group,
                    brand=brand,
                    name=product_name,
                    defaults={
                        "production_location": location,
                        "alcohol_percent": (
                            Decimal(alcohol)
                            if alcohol is not None
                            else None
                        ),
                        "printed_note": printed_note,
                        "allergen_codes": "13",
                        "sort_order": position,
                        "is_available": True,
                        "is_published": False,
                    },
                )
            )

            if item_created:
                created_items += 1
                marker = "+"
            else:
                existing_items += 1
                marker = "="

            # --------------------------------------
            # PRICE VARIANTS
            # --------------------------------------

            for price_order, (size, amount) in enumerate(
                prices,
                start=1,
            ):

                price, price_created = (
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

                if price_created:
                    created_prices += 1
                else:
                    existing_prices += 1

            display_name = (
                f"{brand_name} {product_name}"
                if brand_name
                else product_name
            )

            print(f"  {marker} {display_name}")

    # ==================================================
    # RESULT
    # ==================================================

    print("\n" + "=" * 48)
    print("BIERAKADEMIE — BIERIMPORT")
    print("=" * 48)

    print(f"Neue Marken:          {created_brands}")
    print(f"Neue Bierpositionen:  {created_items}")
    print(f"Bereits vorhanden:    {existing_items}")
    print(f"Neue Preisvarianten:  {created_prices}")
    print(f"Preise unverändert:   {existing_prices}")

    print("-" * 48)

    print(f"Biergruppen im Import: {len(BEER_DATA)}")
    print(
        "Bierpositionen im Import: "
        f"{sum(len(items) for items in BEER_DATA.values())}"
    )

    print("=" * 48)

    print(
        "\nHinweis: Schottenbock — "
        "Flaschengröße noch prüfen."
    )

    print(
        "Alle neuen Bierpositionen bleiben "
        "vorerst unveröffentlicht."
    )

    print("\nImport abgeschlossen.")
