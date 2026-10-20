"""
Safely link existing static beer photos to Bierakademie MenuItem.image.

Run from the directory containing manage.py:

    python link_menu_photos_v2.py

Preview only, no database changes.

    python link_menu_photos_v2.py --apply

Copy files and update verified matches.
"""

import argparse
import hashlib
from difflib import get_close_matches
import os
import re
import shutil
import unicodedata
from collections import Counter
from pathlib import Path


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

import django

django.setup()

from django.conf import settings
from website.models import MenuItem


# ============================================================
# PHOTO RULES
# ============================================================

# Each filename is mapped ONLY by specific product words.
#
# Alternatives use "+" to mean all words must be present.
#
# Typos in image filenames are deliberately kept exactly
# as they appear in static/img.


PHOTO_RULES = {

    "Augustiener Edelstoff.png": (
        "augustiner+edelstoff",
    ),

    "AventinusEisbock_Schneider.png": (
        "schneider+eisbock",
        "schneider+aventinus+eis",
    ),

    "Becks.png": (
        "becks+pils",
        "becks+original",
        "becks",
    ),

    "Becks_Alkfrei.png": (
        "becks+blue",
        "becks+alkoholfrei",
        "becks+alkfrei",
    ),

    "Benediktiner_Alkfrei.png": (
        "benediktiner+alkoholfrei",
        "benediktiner+alkfrei",
    ),

    "Benediktiner_Hell.png": (
        "benediktiner+hell",
    ),

    "Bitburger_Alkfrei.png": (
        "bitburger+alkoholfrei",
        "bitburger+alkfrei",
        "bitburger+0.0",
    ),

    "Camba_Blackschark.png": (
        "camba+blackshark",
        "camba+blackschark",
    ),

    "Desperados.png": (
        "desperados",
    ),

    "Diebels_Alt.png": (
        "diebels+alt",
    ),

    "DunkleWeisse_Hirsch.png": (
        "hirsch+dunk+weiss",
    ),

    "Erdinger_Dunkel.png": (
        "erdinger+dunk",
    ),

    "Erdinger_Weissbier.png": (
        "erdinger+weissbier",
        "erdinger+hefe",
    ),

    "Franziskaner Dunkel im gemütlichen Wirtshaus.png": (
        "franziskaner+dunk",
    ),

    "Freanyisskaner_Weissbier.png": (
        "franziskaner+hefe",
        "franziskaner+weiss",
    ),

    "Freising_Huber.png": (
        "huber+weiss",
        "huber+original",
    ),

    "GoldochsenOriginal_Flasche.png": (
        "goldochsen+original",
    ),

    "GoldstoffVollbier_Hirsch.png": (
        "hirsch+goldstoff",
    ),

    "Hilsenbecks_Schottenbock.png": (
        "schottenbock",
    ),

    "Hirsch_Privatbrauerei_Dunkle.png": (
        "hirsch+dunk",
    ),

    "HirschHellesMild.png": (
        "hirsch+helles",
        "hirsch+hell",
    ),

    "Hopfenweisse_Schneider.png": (
        "schneider+hopfen",
        "schneider+tap5",
    ),

    "ImperialIpa_Blackschark.png": (
        "camba+imperial+ipa",
    ),

    "Jever.png": (
        "jever",
    ),

    "KonigPilser.png": (
        "konig+pils",
    ),

    "MeiselKristal.png": (
        "maisel+kristall",
        "maisel+kristal",
    ),

    "NaturtrubesZwieckl_Hirsch.png": (
        "hirsch+zwickl",
    ),

    "NaturtrubGruibinger.png": (
        "brunnenbier",
        "gruibinger+naturtrub",
    ),

    "PaulanerHefeWeissbier.png": (
        "paulaner+hefe",
    ),

    "RothausZaepfle.png": (
        "rothaus+tannen",
        "rothaus+zapfle",
    ),

    "SalvatorDoppelbock_Paulaner.png": (
        "paulaner+salvator",
    ),

    "Sanwald_Kristal.png": (
        "sanwald+kristall",
        "sanwald+kristal",
    ),

    "Schneider Kristal_Tap2.png": (
        "schneider+tap2",
        "schneider+kristall",
    ),

    "SchneiderTap3_Alkfrei.png": (
        "schneider+tap3",
        "schneider+alkoholfrei",
        "schneider+alkfrei",
    ),

    "SchneiderTap7Weissbier.png": (
        "schneider+tap7",
        "schneider+original+weiss",
    ),

    "Weihenstephaner_Doppelbock.png": (
        "weihenstephaner+korbinian",
        "weihenstephaner+doppelbock",
    ),

    "Weihenstephaner_Kristal.png": (
        "weihenstephaner+kristall",
        "weihenstephaner+kristal",
    ),
}


