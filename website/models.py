
"""Data models for the Bierakademie food and drinks menu.

The existing static drinks.html stays in place until the printed menu has
been imported and verified. No products or prices are created by this file.
"""

from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import logging

from PIL import Image, ImageOps

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

logger = logging.getLogger(__name__)


class MenuCategory(models.Model):
    """Main menu section, e.g. Bier, Spirituosen or Wein & Sekt."""

    name = models.CharField("Name", max_length=100)
    slug = models.SlugField(
        "URL-Kennung",
        max_length=80,
        unique=True,
        help_text="Zum Beispiel: bier, spirituosen, alkoholfrei.",
    )
    subtitle = models.CharField("Untertitel", max_length=180, blank=True)
    introduction = models.TextField("Beschreibung", blank=True)
    notice = models.TextField(
        "Hinweis zur Kategorie",
        blank=True,
        help_text="Zum Beispiel Zuschläge für Mischgetränke.",
    )
    sort_order = models.PositiveIntegerField("Reihenfolge", default=0)
    is_visible = models.BooleanField("Sichtbar", default=True)

    class Meta:
        verbose_name = "Menükategorie"
        verbose_name_plural = "Menükategorien"
        ordering = ("sort_order", "id")

    def __str__(self):
        return self.name


class MenuGroup(models.Model):
    """Subsection, e.g. Bier vom Fass, Scotch or Kräuterschnäpse."""

    class Theme(models.TextChoices):
        LIGHT = "light", "Hell"
        GREEN = "green", "Dunkelgrün"
        RED = "red", "Dunkelrot"
        BOTTLES = "bottles", "Flaschenbier"

    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.PROTECT,
        related_name="groups",
        verbose_name="Kategorie",
    )
    name = models.CharField("Gruppenname", max_length=140)
    eyebrow = models.CharField(
        "Kleine Überschrift", max_length=120, blank=True
    )
    description = models.TextField("Beschreibung", blank=True)
    theme = models.CharField(
        "Darstellung",
        max_length=12,
        choices=Theme.choices,
        default=Theme.LIGHT,
    )
    sort_order = models.PositiveIntegerField("Reihenfolge", default=0)
    is_visible = models.BooleanField("Sichtbar", default=True)

    class Meta:
        verbose_name = "Menügruppe"
        verbose_name_plural = "Menügruppen"
        ordering = ("sort_order", "id")

    def __str__(self):
        return f"{self.category.name} / {self.name}"


