from django.shortcuts import render


def home(request):
    return render(request, "website/home.html")


def drinks(request):
    return render(request, "website/drinks.html")


def about(request):
    return render(request, "website/about.html")


def gallery(request):
    return render(request, "website/gallery.html")


def contact(request):
    return render(request, "website/contact.html")