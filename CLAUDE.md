# Marlyn Jewelry site

Static luxury jewelry showcase (Naga City). Reservation-only; no online checkout or delivery.

**Before changing any HTML, CSS or copy, read `DESIGN_GUIDELINES.md` and follow it.**

- Colors, fonts, spacing, motion live only in `css/tokens.css`. Do not hard-code hex values or font names elsewhere.
- Run `node scripts/check-style.mjs` after style changes; it must pass.
- Config (Messenger URL, branches, Instagram) is in `js/site.config.js`; products are in `data/products.json`.
- Never invent prices, karats, hours, phone numbers or policies. Prices are always "Price on request".
- Preview: `python -m http.server 5180` from this folder (ES modules need http, not file://).
