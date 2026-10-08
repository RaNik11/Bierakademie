
"use strict";

/* ==================================================
   BIERAKADEMIE
   GLOBAL SITE JAVASCRIPT

   1. Mobile Navigation
   2. Keyboard Accessibility
   3. Active Menu Categories
   4. Horizontal Category Scrolling
================================================== */

document.addEventListener("DOMContentLoaded", () => {
    setupMobileNavigation();
    setupMenuCategoryNavigation();
});


/* ==================================================
   MOBILE NAVIGATION
================================================== */

function setupMobileNavigation() {

    const menuToggle = document.querySelector(".menu-toggle");
    const mainNav = document.querySelector(".main-nav");

    if (!menuToggle || !mainNav) {
        return;
    }

    const desktopBreakpoint = 980;

    const navigationLinks = Array.from(
        mainNav.querySelectorAll("a[href]")
    );

    let previouslyFocusedElement = null;

    const isMenuOpen = () => {
        return menuToggle.getAttribute("aria-expanded") === "true";
    };

    const isMobileLayout = () => {
        return window.innerWidth <= desktopBreakpoint;
    };


    /* ----------------------------------------------
       OPEN MENU
    ---------------------------------------------- */

    const openMenu = () => {

        if (isMenuOpen() || !isMobileLayout()) {
            return;
        }

        previouslyFocusedElement = document.activeElement;

        menuToggle.setAttribute("aria-expanded", "true");
        menuToggle.setAttribute(
            "aria-label",
            "Navigation schließen"
        );

        menuToggle.classList.add("active");
        mainNav.classList.add("open");
        document.body.classList.add("menu-open");

        window.requestAnimationFrame(() => {

            if (!isMenuOpen()) {
                return;
            }

            const firstLink = navigationLinks[0];

            if (firstLink) {
                firstLink.focus();
            }

        });
    };


    /* ----------------------------------------------
       CLOSE MENU
    ---------------------------------------------- */

    const closeMenu = ({ returnFocus = false } = {}) => {

        if (!isMenuOpen()) {
            return;
        }

        menuToggle.setAttribute("aria-expanded", "false");
        menuToggle.setAttribute(
            "aria-label",
            "Navigation öffnen"
        );

        menuToggle.classList.remove("active");
        mainNav.classList.remove("open");
        document.body.classList.remove("menu-open");

        if (returnFocus) {

            const focusTarget =
                previouslyFocusedElement &&
                previouslyFocusedElement.isConnected
                    ? previouslyFocusedElement
                    : menuToggle;

            if (typeof focusTarget.focus === "function") {
                focusTarget.focus();
            }
        }

        previouslyFocusedElement = null;
    };


    /* ----------------------------------------------
       BURGER BUTTON
    ---------------------------------------------- */

    menuToggle.addEventListener("click", () => {

        if (isMenuOpen()) {
            closeMenu({ returnFocus: true });
        } else {
            openMenu();
        }

    });


    /* ----------------------------------------------
       NAVIGATION LINKS
    ---------------------------------------------- */

    navigationLinks.forEach((link) => {

        link.addEventListener("click", () => {
            closeMenu();
        });

    });


    /* ----------------------------------------------
       CLICK OUTSIDE
    ---------------------------------------------- */

    document.addEventListener("pointerdown", (event) => {

        if (!isMenuOpen()) {
            return;
        }

        if (
            mainNav.contains(event.target) ||
            menuToggle.contains(event.target)
        ) {
            return;
        }

        closeMenu();
    });


    /* ----------------------------------------------
       KEYBOARD CONTROLS
    ---------------------------------------------- */

    document.addEventListener("keydown", (event) => {

        if (!isMenuOpen()) {
            return;
        }

        /* Escape closes the menu */

        if (event.key === "Escape") {

            event.preventDefault();

            closeMenu({
                returnFocus: true
            });

            return;
        }

        /* Trap Tab focus in the open navigation */

        if (event.key !== "Tab") {
            return;
        }

        const focusableElements = [
            menuToggle,
            ...navigationLinks
        ].filter((element) => {

            return (
                !element.hasAttribute("disabled") &&
                element.getClientRects().length > 0
            );

        });

        if (focusableElements.length === 0) {
            return;
        }

        const firstElement = focusableElements[0];

        const lastElement =
            focusableElements[focusableElements.length - 1];

        const currentElement = document.activeElement;

        if (event.shiftKey) {

            if (
                currentElement === firstElement ||
                !focusableElements.includes(currentElement)
            ) {

                event.preventDefault();
                lastElement.focus();
            }

        } else {

            if (
                currentElement === lastElement ||
                !focusableElements.includes(currentElement)
            ) {

                event.preventDefault();
                firstElement.focus();
            }

        }

    });


    /* ----------------------------------------------
       DESKTOP RESIZE
    ---------------------------------------------- */

    window.addEventListener("resize", () => {

        if (
            !isMobileLayout() &&
            isMenuOpen()
        ) {

            closeMenu();
        }

    });


    /* ----------------------------------------------
       BROWSER BACK / FORWARD
    ---------------------------------------------- */

    window.addEventListener("pageshow", () => {

        menuToggle.setAttribute("aria-expanded", "false");

        menuToggle.setAttribute(
            "aria-label",
            "Navigation öffnen"
        );

        menuToggle.classList.remove("active");

        mainNav.classList.remove("open");

        document.body.classList.remove("menu-open");

        previouslyFocusedElement = null;
    });

}


