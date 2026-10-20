from django.urls import path

from . import views


app_name = "website"

urlpatterns = [
    path("", views.home, name="home"),

    path("getraenke/", views.drinks, name="drinks"),

    path(
        "getraenke/vorschau/",
        views.drinks,
        name="drinks_preview",
    ),

    path("bierakademie/", views.about, name="about"),
    path("galerie/", views.gallery, name="gallery"),
    path("kontakt/", views.contact, name="contact"),
    path("impressum/", views.impressum, name="impressum"),
    path("datenschutz/", views.datenschutz, name="datenschutz"),

]