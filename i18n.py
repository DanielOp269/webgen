"""Translations and language detection.

Everything the customer can read lives here in every supported language:
the UI chrome (`UI`), the question + option labels (`Q`, `OPTIONS`), and the
generated-site copy (`SITE`). The rest of the app refers to choices by stable
*value keys* (e.g. "modern", "friendly", "home") and looks up the display label
here, so translating a label never changes program logic.

Adding a language = add one entry to each of UI / Q / OPTIONS / SITE / LANG_NAMES.
This module imports nothing from the package, so others can import it freely.
"""

from __future__ import annotations

LANGS = ["en", "de"]
DEFAULT_LANG = "en"

LANG_NAMES = {"en": "English", "de": "Deutsch"}


def norm_lang(code: str | None) -> str:
    """Normalize an arbitrary code ("de-DE", "DE", None) to a supported lang."""
    if not code:
        return DEFAULT_LANG
    primary = code.split(",")[0].split(";")[0].split("-")[0].strip().lower()
    return primary if primary in LANGS else DEFAULT_LANG


def from_accept_language(header: str | None) -> str:
    """Pick the first supported language from an Accept-Language header."""
    if not header:
        return DEFAULT_LANG
    for item in header.split(","):
        code = item.split(";")[0].strip()
        primary = code.split("-")[0].lower()
        if primary in LANGS:
            return primary
    return DEFAULT_LANG


# --------------------------------------------------------------------------
# UI chrome (the questionnaire app itself)
# --------------------------------------------------------------------------
UI = {
    "en": {
        "app_sub": "Answer a few questions — our agent drafts three concepts for you to choose from.",
        "hero_title": "Professional websites, built from your brief",
        "step_brief": "Brief",
        "step_generate": "Generate",
        "step_choose": "Choose",
        "form_title": "Tell us about your site",
        "form_sub": "A short brief — about a minute.",
        "optional": "optional",
        "generate_btn": "Generate concepts →",
        "err_generic": "Something went wrong. Please try again.",
        "work_title": "Generating your concepts",
        "work_sub": "Our agent is working through the brief. This usually takes a few seconds.",
        "engine_label": "engine",
        "task_read": "Read the brief",
        "task_choose": "Choose {n} design directions",
        "task_generate": "Generate the “{title}” concept",
        "task_package": "Package previews",
        "pick_title": "Review your concepts",
        "pick_sub": "Preview each one, switch between pages, then select or download.",
        "open_full": "Open full",
        "download_zip": "Download",
        "choose_this": "Select",
        "selected": "Selected",
        "lang_label": "Language",
        "app_footer": "webgen · automated website generation",
    },
    "de": {
        "app_sub": "Beantworten Sie ein paar Fragen — unser Agent erstellt drei Konzepte zur Auswahl.",
        "hero_title": "Professionelle Websites aus Ihrem Briefing",
        "step_brief": "Briefing",
        "step_generate": "Erstellen",
        "step_choose": "Auswählen",
        "form_title": "Erzählen Sie uns von Ihrer Website",
        "form_sub": "Ein kurzes Briefing — etwa eine Minute.",
        "optional": "optional",
        "generate_btn": "Konzepte erstellen →",
        "err_generic": "Etwas ist schiefgelaufen. Bitte erneut versuchen.",
        "work_title": "Ihre Konzepte werden erstellt",
        "work_sub": "Unser Agent arbeitet das Briefing ab. Das dauert meist nur wenige Sekunden.",
        "engine_label": "Engine",
        "task_read": "Briefing lesen",
        "task_choose": "{n} Design-Richtungen wählen",
        "task_generate": "Konzept „{title}“ erstellen",
        "task_package": "Vorschauen zusammenstellen",
        "pick_title": "Ihre Konzepte im Überblick",
        "pick_sub": "Vorschau ansehen, zwischen Seiten wechseln, dann auswählen oder herunterladen.",
        "open_full": "Öffnen",
        "download_zip": "Herunterladen",
        "choose_this": "Auswählen",
        "selected": "Ausgewählt",
        "lang_label": "Sprache",
        "app_footer": "webgen · automatisierte Website-Erstellung",
    },
}

