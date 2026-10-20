"""Regression tests for the Bierakademie menu redesign.

Run after migrations:
    python manage.py test website.tests.test_menu_redesign

These tests exercise Django data, access control, and rendered markup.
Responsive grid and interactive JS behavior need a browser check as well.
"""

from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from website.models import MenuCategory, MenuGroup, MenuItem, MenuPrice
from website.views import build_menu_sections, separate_new_items


class MenuRedesignTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = MenuCategory.objects.create(
            name="Bier", slug="bier", sort_order=1,
        )
        cls.group = MenuGroup.objects.create(
            category=cls.category, name="Helle Biere", sort_order=1,
        )
        cls.classic = MenuItem.objects.create(
            group=cls.group,
            name="Klassiker",
            alcohol_percent=Decimal("5.2"),
            is_published=True,
            is_available=True,
            sort_order=1,
        )
        cls.arrival = MenuItem.objects.create(
            group=cls.group,
            name="Neuheit",
            alcohol_percent=Decimal("4.8"),
            is_published=True,
            is_available=True,
            is_new=True,
            sort_order=2,
        )
        cls.draft = MenuItem.objects.create(
            group=cls.group,
            name="Unveroeffentlichter Entwurf",
            is_published=False,
            is_available=True,
            is_new=True,
            sort_order=3,
        )
        cls.unavailable = MenuItem.objects.create(
            group=cls.group,
            name="Derzeit Ausverkauft",
            is_published=True,
            is_available=False,
            sort_order=4,
        )
        MenuPrice.objects.create(
            item=cls.classic,
            size_label="0,5 l",
            price_eur=Decimal("4.50"),
            sort_order=1,
        )
        MenuPrice.objects.create(
            item=cls.classic,
            size_label="0,33 l",
            price_eur=Decimal("3.50"),
            is_available=False,
            sort_order=2,
        )
        MenuPrice.objects.create(
            item=cls.arrival,
            size_label="0,33 l",
            price_eur=Decimal("3.80"),
        )
        cls.staff = get_user_model().objects.create_user(
            username="bierakademie_staff_test",
            password="test-password-123",
            is_staff=True,
        )
        cls.customer = get_user_model().objects.create_user(
            username="bierakademie_customer_test",
            password="test-password-123",
        )

    @staticmethod
    def _all_regular_items(sections):
        return [
            item
            for section in sections
            for entry in section["groups"]
            for item in entry["items"]
        ]

    def test_new_arrivals_are_separate_and_not_duplicated(self):
        sections = build_menu_sections(include_unpublished=True)
        regular, new = separate_new_items(sections)

        self.assertEqual([item.name for item in new], [
            "Neuheit", "Unveroeffentlichter Entwurf",
        ])
        regular_names = [item.name for item in self._all_regular_items(regular)]
        self.assertEqual(regular_names, ["Klassiker", "Derzeit Ausverkauft"])
        self.assertFalse(set(item.pk for item in new) & set(
            item.pk for item in self._all_regular_items(regular)
        ))

    def test_public_data_excludes_drafts_and_unavailable_items(self):
        sections = build_menu_sections(include_unpublished=False)
        regular, new = separate_new_items(sections)

        self.assertEqual([item.name for item in new], ["Neuheit"])
        self.assertEqual(
            [item.name for item in self._all_regular_items(regular)],
            ["Klassiker"],
        )

    def test_unavailable_price_variant_is_hidden_from_public(self):
        public = build_menu_sections(include_unpublished=False)
        classic_public = next(
            item for item in self._all_regular_items(public)
            if item.pk == self.classic.pk
        )
        self.assertEqual(
            [price.size_label for price in classic_public.menu_prices],
            ["0,5 l"],
        )

        staff = build_menu_sections(include_unpublished=True)
        classic_staff = next(
            item for item in self._all_regular_items(staff)
            if item.pk == self.classic.pk
        )
        self.assertEqual(
            [price.size_label for price in classic_staff.menu_prices],
            ["0,5 l", "0,33 l"],
        )

    def test_hidden_categories_and_groups_are_excluded(self):
        hidden_category = MenuCategory.objects.create(
            name="Versteckt", slug="versteckt", is_visible=False,
        )
        hidden_group = MenuGroup.objects.create(
            name="Geheim", category=self.category, is_visible=False,
        )
        hidden_category_group = MenuGroup.objects.create(
            name="Versteckte Gruppe", category=hidden_category,
        )
        for group in (hidden_group, hidden_category_group):
            MenuItem.objects.create(
                group=group, name="Nicht zeigen", is_published=True,
            )

        sections = build_menu_sections(include_unpublished=True)
        self.assertEqual([s["category"].slug for s in sections], ["bier"])
        self.assertEqual(
            [entry["group"].name for entry in sections[0]["groups"]],
            ["Helle Biere"],
        )

    def test_preview_is_forbidden_to_guests_and_nonstaff(self):
        url = reverse("website:drinks_preview")
        alternate_url = reverse("website:drinks") + "?preview=1"

        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.get(alternate_url).status_code, 403)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.get(alternate_url).status_code, 403)

    def test_staff_preview_shows_prices_and_new_section(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("website:drinks_preview"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "website/drinks_preview.html")
        self.assertTrue(response.context["menu_preview"])
        self.assertEqual(response.context["menu_item_count"], 4)
        self.assertContains(response, 'id="neu"')
        self.assertContains(response, "0,33 l")
        self.assertContains(response, "Interner Entwurf")
        self.assertContains(response, 'data-menu-detail="menu-detail-')
        self.assertContains(response, 'aria-expanded="false"')
        self.assertEqual(
            response.content.decode().count(f'id="menu-detail-{self.arrival.pk}"'),
            1,
        )

    def test_staff_preview_query_parameter_works(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("website:drinks") + "?preview=1")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "website/drinks_preview.html")

    def test_public_remains_static_until_approved(self):
        with patch("website.views.ENABLE_DYNAMIC_PUBLIC_MENU", False):
            response = self.client.get(reverse("website:drinks"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "website/drinks.html")

    def test_dynamic_public_menu_only_shows_approved_items(self):
        with patch("website.views.ENABLE_DYNAMIC_PUBLIC_MENU", True):
            response = self.client.get(reverse("website:drinks"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "website/drinks_preview.html")
        self.assertFalse(response.context["menu_preview"])
        self.assertEqual(
            [item.name for item in response.context["new_items"]],
            ["Neuheit"],
        )
        self.assertContains(response, "Klassiker")
        self.assertNotContains(response, "Unveroeffentlichter Entwurf")
        self.assertNotContains(response, "Derzeit Ausverkauft")
        self.assertNotContains(response, "INTERNE MENÜ-VORSCHAU")

    def test_no_new_section_when_no_items_are_marked_new(self):
        MenuItem.objects.filter(is_new=True).update(is_new=False)
        regular, new = separate_new_items(
            build_menu_sections(include_unpublished=True)
        )
        self.assertEqual(new, [])
        self.assertEqual(len(self._all_regular_items(regular)), 4)