/* ==================================================
   MENÜ CATEGORY NAVIGATION
================================================== */

function setupMenuCategoryNavigation() {

    const categoryNavigation =
        document.querySelector(".karte-categories");

    if (!categoryNavigation) {
        return;
    }

    const categoryLinks = Array.from(
        categoryNavigation.querySelectorAll("a[href^='#']")
    );

    if (categoryLinks.length === 0) {
        return;
    }


    /* ----------------------------------------------
       FIND CATEGORIES
    ---------------------------------------------- */

    const categoryItems = categoryLinks
        .map((link) => {

            const targetId = link
                .getAttribute("href")
                .slice(1)
                .trim();

            if (!targetId) {
                return null;
            }

            const section = document.getElementById(targetId);

            if (!section) {
                return null;
            }

            return {
                id: targetId,
                link,
                section
            };

        })
        .filter(Boolean);

    if (categoryItems.length === 0) {
        return;
    }


    const categoryNavigationInner =
        categoryNavigation.querySelector(
            ".karte-categories-inner"
        );

    const reducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    );

    let currentCategoryId = "";

    let scrollFrameRequested = false;


    /* ----------------------------------------------
       HORIZONTAL NAVIGATION SCROLL
    ---------------------------------------------- */

    const scrollCategoryIntoView = (link) => {

        if (!categoryNavigationInner) {
            return;
        }

        const container = categoryNavigationInner;

        if (container.scrollWidth <= container.clientWidth) {
            return;
        }

        const containerRect =
            container.getBoundingClientRect();

        const linkRect =
            link.getBoundingClientRect();

        const linkCenter =
            linkRect.left +
            linkRect.width / 2;

        const containerCenter =
            containerRect.left +
            containerRect.width / 2;

        const targetScrollLeft =
            container.scrollLeft +
            linkCenter -
            containerCenter;

        const maxScrollLeft =
            container.scrollWidth -
            container.clientWidth;

        const safeScrollLeft = Math.max(
            0,
            Math.min(targetScrollLeft, maxScrollLeft)
        );

        container.scrollTo({
            left: safeScrollLeft,
            behavior: reducedMotion.matches
                ? "auto"
                : "smooth"
        });

    };


    /* ----------------------------------------------
       ACTIVE CATEGORY
    ---------------------------------------------- */

    const setActiveCategory = (
        categoryId,
        { moveNavigation = true } = {}
    ) => {

        if (!categoryId) {
            return;
        }

        if (categoryId === currentCategoryId) {
            return;
        }

        currentCategoryId = categoryId;

        categoryItems.forEach((item) => {

            const isActive = item.id === categoryId;

            item.link.classList.toggle(
                "active",
                isActive
            );

            if (isActive) {

                item.link.setAttribute(
                    "aria-current",
                    "location"
                );

            } else {

                item.link.removeAttribute(
                    "aria-current"
                );
            }

        });

        if (!moveNavigation) {
            return;
        }

        const activeItem = categoryItems.find(
            (item) => item.id === categoryId
        );

        if (activeItem) {
            scrollCategoryIntoView(activeItem.link);
        }

    };


    /* ----------------------------------------------
       SECTION POSITION
    ---------------------------------------------- */

    const getDocumentTop = (element) => {

        return (
            element.getBoundingClientRect().top +
            window.scrollY
        );

    };


    /* ----------------------------------------------
       UPDATE CATEGORY ON SCROLL
    ---------------------------------------------- */

    const updateActiveCategory = () => {

        scrollFrameRequested = false;

        const navigationHeight =
            categoryNavigation.offsetHeight;

        const markerPosition =
            window.scrollY +
            navigationHeight +
            150;

        let activeItem = categoryItems[0];

        categoryItems.forEach((item) => {

            const sectionTop =
                getDocumentTop(item.section);

            if (sectionTop <= markerPosition) {
                activeItem = item;
            }

        });

        const reachedDocumentBottom =
            window.innerHeight +
            window.scrollY >=
            document.documentElement.scrollHeight - 4;

        if (reachedDocumentBottom) {

            activeItem =
                categoryItems[categoryItems.length - 1];
        }

        setActiveCategory(activeItem.id);

    };


    /* ----------------------------------------------
       THROTTLE WITH REQUEST ANIMATION FRAME
    ---------------------------------------------- */

    const requestCategoryUpdate = () => {

        if (scrollFrameRequested) {
            return;
        }

        scrollFrameRequested = true;

        window.requestAnimationFrame(
            updateActiveCategory
        );

    };


    /* ----------------------------------------------
       CATEGORY CLICK
    ---------------------------------------------- */

    categoryItems.forEach((item) => {

        item.link.addEventListener("click", () => {

            setActiveCategory(
                item.id,
                {
                    moveNavigation: false
                }
            );

        });

    });


    /* ----------------------------------------------
       SCROLL / RESIZE
    ---------------------------------------------- */

    window.addEventListener(
        "scroll",
        requestCategoryUpdate,
        {
            passive: true
        }
    );

    window.addEventListener(
        "resize",
        requestCategoryUpdate
    );


    /* ----------------------------------------------
       INITIAL CATEGORY
    ---------------------------------------------- */

    const initialHash =
        window.location.hash
            .slice(1)
            .trim();

    const matchingInitialItem =
        categoryItems.find(
            (item) => item.id === initialHash
        );

    if (matchingInitialItem) {

        setActiveCategory(
            matchingInitialItem.id,
            {
                moveNavigation: false
            }
        );

    } else {

        updateActiveCategory();
    }


    /* ----------------------------------------------
       BROWSER HASH CHANGES
    ---------------------------------------------- */

    window.addEventListener("hashchange", () => {

        const currentHash =
            window.location.hash
                .slice(1)
                .trim();

        const matchingItem =
            categoryItems.find(
                (item) => item.id === currentHash
            );

        if (matchingItem) {

            setActiveCategory(
                matchingItem.id,
                {
                    moveNavigation: false
                }
            );
        }

    });

}


/* ==================================================
   FUTURE DRINK DETAILS

   Drink detail interactions will be added when
   a real modal/dialog is implemented.

   Until then, ordinary drink cards remain
   non-interactive, so visitors do not encounter
   buttons that appear broken.
================================================== */
