
"use strict";

/* Inline product details for Bierakademie.
   Only one detail panel exists, and it sits below its row of cards.
   No modal windows, overlays, third-party libraries, or masonry calculations. */

document.addEventListener("DOMContentLoaded", () => {
    const catalogue = document.getElementById("menu-preview-catalog");
    if (!catalogue) return;

    let activeTrigger = null;
    let activePanel = null;
    let resizeFrame = 0;

    function selectedGrid() {
        return activeTrigger ? activeTrigger.closest("[data-menu-grid]") : null;
    }

    function positionPanel() {
        const grid = selectedGrid();
        if (!grid || !activePanel) return;

        // Always use the same CSS breakpoint value as the actual layout.
        const columns = Math.max(1, parseInt(
            window.getComputedStyle(grid).getPropertyValue("--menu-columns"), 10
        ) || 4);

        const cards = Array.from(grid.children).filter(
            element => element.matches(".menu-drink-card")
        );
        const selectedIndex = cards.indexOf(activeTrigger);
        if (selectedIndex < 0) return;

        const finalCard = cards[Math.min(
            cards.length - 1,
            Math.ceil((selectedIndex + 1) / columns) * columns - 1
        )];
        finalCard.after(activePanel);
    }

    function closeDetails({ restoreFocus = false } = {}) {
        if (!activeTrigger || !activePanel) return;

        const previousTrigger = activeTrigger;
        previousTrigger.setAttribute("aria-expanded", "false");
        previousTrigger.classList.remove("is-selected");
        activePanel.remove();
        activePanel = null;
        activeTrigger = null;

        if (restoreFocus && previousTrigger.isConnected) {
            previousTrigger.focus({ preventScroll: true });
        }
    }

    function openDetails(trigger) {
        if (trigger === activeTrigger) {
            closeDetails({ restoreFocus: true });
            return;
        }

        const templateId = trigger.getAttribute("data-menu-detail");
        const template = templateId && document.getElementById(templateId);
        if (!(template instanceof HTMLTemplateElement)) return;

        closeDetails();

        const panel = document.createElement("section");
        panel.className = "menu-expanded-panel";
        panel.id = trigger.getAttribute("aria-controls");
        panel.setAttribute("role", "region");
        panel.setAttribute("aria-label", trigger.getAttribute("aria-label") || "Produktdetails");
        panel.setAttribute("tabindex", "-1");

        const closeButton = document.createElement("button");
        closeButton.type = "button";
        closeButton.className = "menu-expanded-close";
        closeButton.setAttribute("aria-label", "Produktdetails schließen");
        closeButton.textContent = "×";
        closeButton.addEventListener("click", () => closeDetails({ restoreFocus: true }));

        panel.appendChild(closeButton);
        panel.appendChild(template.content.cloneNode(true));
        activeTrigger = trigger;
        activePanel = panel;
        trigger.setAttribute("aria-expanded", "true");
        trigger.classList.add("is-selected");
        positionPanel();

        // On narrow screens, reveal the beginning of details without a modal.
        if (window.matchMedia("(max-width: 550px)").matches) {
            window.requestAnimationFrame(() => {
                if (activePanel !== panel) return;
                const bounds = panel.getBoundingClientRect();
                if (bounds.top >= window.innerHeight - 65) {
                    panel.scrollIntoView({
                        block: "start",
                        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
                            ? "auto" : "smooth"
                    });
                }
            });
        }
    }

    catalogue.addEventListener("click", event => {
        if (!(event.target instanceof Element)) return;
        const trigger = event.target.closest("button[data-menu-detail]");
        if (!trigger || !catalogue.contains(trigger)) return;
        openDetails(trigger);
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape" && activePanel) {
            event.preventDefault();
            closeDetails({ restoreFocus: true });
        }
    });

    window.addEventListener("resize", () => {
        if (!activePanel || resizeFrame) return;
        resizeFrame = window.requestAnimationFrame(() => {
            resizeFrame = 0;
            positionPanel();
        });
    }, { passive: true });
});
