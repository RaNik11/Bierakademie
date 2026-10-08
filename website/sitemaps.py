from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    protocol = "https"

    changefreq = "weekly"

    priority = 0.8


    def items(self):
        return [
            "website:home",
            "website:drinks",
            "website:about",
            "website:gallery",
            "website:contact",
        ]


    def location(self, item):
        return reverse(item)


    def priority(self, item):
        priorities = {
            "website:home": 1.0,
            "website:drinks": 0.9,
            "website:about": 0.8,
            "website:gallery": 0.7,
            "website:contact": 0.9,
        }

        return priorities.get(item, 0.8)


    def changefreq(self, item):
        frequencies = {
            "website:home": "weekly",
            "website:drinks": "weekly",
            "website:about": "monthly",
            "website:gallery": "monthly",
            "website:contact": "monthly",
        }

        return frequencies.get(item, "monthly")