# --------------------------------------------------------------------------
# Question labels + placeholders, keyed by question id
# --------------------------------------------------------------------------
Q = {
    "en": {
        "name": ("Business / project name", "e.g. Nordlicht Studio"),
        "tagline": ("Tagline or one-liner (optional)", "e.g. Design that feels like home"),
        "industry": ("What do you do? A sentence or two.",
                     "We design calm, modern interiors for small cafés and shops."),
        "pages": ("Which pages do you want?", ""),
        "style": ("Overall vibe", ""),
        "tone": ("Tone of the writing", ""),
        "color": ("Preferred accent color (optional)", ""),
        "cta": ("Main call to action", "e.g. Book a consultation"),
        "services": ("List your main services / offerings (one per line)",
                     "Interior design\nColor consulting\nFurniture sourcing"),
    },
    "de": {
        "name": ("Name des Unternehmens / Projekts", "z. B. Nordlicht Studio"),
        "tagline": ("Slogan oder Einzeiler (optional)", "z. B. Design, das sich wie Zuhause anfühlt"),
        "industry": ("Was machen Sie? Ein, zwei Sätze.",
                     "Wir gestalten ruhige, moderne Innenräume für kleine Cafés und Geschäfte."),
        "pages": ("Welche Seiten möchten Sie?", ""),
        "style": ("Gesamtstil", ""),
        "tone": ("Tonalität der Texte", ""),
        "color": ("Bevorzugte Akzentfarbe (optional)", ""),
        "cta": ("Wichtigster Handlungsaufruf", "z. B. Beratung buchen"),
        "services": ("Ihre wichtigsten Leistungen / Angebote (eine pro Zeile)",
                     "Innenarchitektur\nFarbberatung\nMöbelbeschaffung"),
    },
}

# --------------------------------------------------------------------------
# Option labels: question id -> value key -> label
# --------------------------------------------------------------------------
OPTIONS = {
    "en": {
        "pages": {"home": "Home", "about": "About", "services": "Services",
                  "portfolio": "Portfolio", "pricing": "Pricing", "contact": "Contact"},
        "style": {"modern": "Modern & minimal", "bold": "Bold & vibrant",
                  "elegant": "Elegant & classic", "surprise": "One of each"},
        "tone": {"friendly": "Friendly", "professional": "Professional",
                 "luxury": "Luxury", "playful": "Playful"},
    },
    "de": {
        "pages": {"home": "Startseite", "about": "Über uns", "services": "Leistungen",
                  "portfolio": "Portfolio", "pricing": "Preise", "contact": "Kontakt"},
        "style": {"modern": "Modern & minimalistisch", "bold": "Auffällig & lebendig",
                  "elegant": "Elegant & klassisch", "surprise": "Von jedem eins"},
        "tone": {"friendly": "Freundlich", "professional": "Professionell",
                 "luxury": "Luxuriös", "playful": "Verspielt"},
    },
}

