
"use strict";

/* Immediate local preview of a selected menu photo in Django Admin.
   Does not upload, save, or modify the original image. */

document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("id_image");
    const preview = document.querySelector("[data-ba-image-preview]");
    if (!input || !preview) return;

    let temporaryUrl = null;

    input.addEventListener("change", () => {
        if (temporaryUrl) URL.revokeObjectURL(temporaryUrl);
        temporaryUrl = null;

        const file = input.files && input.files[0];
        if (!file || !file.type.startsWith("image/")) return;

        temporaryUrl = URL.createObjectURL(file);
        let image = preview.querySelector("img");
        if (!image) {
            image = document.createElement("img");
            image.alt = "Vorschau der ausgewählten Datei";
            preview.prepend(image);
        }
        image.src = temporaryUrl;
        const caption = preview.querySelector("span");
        if (caption) caption.textContent = "Neue Datei: " + file.name + " (noch nicht gespeichert)";
        preview.classList.remove("ba-image-preview--empty");
    });

    window.addEventListener("pagehide", () => {
        if (temporaryUrl) URL.revokeObjectURL(temporaryUrl);
    });
});