# ============================================================
# FORBIDDEN WORDS
# ============================================================

# Prevent similarly named variants from being swapped.


FORBIDDEN_WORDS = {

    "Becks.png": (
        "blue",
        "alkoholfrei",
        "alkfrei",
    ),

    "Benediktiner_Hell.png": (
        "alkoholfrei",
        "alkfrei",
    ),

    "Erdinger_Weissbier.png": (
        "dunk",
        "alkoholfrei",
        "alkfrei",
    ),

    "Freanyisskaner_Weissbier.png": (
        "dunk",
        "alkoholfrei",
        "alkfrei",
    ),

    "Hirsch_Privatbrauerei_Dunkle.png": (
        "weiss",
    ),

    "SchneiderTap7Weissbier.png": (
        "helle",
        "kristall",
        "hopfen",
        "alkoholfrei",
        "eisbock",
    ),
}


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(value):

    value = str(value or "").lower().replace("ß", "ss")

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        ch
        for ch in value
        if not unicodedata.combining(ch)
    )

    return re.sub(
        r"[^a-z0-9]",
        "",
        value,
    )


# ============================================================
# PRODUCT MATCHING
# ============================================================

def is_match(fullname, filename):

    for forbidden in FORBIDDEN_WORDS.get(
        filename,
        (),
    ):

        if all(
            normalize(word) in fullname
            for word in forbidden.split("+")
        ):
            return False

    return any(
        all(
            normalize(word) in fullname
            for word in alternative.split("+")
        )
        for alternative in PHOTO_RULES[filename]
    )


# ============================================================
# FILE HASH
# ============================================================