class Brand(models.Model):
    """Brand or brewery; separate from a product and its place of production."""

    name = models.CharField("Marke / Hersteller", max_length=140, unique=True)
    country = models.CharField("Land", max_length=100, blank=True)
    city = models.CharField("Ort", max_length=120, blank=True)
    founded_year = models.PositiveSmallIntegerField(
        "Historisches Jahr", null=True, blank=True
    )
    founded_year_meaning = models.CharField(
        "Bedeutung des Jahres",
        max_length=140,
        blank=True,
        help_text="Zum Beispiel: Brauerei gegründet / Marke eingeführt.",
    )
    history = models.TextField("Geschichte", blank=True)
    history_source_url = models.URLField(
        "Offizielle Quelle zur Geschichte", max_length=500, blank=True
    )
    official_website = models.URLField(
        "Offizielle Website", max_length=500, blank=True
    )
    logo_source_url = models.URLField(
        "Quelle des Markenlogos", max_length=500, blank=True
    )
    logo = models.ImageField(
        "Logo", upload_to="menu/brands/", blank=True
    )

    class Meta:
        verbose_name = "Marke / Hersteller"
        verbose_name_plural = "Marken / Hersteller"
        ordering = ("name",)

    def clean(self):
        super().clean()
        if (self.history or self.founded_year) and not self.history_source_url:
            raise ValidationError({
                "history_source_url": (
                    "Für die Markengeschichte bitte eine offizielle Quelle angeben."
                )
            })

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    """A menu listing. Mixed drinks and food may have no manufacturer."""

    group = models.ForeignKey(
        MenuGroup,
        on_delete=models.PROTECT,
        related_name="items",
        verbose_name="Menügruppe",
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="items",
        verbose_name="Marke / Hersteller",
        null=True,
        blank=True,
    )
    name = models.CharField(
        "Produktname / Sorte", max_length=180
    )
    production_location = models.CharField(
        "Herstellungsort laut Karte", max_length=160, blank=True
    )
    alcohol_percent = models.DecimalField(
        "Alkoholgehalt in %",
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
    )
    printed_note = models.TextField(
        "Beschreibung aus der Papierkarte", blank=True
    )
    geschmack_kurz = models.CharField(
        "Geschmack – Kurztext für die Karte",
        max_length=160,
        blank=True,
        help_text=(
            "Wenige Stichwörter für die kleine Produktkarte, z. B. "
            "Würzig · Pflaume · Marzipan. Nur geprüfte Angaben verwenden."
        ),
    )
    beschreibung = models.TextField(
        "Bierakademie-Beschreibung für Details",
        blank=True,
        help_text=(
            "Eigener Beschreibungstext in 2–3 Sätzen für die "
            "aufgeklappte Produktkarte."
        ),
    )
    official_description = models.TextField(
        "Produktbeschreibung laut Hersteller", blank=True
    )
    official_source_url = models.URLField(
        "Offizielle Produktquelle", max_length=500, blank=True
    )
    product_history = models.TextField(
        "Produktgeschichte (belegt)", blank=True
    )
    product_history_source_url = models.URLField(
        "Offizielle Quelle zur Produktgeschichte", max_length=500, blank=True
    )
    ingredients = models.TextField(
        "Zutaten / Speisenbeschreibung", blank=True
    )
    allergen_codes = models.CharField(
        "Allergenkennzeichnung", max_length=120, blank=True
    )
    additive_codes = models.CharField(
        "Zusatzstoffkennzeichnung", max_length=120, blank=True
    )
    image = models.ImageField(
        "Produktbild", upload_to="menu/products/", blank=True
    )
    is_new = models.BooleanField(
        "Neu im Sortiment",
        default=False,
        help_text=(
            "Neue Produkte stehen in einem eigenen Bereich oben und "
            "erscheinen nicht zusätzlich in ihrer regulären Gruppe."
        ),
    )
    sort_order = models.PositiveIntegerField("Reihenfolge", default=0)
    is_available = models.BooleanField("Verfügbar", default=True)
    is_published = models.BooleanField(
        "Auf Website anzeigen",
        default=False,
        help_text="Erst aktivieren, wenn die Angaben geprüft wurden.",
    )

    class Meta:
        verbose_name = "Menüposition"
        verbose_name_plural = "Menüpositionen"
        ordering = ("sort_order", "id")

    def clean(self):
        super().clean()
        errors = {}

        if self.official_description and not self.official_source_url:
            errors["official_source_url"] = (
                "Für die Herstellerbeschreibung bitte eine offizielle Quelle angeben."
            )

        if self.product_history and not self.product_history_source_url:
            errors["product_history_source_url"] = (
                "Für die Produktgeschichte bitte eine offizielle Quelle angeben."
            )

        if errors:
            raise ValidationError(errors)

    # Optimized WebP files are stored separately.
    # Original uploads remain unchanged.
    # No database migration is required.

    def _webp_name(self, variant):
        if not self.pk or not self.image:
            return ""

        version = sha256(
            self.image.name.encode("utf-8")
        ).hexdigest()[:12]

        return f"menu/webp/{self.pk}/{version}_{variant}.webp"

    def _webp_url(self, variant):
        if not self.image:
            return ""

        path = self._webp_name(variant)

        if path and self.image.storage.exists(path):
            return self.image.storage.url(path)

        # Original image is used if WebP is not ready.
        return self.image.url

    @property
    def image_card_url(self):
        return self._webp_url("card")

    @property
    def image_detail_url(self):
        return self._webp_url("detail")

    def generate_webp_variants(self, force=False):
        """
        Generate optimized copies for card and detail views.

        Card: maximum 900 x 900 px.
        Detail: maximum 1600 x 1600 px.

        The original image is never changed.
        Image proportions are preserved.
        """

        if not self.pk or not self.image:
            return False

        storage = self.image.storage

        variants = {
            "card": (900, 900),
            "detail": (1600, 1600),
        }

        pending = {
            name: bounds
            for name, bounds in variants.items()
            if force or not storage.exists(self._webp_name(name))
        }

        if not pending:
            return False

        with storage.open(self.image.name, "rb") as source_file:
            with Image.open(source_file) as opened:

                photo = ImageOps.exif_transpose(opened)

                # Transparent images receive a cream background.
                if (
                    "A" in photo.getbands()
                    or "transparency" in photo.info
                ):
                    transparent = photo.convert("RGBA")

                    backdrop = Image.new(
                        "RGBA",
                        photo.size,
                        "#faf7ef",
                    )

                    backdrop.alpha_composite(transparent)
                    photo = backdrop.convert("RGB")

                else:
                    photo = photo.convert("RGB")

                for variant, bounds in pending.items():

                    resized = photo.copy()

                    resized.thumbnail(
                        bounds,
                        Image.Resampling.LANCZOS,
                    )

                    output = BytesIO()

                    resized.save(
                        output,
                        format="WEBP",
                        quality=85,
                        method=4,
                    )

                    destination = self._webp_name(variant)

                    if storage.exists(destination):
                        storage.delete(destination)

                    storage.save(
                        destination,
                        ContentFile(output.getvalue()),
                    )

        return True

    def save(self, *args, **kwargs):
        """
        Automatically optimize a newly uploaded image.

        Editing other product information does not
        trigger another image conversion.
        """

        update_fields = kwargs.get("update_fields")

        can_update_image = (
            update_fields is None
            or "image" in update_fields
        )

        old_image = None

        if self.pk and can_update_image:
            old_image = (
                type(self)
                .objects
                .filter(pk=self.pk)
                .values_list("image", flat=True)
                .first()
            )

        current_image = (
            self.image.name if self.image else ""
        )

        needs_optimization = (
            can_update_image
            and bool(self.image)
            and (
                self._state.adding
                or not self.image._committed
                or old_image != current_image
            )
        )

        super().save(*args, **kwargs)

        if needs_optimization:
            try:
                self.generate_webp_variants(force=True)

            except Exception:
                # Never discard the original if conversion fails.
                logger.exception(
                    "WebP conversion failed for menu item %s",
                    self.pk,
                )

    def __str__(self):
        if self.brand_id:
            return f"{self.brand.name} — {self.name}"
        return self.name


class MenuPrice(models.Model):
    """One verified amount/price combination (0,33 l, 2 cl, portion...)."""

    item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="prices",
        verbose_name="Menüposition",
    )
    size_label = models.CharField(
        "Menge / Variante",
        max_length=60,
        help_text="Beispiele: 0,33 l; 0,5 l; 2 cl; 4 cl; Flasche 0,75 l; Portion.",
    )
    price_eur = models.DecimalField(
        "Preis in Euro",
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    sort_order = models.PositiveIntegerField("Reihenfolge", default=0)
    is_available = models.BooleanField("Verfügbar", default=True)

    class Meta:
        verbose_name = "Preisvariante"
        verbose_name_plural = "Preisvarianten"
        ordering = ("sort_order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("item", "size_label"),
                name="unique_menu_item_size_label",
            ),
        ]

    def __str__(self):
        return (
            f"{self.item} · "
            f"{self.size_label}: "
            f"{self.price_eur} €"
        )
