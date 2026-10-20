
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Brand,
    MenuCategory,
    MenuGroup,
    MenuItem,
    MenuPrice,
)


# ==================================================
# ADMIN BRANDING
# ==================================================

admin.site.site_header = "Bierakademie | Verwaltung"
admin.site.site_title = "Bierakademie"
admin.site.index_title = "Getränkekarte & Sortiment"


# ==================================================
# CATEGORIES
# ==================================================

@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "slug",
        "sort_order",
        "is_visible",
    )

    list_display_links = ("name",)

    list_editable = (
        "sort_order",
        "is_visible",
    )

    search_fields = (
        "name",
        "slug",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    ordering = (
        "sort_order",
        "id",
    )


# ==================================================
# GROUPS
# ==================================================

@admin.register(MenuGroup)
class MenuGroupAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "category",
        "theme",
        "sort_order",
        "is_visible",
    )

    list_display_links = ("name",)

    list_editable = (
        "sort_order",
        "is_visible",
    )

    list_filter = (
        "category",
        "theme",
        "is_visible",
    )

    search_fields = (
        "name",
        "category__name",
    )

    autocomplete_fields = (
        "category",
    )

    ordering = (
        "category__sort_order",
        "sort_order",
        "id",
    )


# ==================================================
# BRANDS / MANUFACTURERS
# ==================================================

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "city",
        "country",
        "founded_year",
        "has_logo",
    )

    list_filter = (
        "country",
    )

    search_fields = (
        "name",
        "city",
        "country",
    )

    readonly_fields = (
        "logo_preview",
    )

    fieldsets = (

        (
            "Hersteller / Marke",
            {
                "fields": (
                    "name",
                    "city",
                    "country",
                    "official_website",
                )
            },
        ),

        (
            "Geschichte",
            {
                "fields": (
                    "founded_year",
                    "founded_year_meaning",
                    "history",
                    "history_source_url",
                )
            },
        ),

        (
            "Markenlogo",
            {
                "fields": (
                    "logo",
                    "logo_preview",
                    "logo_source_url",
                )
            },
        ),

    )

    ordering = ("name",)

    @admin.display(
        boolean=True,
        description="Logo vorhanden",
    )
    def has_logo(self, obj):
        return bool(obj.logo)

    @admin.display(description="Logovorschau")
    def logo_preview(self, obj):

        if not obj.pk or not obj.logo:
            return "Noch kein Logo hochgeladen."

        return format_html(
            '<img src="{}" alt="Markenlogo" '
            'style="max-width:180px;'
            'max-height:110px;'
            'object-fit:contain;">',
            obj.logo.url,
        )


# ==================================================
# PRICE VARIANTS INSIDE MENU ITEMS
# ==================================================

class MenuPriceInline(admin.TabularInline):

    model = MenuPrice

    extra = 1

    fields = (
        "size_label",
        "price_eur",
        "sort_order",
        "is_available",
    )

    verbose_name = "Preisvariante"
    verbose_name_plural = "Preise und Größen"


# ==================================================
# MENU ITEMS
# ==================================================

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):

    list_display = (
        "display_name",
        "group",
        "alcohol_percent",
        "price_summary",
        "is_available",
        "is_published",
        "sort_order",
    )

    list_display_links = (
        "display_name",
    )

    list_editable = (
        "is_available",
        "is_published",
        "sort_order",
    )

    list_filter = (
        "group__category",
        "is_available",
        "is_published",
    )

    search_fields = (
        "name",
        "brand__name",
        "group__name",
        "production_location",
    )

    autocomplete_fields = (
        "group",
        "brand",
    )

    list_select_related = (
        "group",
        "group__category",
        "brand",
    )

    inlines = (
        MenuPriceInline,
    )

    list_per_page = 50

    ordering = (
        "group__category__sort_order",
        "group__sort_order",
        "sort_order",
        "id",
    )

    fieldsets = (

        (
            "Produkt",
            {
                "fields": (
                    "group",
                    "brand",
                    "name",
                    "production_location",
                    "alcohol_percent",
                )
            },
        ),

        (
            "Angaben aus der gedruckten Karte",
            {
                "fields": (
                    "printed_note",
                    "ingredients",
                    "allergen_codes",
                    "additive_codes",
                )
            },
        ),

        (
            "Bierakademie-Texte für die Website",
            {
                "fields": (
                    "geschmack_kurz",
                    "beschreibung",
                ),
                "description": (
                    "Kurzgeschmack erscheint auf der kleinen Karte; "
                    "Beschreibung erscheint in den aufgeklappten Details."
                ),
            },
        ),

        (
            "Offizielle Herstellerinformationen",
            {
                "fields": (
                    "official_description",
                    "official_source_url",
                    "product_history",
                    "product_history_source_url",
                ),
                "classes": ("collapse",),
            },
        ),

        (
            "Produktbild",
            {
                "fields": (
                    "image",
                )
            },
        ),

        (
            "Anzeige und Reihenfolge",
            {
                "fields": (
                    "sort_order",
                    "is_available",
                    "is_published",
                )
            },
        ),

    )

    def get_queryset(self, request):

        queryset = super().get_queryset(request)

        return queryset.prefetch_related("prices")

    @admin.display(
        description="Getränk / Speise",
        ordering="name",
    )
    def display_name(self, obj):

        if obj.brand_id:
            return f"{obj.brand.name} — {obj.name}"

        return obj.name

    @admin.display(description="Preise")
    def price_summary(self, obj):

        prices = [
            price
            for price in obj.prices.all()
            if price.is_available
        ]

        if not prices:
            return "Keine Preise"

        return " | ".join(
            f"{price.size_label}: "
            f"{str(price.price_eur).replace('.', ',')} €"
            for price in prices
        )


# ==================================================
# ALL PRICES
# ==================================================

@admin.register(MenuPrice)
class MenuPriceAdmin(admin.ModelAdmin):

    list_display = (
        "item",
        "size_label",
        "price_eur",
        "is_available",
        "sort_order",
    )

    list_display_links = (
        "item",
    )

    list_editable = (
        "price_eur",
        "is_available",
        "sort_order",
    )

    list_filter = (
        "is_available",
        "item__group__category",
    )

    search_fields = (
        "item__name",
        "item__brand__name",
        "size_label",
    )

    autocomplete_fields = (
        "item",
    )

    list_select_related = (
        "item",
        "item__brand",
        "item__group",
    )

    list_per_page = 50