def digest(path):

    result = hashlib.sha256()

    with path.open("rb") as stream:

        for chunk in iter(
            lambda: stream.read(1024 * 1024),
            b"",
        ):
            result.update(chunk)

    return result.hexdigest()


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=__doc__,
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Copy and link verified photos",
    )

    args = parser.parse_args()

    source_dir = (
        Path(settings.BASE_DIR)
        / "static"
        / "img"
    )

    target_dir = (
        Path(settings.MEDIA_ROOT)
        / "menu"
        / "products"
    )

    if not source_dir.is_dir():

        parser.error(
            f"Image directory does not exist: {source_dir}"
        )

    # --------------------------------------------------------
    # Load PNG files
    # --------------------------------------------------------

    photos = sorted(
        (
            p
            for p in source_dir.iterdir()
            if p.is_file()
            and p.suffix.lower() == ".png"
        ),
        key=lambda p: p.name.casefold(),
    )

    by_name = {}

    for photo in photos:

        by_name.setdefault(
            normalize(photo.name),
            [],
        ).append(photo)

    # --------------------------------------------------------
    # Load database products
    # --------------------------------------------------------

    items = list(
        MenuItem.objects.select_related(
            "brand",
            "group__category",
        )
    )

    print(
        "MODE:",
        "APPLY" if args.apply
        else "PREVIEW (no changes)",
    )

    print(
        "Database items:",
        len(items),
    )

    print(
        "PNG files in static/img:",
        len(photos),
    )

    print(
        "Defined photo rules:",
        len(PHOTO_RULES),
    )

    if not items:

        print(
            "No MenuItem records in the database. "
            "Nothing changed."
        )

        return

    # --------------------------------------------------------
    # Find matches
    # --------------------------------------------------------

    problems = []
    proposals = []

    for filename in PHOTO_RULES:

        possible_sources = by_name.get(
            normalize(filename),
            [],
        )

        if not possible_sources:

            suggestions = get_close_matches(
                normalize(filename),
                list(by_name),
                n=3,
                cutoff=0.62,
            )

            hints = ", ".join(
                p.name
                for name in suggestions
                for p in by_name[name]
            )

            detail = (
                f"; similar files: {hints}"
                if hints
                else ""
            )

            problems.append(
                f"[FILE MISSING] {filename}{detail}"
            )

            continue

        if len(possible_sources) != 1:

            problems.append(
                f"[DUPLICATE SOURCE] {filename} "
                f"({len(possible_sources)} matching paths)"
            )

            continue

        candidate_items = []

        for item in items:

            brand = (
                item.brand.name
                if item.brand_id
                else ""
            )

            fullname = normalize(
                f"{brand} {item.name}"
            )

            if is_match(fullname, filename):

                candidate_items.append(item)

        if len(candidate_items) == 0:

            problems.append(
                f"[NO DB MATCH] {filename}"
            )

        elif len(candidate_items) > 1:

            descriptions = "; ".join(
                (
                    f"#{item.pk} "
                    f"{(item.brand.name + ' ') if item.brand_id else ''}"
                    f"{item.name}"
                )
                for item in candidate_items
            )

            problems.append(
                f"[AMBIGUOUS] {filename} => {descriptions}"
            )

        else:

            proposals.append(
                (
                    possible_sources[0],
                    candidate_items[0],
                )
            )

    # --------------------------------------------------------
    # Prevent two photos linking to the same product
    # --------------------------------------------------------

    counts = Counter(
        item.pk
        for _, item in proposals
    )

    print("\n--- PHOTO MATCHES ---")

    ready = 0
    attached = 0

    for source, item in proposals:

        brand = (
            item.brand.name
            if item.brand_id
            else ""
        )

        label = (
            f"#{item.pk} {brand} {item.name}"
        ).strip()

        relative = (
            Path("menu/products")
            / source.name
        )

        destination = (
            target_dir
            / source.name
        )

        # One product cannot receive two automatic matches.

        if counts[item.pk] > 1:

            print(
                f"[CONFLICT - SKIPPED] "
                f"{source.name} => {label}"
            )

            continue

        # Never replace an existing product image.

        if item.image:

            print(
                f"[HAS IMAGE - SKIPPED] "
                f"{source.name} => {label} "
                f"({item.image.name})"
            )

            continue

        # Never overwrite a different existing file.

        if (
            destination.exists()
            and digest(source) != digest(destination)
        ):

            print(
                f"[TARGET DIFFERS - SKIPPED] "
                f"{source.name} => {label}"
            )

            continue

        ready += 1

        # Preview mode does not change the database.

        if not args.apply:

            print(
                f"[READY] {source.name} => {label}"
            )

            continue

        # ----------------------------------------------------
        # Apply mode
        # ----------------------------------------------------

        target_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not destination.exists():

            shutil.copy2(
                source,
                destination,
            )

        item.image.name = relative.as_posix()

        item.save(
            update_fields=["image"],
        )

        attached += 1

        print(
            f"[SAVED] {source.name} => {label}"
        )

    # --------------------------------------------------------
    # Print unresolved items
    # --------------------------------------------------------

    if problems:

        print(
            "\n--- ITEMS NEEDING REVIEW "
            "(never auto-attached) ---"
        )

        for warning in problems:

            print(warning)

    # --------------------------------------------------------
    # Print PNG files without rules
    # --------------------------------------------------------

    recognized = {
        normalize(name)
        for name in PHOTO_RULES
    }

    unmapped = [
        p.name
        for p in photos
        if normalize(p.name) not in recognized
    ]

    if unmapped:

        print(
            "\n--- PNG FILES WITHOUT RULE "
            "(not attached) ---"
        )

        for filename in unmapped:

            print(
                "[UNMAPPED]",
                filename,
            )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print(
        f"\nReady: {ready} | Attached now: {attached}"
    )

    if not args.apply:

        print(
            "Nothing was changed. "
            "Review these matches before running --apply."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()