# --------------------------------------------------------------------------
# Generated-site copy (rendered into the customer's actual website)
# --------------------------------------------------------------------------
SITE = {
    "en": {
        "default_cta": "Get in touch",
        "directions": {
            "modern": ("Modern & Minimal",
                       "Generous whitespace, a clean sans-serif, one confident accent."),
            "bold": ("Bold & Vibrant", "Strong typography, a gradient hero, high contrast."),
            "elegant": ("Elegant & Classic",
                        "Refined serif headings, a muted palette, a timeless feel."),
        },
        "tone": {
            "friendly": "Let's talk about your goals",
            "professional": "Let's discuss your project",
            "luxury": "Request a private consultation",
            "playful": "Let's get started",
        },
        "fallback_services": ["Strategy & consultation", "Design & planning",
                              "Delivery & support"],
        "features_eyebrow": "Capabilities",
        "features_h2": "What we deliver",
        "service_blurb": "{s} — delivered to a professional standard, scoped to your requirements.",
        "band_p": "Tell us about your project and we'll respond within one business day.",
        "about_eyebrow": "About",
        "about_h2": "About {name}",
        "about_p2": ("We focus on doing a few things exceptionally well. Every engagement "
                     "begins with understanding your objectives and ends with results you "
                     "can measure."),
        "services_eyebrow": "Services",
        "services_h2": "How we can help",
        "portfolio_eyebrow": "Portfolio",
        "portfolio_h2": "Selected work",
        "pricing_eyebrow": "Pricing",
        "pricing_h2": "Transparent pricing",
        "pricing_tiers": ["Starter", "Professional", "Enterprise"],
        "pricing_card_p": "A package scoped to your needs.",
        "contact_eyebrow": "Contact",
        "contact_lead": "Get in touch and we'll respond within one business day.",
        "form_name": "Your name",
        "form_email": "Email",
        "form_msg": "How can we help?",
        "footer_rights": "All rights reserved.",
    },
    "de": {
        "default_cta": "Kontakt aufnehmen",
        "directions": {
            "modern": ("Modern & Minimalistisch",
                       "Großzügiger Weißraum, klare serifenlose Schrift, ein klarer Akzent."),
            "bold": ("Auffällig & Lebendig",
                     "Markante Typografie, ein Verlaufs-Hero, starker Kontrast."),
            "elegant": ("Elegant & Klassisch",
                        "Edle Serifenüberschriften, gedämpfte Palette, zeitlos."),
        },
        "tone": {
            "friendly": "Sprechen wir über Ihre Ziele",
            "professional": "Besprechen wir Ihr Projekt",
            "luxury": "Vereinbaren Sie eine persönliche Beratung",
            "playful": "Legen wir los",
        },
        "fallback_services": ["Strategie & Beratung", "Konzept & Planung",
                              "Umsetzung & Support"],
        "features_eyebrow": "Leistungsspektrum",
        "features_h2": "Was wir liefern",
        "service_blurb": "{s} — auf professionellem Niveau umgesetzt, zugeschnitten auf Ihre Anforderungen.",
        "band_p": "Erzählen Sie uns von Ihrem Projekt — wir antworten innerhalb eines Werktags.",
        "about_eyebrow": "Über uns",
        "about_h2": "Über {name}",
        "about_p2": ("Wir konzentrieren uns darauf, wenige Dinge außergewöhnlich gut zu machen. "
                     "Jede Zusammenarbeit beginnt mit dem Verständnis Ihrer Ziele und endet mit "
                     "messbaren Ergebnissen."),
        "services_eyebrow": "Leistungen",
        "services_h2": "Wie wir unterstützen",
        "portfolio_eyebrow": "Referenzen",
        "portfolio_h2": "Ausgewählte Projekte",
        "pricing_eyebrow": "Preise",
        "pricing_h2": "Transparente Preise",
        "pricing_tiers": ["Starter", "Professional", "Enterprise"],
        "pricing_card_p": "Ein Paket, das zu Ihrem Bedarf passt.",
        "contact_eyebrow": "Kontakt",
        "contact_lead": "Nehmen Sie Kontakt auf — wir antworten innerhalb eines Werktags.",
        "form_name": "Ihr Name",
        "form_email": "E-Mail",
        "form_msg": "Wie können wir helfen?",
        "footer_rights": "Alle Rechte vorbehalten.",
    },
}


# --------------------------------------------------------------------------
# Accessors
# --------------------------------------------------------------------------

def ui(lang: str) -> dict:
    return UI.get(lang, UI[DEFAULT_LANG])


def site(lang: str) -> dict:
    return SITE.get(lang, SITE[DEFAULT_LANG])


def question_label(qid: str, lang: str) -> str:
    return Q.get(lang, Q[DEFAULT_LANG]).get(qid, (qid, ""))[0]


def direction_label(key: str, lang: str) -> tuple[str, str]:
    return site(lang)["directions"].get(key, (key, ""))


def page_label(key: str, lang: str) -> str:
    return OPTIONS.get(lang, OPTIONS[DEFAULT_LANG])["pages"].get(key, key.title())


def localized_questions(questions: list, lang: str) -> list:
    """Turn the structural QUESTIONS into a display schema for the frontend.

    `questions` is brief.QUESTIONS (ids, types, value-key options). The result
    carries localized label/placeholder and, for choice types, options as
    [{value, label}] pairs so the frontend shows labels but submits value keys.
    """
    qmap = Q.get(lang, Q[DEFAULT_LANG])
    omap = OPTIONS.get(lang, OPTIONS[DEFAULT_LANG])
    out = []
    for q in questions:
        label, placeholder = qmap.get(q["id"], (q["id"], ""))
        item = {
            "id": q["id"],
            "type": q["type"],
            "required": q.get("required", False),
            "label": label,
            "placeholder": placeholder,
            "default": q.get("default", ""),
        }
        if "options" in q:
            labels = omap.get(q["id"], {})
            item["options"] = [
                {"value": v, "label": labels.get(v, v)} for v in q["options"]
            ]
        out.append(item)
    return out
