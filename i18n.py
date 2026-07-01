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
        "app_sub": "Tell us about your project. We design your website and "
                   "get back to you soon.",
        "nav_start": "Get started",
        "home_cta": "Start your brief",
        "see_how": "See how it works ›",
        "scroll_cue": "Scroll",
        # how it works (plain 1-2-3)
        "how_title": "How it works",
        "how_1_t": "Tell us about your business",
        "how_1_d": "A few simple questions — about a minute.",
        "how_2_t": "We build your website",
        "how_2_d": "Our team designs it for you. You don't do anything technical.",
        "how_3_t": "You look it over",
        "how_3_d": "We send it to you to review, then make it live.",
        "reassure": "Free and no obligation. No technical skills needed — we'll get back to you soon.",
        # stats / references — placeholder numbers, swap for real ones later
        "stat_1_n": "2,400+", "stat_1_l": "Websites delivered",
        "stat_2_n": "98%",    "stat_2_l": "Client satisfaction",
        "stat_3_n": "11 min",  "stat_3_l": "Average brief",
        "stat_4_n": "30+",    "stat_4_l": "Industries served",
        # showcase
        "show_title": "Built for your world",
        "show_1_t": "Cafés & retail",     "show_1_d": "Warm, inviting sites that fill tables and baskets.",
        "show_2_t": "Studios & agencies", "show_2_d": "Bold portfolios that let the work speak.",
        "show_3_t": "Clinics & care",     "show_3_d": "Calm, trustworthy sites that put people at ease.",
        "show_4_t": "Trades & services",  "show_4_d": "Straightforward sites that bring the calls in.",
        # closing cta
        "cta_title": "Your website starts with a brief.",
        "cta_sub": "Answer a few questions. We'll handle the rest and get back to you soon.",
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
        "begin_btn": "Let’s begin →",
        "wiz_count": "Question {n} of {total}",
        "part_label": "Part {n} of {total}",
        "err_generic": "Something went wrong. Please try again.",
        # contact step
        "contact_title": "How can we reach you?",
        "contact_sub": "We'll use this to reach you about your website. "
                       "We'll be in touch soon.",
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
        "thanks_sub": "We've got your brief — we'll get back to you soon.",
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
                   "und melden uns bald.",
        "nav_start": "Loslegen",
        "home_cta": "Briefing starten",
        "see_how": "So funktioniert's ›",
        "scroll_cue": "Scrollen",
        # So funktioniert's (einfach 1-2-3)
        "how_title": "So funktioniert's",
        "how_1_t": "Erzählen Sie von Ihrem Unternehmen",
        "how_1_d": "Ein paar einfache Fragen — etwa eine Minute.",
        "how_2_t": "Wir bauen Ihre Website",
        "how_2_d": "Unser Team gestaltet sie für Sie. Die Technik übernehmen wir.",
        "how_3_t": "Sie schauen sie sich an",
        "how_3_d": "Wir senden sie Ihnen zur Ansicht und schalten sie dann live.",
        "reassure": "Kostenlos und unverbindlich. Keine technischen Kenntnisse nötig — wir melden uns bald.",
        # Statistiken / Referenzen — Platzhalter, später ersetzen
        "stat_1_n": "2.400+", "stat_1_l": "Websites geliefert",
        "stat_2_n": "98 %",   "stat_2_l": "Kundenzufriedenheit",
        "stat_3_n": "11 Min",  "stat_3_l": "Briefing im Schnitt",
        "stat_4_n": "30+",    "stat_4_l": "Branchen betreut",
        # Showcase
        "show_title": "Für Ihre Welt gemacht",
        "show_1_t": "Cafés & Handel",      "show_1_d": "Einladende Seiten, die Tische und Körbe füllen.",
        "show_2_t": "Studios & Agenturen", "show_2_d": "Starke Portfolios, die die Arbeit sprechen lassen.",
        "show_3_t": "Praxen & Pflege",     "show_3_d": "Ruhige, vertrauensvolle Seiten, die Sicherheit geben.",
        "show_4_t": "Handwerk & Dienste",  "show_4_d": "Klare Seiten, die für Anfragen sorgen.",
        # Abschluss-CTA
        "cta_title": "Ihre Website beginnt mit einem Briefing.",
        "cta_sub": "Beantworten Sie ein paar Fragen. Den Rest übernehmen wir — wir melden uns bald.",
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
        "begin_btn": "Los geht's →",
        "wiz_count": "Frage {n} von {total}",
        "part_label": "Teil {n} von {total}",
        "err_generic": "Etwas ist schiefgelaufen. Bitte erneut versuchen.",
        # contact step
        "contact_title": "Wie erreichen wir Sie?",
        "contact_sub": "Damit erreichen wir Sie zu Ihrer Website. "
                       "Wir melden uns bald.",
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
        "thanks_sub": "Wir haben Ihr Briefing — wir melden uns bald.",
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
        "name": ("What's your business called?", "e.g. Nordlicht Café"),
        "business_type": ("What kind of business are you?", ""),
        "offerings": ("What do you offer? (your main products or services)",
                      "e.g. Fresh coffee, homemade cakes, breakfast, small catering"),
        "audience": ("Who are your customers? (pick any)", ""),
        "strengths": ("What makes you special? (pick any)", ""),
        "area": ("Where are your customers based?", ""),
        "years": ("How long have you been in business?", ""),
        "goal": ("What should your website do for you? (pick any)", ""),
        "pages": ("Which pages would you like? (pick any)", ""),
        "features": ("Any special features? (pick any, or skip)", ""),
        "feel": ("How should your website feel?", ""),
        "imagery": ("What should stand out most?", ""),
        "logo": ("Do you already have a logo?", ""),
        "example": ("A website whose look you like? (optional)",
                    "Paste a link, e.g. www.example.com"),
        "motion": ("How much movement should your website have?", ""),
        "intensity": ("Calm or bold?", ""),
        "colors": ("Which colours feel right?", ""),
        "theme": ("Light or dark?", ""),
    },
    "de": {
        "name": ("Wie heißt Ihr Unternehmen?", "z. B. Nordlicht Café"),
        "business_type": ("Was für ein Unternehmen sind Sie?", ""),
        "offerings": ("Was bieten Sie an? (Ihre wichtigsten Produkte oder Leistungen)",
                      "z. B. Frischer Kaffee, hausgemachte Kuchen, Frühstück, kleines Catering"),
        "audience": ("Wer sind Ihre Kunden? (beliebig wählen)", ""),
        "strengths": ("Was macht Sie besonders? (beliebig wählen)", ""),
        "area": ("Wo sind Ihre Kunden zu Hause?", ""),
        "years": ("Wie lange gibt es Ihr Unternehmen schon?", ""),
        "goal": ("Was soll Ihre Website für Sie tun? (beliebig wählen)", ""),
        "pages": ("Welche Seiten möchten Sie? (beliebig wählen)", ""),
        "features": ("Besondere Funktionen? (beliebig wählen oder überspringen)", ""),
        "feel": ("Wie soll sich Ihre Website anfühlen?", ""),
        "imagery": ("Was soll am meisten auffallen?", ""),
        "logo": ("Haben Sie schon ein Logo?", ""),
        "example": ("Eine Website, deren Look Ihnen gefällt? (optional)",
                    "Link einfügen, z. B. www.beispiel.de"),
        "motion": ("Wie viel Bewegung soll Ihre Website haben?", ""),
        "intensity": ("Ruhig oder auffällig?", ""),
        "colors": ("Welche Farben passen für Sie?", ""),
        "theme": ("Hell oder dunkel?", ""),
    },
}

