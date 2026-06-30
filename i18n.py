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
        # homepage / landing
        "hero_title": "Professional websites, built from your brief",
        "app_sub": "Tell us about your project. We design your website and get "
                   "back to you within one business day.",
        "nav_start": "Get started",
        "home_cta": "Start your brief →",
        "how_title": "How it works",
        "how_1_t": "Share your brief",
        "how_1_d": "Answer a few quick questions about your business and the site you want.",
        "how_2_t": "We design it",
        "how_2_d": "Our team turns your brief into a polished, multi-page website.",
        "how_3_t": "Review & launch",
        "how_3_d": "We send it over, refine it together, and take it live.",
        # stepper
        "step_brief": "Brief",
        "step_contact": "Contact",
        "step_done": "Done",
        # brief step
        "form_title": "Tell us about your site",
        "form_sub": "A short brief — about a minute.",
        "optional": "optional",
        "continue_btn": "Continue →",
        "back_btn": "← Back",
        "err_generic": "Something went wrong. Please try again.",
        # contact step
        "contact_title": "How can we reach you?",
        "contact_sub": "We'll use this to send your website and follow up. "
                       "We reply within one business day.",
        "contact_name": "Your name",
        "contact_name_ph": "Jane Doe",
        "contact_email": "Email",
        "contact_email_ph": "you@example.com",
        "contact_phone": "Phone",
        "contact_phone_ph": "+49 …",
        "contact_message": "Anything else we should know?",
        "contact_message_ph": "Timeline, budget, examples you like …",
        "submit_btn": "Send my request →",
        # thank-you step
        "thanks_title": "Thank you — we've got your brief",
        "thanks_sub": "We'll review your project and get back to you within one business day.",
        "thanks_back": "Start another brief",
        # chrome
        "lang_label": "Language",
        "app_footer": "webgen · professional websites from your brief",
        # task labels — used by the (separate) generation engine, not the customer UI
        "task_read": "Read the brief",
        "task_choose": "Choose {n} design directions",
        "task_generate": "Generate the “{title}” concept",
        "task_package": "Package previews",
    },
    "de": {
        # homepage / landing
        "hero_title": "Professionelle Websites aus Ihrem Briefing",
        "app_sub": "Erzählen Sie uns von Ihrem Projekt. Wir gestalten Ihre Website "
                   "und melden uns innerhalb eines Werktags.",
        "nav_start": "Loslegen",
        "home_cta": "Briefing starten →",
        "how_title": "So funktioniert's",
        "how_1_t": "Briefing teilen",
        "how_1_d": "Beantworten Sie ein paar kurze Fragen zu Ihrem Unternehmen und der gewünschten Website.",
        "how_2_t": "Wir gestalten",
        "how_2_d": "Unser Team macht aus Ihrem Briefing eine ausgefeilte, mehrseitige Website.",
        "how_3_t": "Prüfen & live gehen",
        "how_3_d": "Wir senden sie Ihnen zu, verfeinern sie gemeinsam und schalten sie live.",
        # stepper
        "step_brief": "Briefing",
        "step_contact": "Kontakt",
        "step_done": "Fertig",
        # brief step
        "form_title": "Erzählen Sie uns von Ihrer Website",
        "form_sub": "Ein kurzes Briefing — etwa eine Minute.",
        "optional": "optional",
        "continue_btn": "Weiter →",
        "back_btn": "← Zurück",
        "err_generic": "Etwas ist schiefgelaufen. Bitte erneut versuchen.",
        # contact step
        "contact_title": "Wie erreichen wir Sie?",
        "contact_sub": "Damit senden wir Ihnen Ihre Website und melden uns. "
                       "Wir antworten innerhalb eines Werktags.",
        "contact_name": "Ihr Name",
        "contact_name_ph": "Max Mustermann",
        "contact_email": "E-Mail",
        "contact_email_ph": "sie@beispiel.de",
        "contact_phone": "Telefon",
        "contact_phone_ph": "+49 …",
        "contact_message": "Möchten Sie uns noch etwas mitteilen?",
        "contact_message_ph": "Zeitrahmen, Budget, Beispiele, die Ihnen gefallen …",
        "submit_btn": "Anfrage senden →",
        # thank-you step
        "thanks_title": "Vielen Dank — wir haben Ihr Briefing",
        "thanks_sub": "Wir sehen uns Ihr Projekt an und melden uns innerhalb eines Werktags.",
        "thanks_back": "Neues Briefing starten",
        # chrome
        "lang_label": "Sprache",
        "app_footer": "webgen · professionelle Websites aus Ihrem Briefing",
        # task labels — used by the (separate) generation engine, not the customer UI
        "task_read": "Briefing lesen",
        "task_choose": "{n} Design-Richtungen wählen",
        "task_generate": "Konzept „{title}“ erstellen",
        "task_package": "Vorschauen zusammenstellen",
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