# --------------------------------------------------------------------------
# Question groups (the wizard shows these as "parts")
# --------------------------------------------------------------------------
GROUPS = {
    "en": {"you": "About you", "website": "Your website",
           "look": "Overall look", "dynamic": "Dynamic", "color": "Colours"},
    "de": {"you": "Über Sie", "website": "Ihre Website",
           "look": "Aussehen", "dynamic": "Dynamik", "color": "Farben"},
}

# Chapters — the three top-level parts of the brief. Groups roll up into these,
# and the wizard shows a divider screen when a new chapter begins.
GROUP_CHAPTER = {"you": "about", "website": "site",
                 "look": "design", "dynamic": "design", "color": "design"}
CHAPTER_ORDER = ["about", "site", "design"]
CHAPTERS = {
    "en": {
        "about": ("About you", "First, a little about you and your business."),
        "site": ("Your website", "Now — what your website should do for you."),
        "design": ("The design", "Finally, how it should look and feel."),
    },
    "de": {
        "about": ("Über Sie", "Zuerst etwas über Sie und Ihr Unternehmen."),
        "site": ("Ihre Website", "Nun — was Ihre Website für Sie tun soll."),
        "design": ("Das Design", "Zum Schluss: Aussehen und Wirkung."),
    },
}

# --------------------------------------------------------------------------
# Option labels: question id -> value key -> label
# --------------------------------------------------------------------------
OPTIONS = {
    "en": {
        "business_type": {"food": "Restaurant or café", "shop": "Shop or store",
                          "trade": "Trade or craft", "health": "Health or care",
                          "beauty": "Beauty or wellness", "professional": "Professional service",
                          "other": "Something else"},
        "area": {"local": "My local area", "region": "My region",
                 "country": "My whole country", "online": "Online — everywhere"},
        "years": {"new": "Just getting started", "few": "A few years",
                  "ten": "More than 10 years", "twentyfive": "More than 25 years"},
        "goal": {"calls": "Bring in phone calls", "bookings": "Take bookings or appointments",
                 "show": "Show what I offer", "sell": "Sell products online",
                 "visit": "Get people to visit me", "inform": "Share information & build trust"},
        "audience": {"families": "Families", "young": "Young adults", "older": "Older adults",
                     "locals": "Local residents", "tourists": "Tourists & visitors",
                     "business": "Other businesses", "everyone": "Everyone"},
        "strengths": {"price": "Great value / fair prices", "quality": "Top quality",
                      "service": "Friendly, personal service", "experience": "Experience & expertise",
                      "reliability": "Reliable & on time", "local": "Local & trusted",
                      "choice": "Big choice / selection"},
        "pages": {"home": "Home", "about": "About us", "services": "Services / Menu",
                  "gallery": "Photo gallery", "pricing": "Prices", "reviews": "Reviews",
                  "contact": "Contact"},
        "features": {"booking": "Online booking", "contactform": "Contact form",
                     "map": "Map & directions", "gallery": "Photo gallery",
                     "reviews": "Customer reviews", "shop": "Online shop",
                     "newsletter": "Newsletter sign-up"},
        "feel": {"warm": "Warm & friendly", "professional": "Professional & trustworthy",
                 "modern": "Modern & clean", "classic": "Classic & elegant"},
        "imagery": {"photos": "Big photos", "text": "Clean, clear text",
                    "graphics": "Illustrations & graphics", "mix": "A balanced mix"},
        "motion": {"still": "Calm — barely any movement", "gentle": "Gentle, smooth movement",
                   "lively": "Lively & animated"},
        "intensity": {"calm": "Calm & understated", "balanced": "Balanced",
                      "bold": "Bold & striking"},
        "colors": {"blue": "Calm blues", "green": "Fresh greens",
                   "warm": "Warm reds & oranges", "elegant": "Elegant black & gold",
                   "neutral": "Soft & neutral", "designer": "Let the designer choose"},
        "theme": {"light": "Bright & light", "dark": "Dark & dramatic",
                  "auto": "Let the designer choose"},
        "logo": {"have": "Yes, I have one", "need": "No, I need one", "unsure": "Not sure"},
    },
    "de": {
        "business_type": {"food": "Restaurant oder Café", "shop": "Laden oder Geschäft",
                          "trade": "Handwerk", "health": "Gesundheit oder Pflege",
                          "beauty": "Beauty oder Wellness", "professional": "Dienstleistung",
                          "other": "Etwas anderes"},
        "area": {"local": "Meine Umgebung", "region": "Meine Region",
                 "country": "Landesweit", "online": "Online — überall"},
        "years": {"new": "Ganz frisch dabei", "few": "Ein paar Jahre",
                  "ten": "Über 10 Jahre", "twentyfive": "Über 25 Jahre"},
        "goal": {"calls": "Anrufe gewinnen", "bookings": "Termine/Buchungen erhalten",
                 "show": "Zeigen, was ich anbiete", "sell": "Produkte online verkaufen",
                 "visit": "Besucher ins Geschäft holen", "inform": "Informieren & Vertrauen aufbauen"},
        "audience": {"families": "Familien", "young": "Junge Erwachsene", "older": "Ältere Menschen",
                     "locals": "Menschen aus der Umgebung", "tourists": "Touristen & Besucher",
                     "business": "Andere Unternehmen", "everyone": "Alle"},
        "strengths": {"price": "Gutes Preis-Leistungs-Verhältnis", "quality": "Top-Qualität",
                      "service": "Freundlicher, persönlicher Service", "experience": "Erfahrung & Kompetenz",
                      "reliability": "Zuverlässig & pünktlich", "local": "Lokal & vertrauenswürdig",
                      "choice": "Große Auswahl"},
        "pages": {"home": "Startseite", "about": "Über uns", "services": "Leistungen / Speisekarte",
                  "gallery": "Fotogalerie", "pricing": "Preise", "reviews": "Bewertungen",
                  "contact": "Kontakt"},
        "features": {"booking": "Online-Buchung", "contactform": "Kontaktformular",
                     "map": "Karte & Anfahrt", "gallery": "Fotogalerie",
                     "reviews": "Kundenbewertungen", "shop": "Online-Shop",
                     "newsletter": "Newsletter-Anmeldung"},
        "feel": {"warm": "Warm & freundlich", "professional": "Professionell & seriös",
                 "modern": "Modern & klar", "classic": "Klassisch & elegant"},
        "imagery": {"photos": "Große Fotos", "text": "Klarer, aufgeräumter Text",
                    "graphics": "Illustrationen & Grafiken", "mix": "Eine ausgewogene Mischung"},
        "motion": {"still": "Ruhig — kaum Bewegung", "gentle": "Sanfte, weiche Bewegung",
                   "lively": "Lebendig & animiert"},
        "intensity": {"calm": "Ruhig & dezent", "balanced": "Ausgewogen",
                      "bold": "Auffällig & markant"},
        "colors": {"blue": "Ruhige Blautöne", "green": "Frisches Grün",
                   "warm": "Warme Rot- & Orangetöne", "elegant": "Elegantes Schwarz & Gold",
                   "neutral": "Sanft & neutral", "designer": "Der Designer entscheidet"},
        "theme": {"light": "Hell & freundlich", "dark": "Dunkel & edel",
                  "auto": "Der Designer entscheidet"},
        "logo": {"have": "Ja, habe ich", "need": "Nein, brauche ich", "unsure": "Bin nicht sicher"},
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


def group_label(key: str, lang: str) -> str:
    return GROUPS.get(lang, GROUPS[DEFAULT_LANG]).get(key, key)


def chapters_list(lang: str) -> list:
    """Ordered [{key, title, sub}] for the wizard's chapter dividers."""
    m = CHAPTERS.get(lang, CHAPTERS[DEFAULT_LANG])
    return [{"key": k, "title": m[k][0], "sub": m[k][1]} for k in CHAPTER_ORDER]


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
            "group": q.get("group", ""),
            "group_label": group_label(q.get("group", ""), lang),
            "chapter": GROUP_CHAPTER.get(q.get("group", ""), ""),
        }
        if "options" in q:
            labels = omap.get(q["id"], {})
            item["options"] = [
                {"value": v, "label": labels.get(v, v)} for v in q["options"]
            ]
        out.append(item)
    return out
