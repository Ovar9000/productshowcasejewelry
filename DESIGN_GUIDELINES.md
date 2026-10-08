# Marlyn Jewelry — Design Guidelines

Single source of truth for look, feel and voice. If a rule here conflicts with a quick idea, the rule wins.
Values live in `css/tokens.css`; this file explains **how and when** to use them. Never restate a hex value or
font name in any other CSS/JS file — reference the token.

## 1. Brand in one line

Marlyn Jewelry, Naga City, **since 1988** (formerly Jaeum Silver and Gold). Quiet, confident, warm. The gold is the
star; everything else steps back. Think a bright white gallery with one piece under the light, not a flash sale.

Logo: white script “M” on black (`assets/img/brand/logo.jpg`), shown as a black circular badge on the white page. Use as-is. Never recolor, stretch, outline, add
effects, or recreate in a font. Minimum 40px tall. Keep clear space equal to the M's width on all sides.

## 2. Principles

1. **White lets gold glow.** Surfaces are white and near-white; gold appears only as accent, never as a large fill.
2. **One focal point per screen.** One product, one headline, one action.
3. **Restraint over decoration.** No gradients on surfaces, no drop-shadows on text, no emoji, no stock icons.
4. **Slow, weighted motion.** Movement should feel like turning a piece in your hand, not a web animation.
5. **Phone first.** Most Bicol visitors arrive from Facebook on a phone. Design at 390px wide, then scale up.

## 3. Color

Tokens in `css/tokens.css`. Use **only** these.

| Token | Role | Use |
|---|---|---|
| `--paper` | Page background (white) | Default surface |
| `--paper-raised` | Cards, raised sections, header on scroll | One step off the page |
| `--line` | Hairlines, dividers, card borders | 1px only |
| `--ink` | Primary text | Headings, body |
| `--ink-muted` | Secondary text | Captions, meta, labels. Never for body paragraphs under 16px |
| `--gold` | Accent fills and lines | Hairlines, focus ring, the one primary CTA fill, active chip border |
| `--gold-deep` | Accent **text** | Eyebrow labels, italic emphasis, links. Gold text on white must be this token for contrast |
| `--gold-bright` | Highlights | Hover state of gold fills only |

Rules
- Text is always `--ink` or `--ink-muted`. **Never pure `#000`.** The page itself is pure white (`--paper`) on purpose.
- Gold *text* is always `--gold-deep` (the lighter `--gold` fails contrast on white), only at ≥ 14px and only for labels, numerals or links. Never gold body paragraphs.
- Max **one** gold-filled button per viewport (ink text on gold). Secondary actions are outlined (gold hairline, ink text).
- No colors outside the table. No blues, no reds (errors use ink + a text message, not red).
- Contrast: ink on paper must stay ≥ 7:1; muted on paper and `--gold-deep` on paper ≥ 4.5:1. Check before changing a token.

## 4. Typography

Two families, loaded from Google Fonts. Nothing else.

| Role | Family | Weights | Token |
|---|---|---|---|
| Display / headings | **Cormorant Garamond** | 400, 500, italic 400 | `--font-display` |
| UI / body / labels | **Jost** | 300, 400, 500 | `--font-ui` |

Scale (fluid, defined as tokens `--step--1` … `--step-5`)

| Use | Token | Notes |
|---|---|---|
| Hero statement | `--step-5` | Display, 400, line-height 1.02, letter-spacing -0.01em |
| Section title | `--step-4` | Display, 400, line-height 1.08 |
| Sub-heading / card title | `--step-2` | Display, 500, line-height 1.2 |
| Body | `--step-0` | UI, 400, line-height 1.65, max-width 62ch |
| Label / eyebrow | `--step--1` | UI, 500, UPPERCASE, letter-spacing 0.22em, `--gold-deep` |

Rules
- Headings are sentence case. Only eyebrow labels are uppercase.
- Italic Cormorant is allowed for **one emphasised word or phrase** per heading, not whole headings.
- No bold (700+) anywhere. Hierarchy comes from size, family and color.
- Never use system fonts or a third family. Fallbacks in the token only: `Georgia, serif` / `system-ui, sans-serif`.
- Numerals in prices/dates use `font-variant-numeric: lining-nums`.

## 5. Layout and spacing

- 8px base grid. Spacing tokens `--space-1` … `--space-9` only; no ad-hoc px margins.
- Content max width `--content-max` (1200px); text blocks `--measure` (62ch).
- Side gutter: 20px on phone, 40px tablet, 64px desktop (`--gutter`).
- Sections breathe: vertical padding `--space-8` phone / `--space-9` desktop. Generous empty space is the luxury cue.
- Radius: `--radius` 2px for images and cards, 999px only for pill filter chips. No rounded-corner cards.
- Borders are 1px `--line`. No shadows except the soft ambient glow token `--glow` behind a lit product.
- Grid: 2 columns on phone, 3 on tablet, 4 on desktop for the catalog.

## 6. Imagery

Product photos
- Catalog photos keep their neutral studio backdrop, normalised to one tone by `scripts/process-photos.py`, sitting on the white
  page inside a hairline frame. Never put a photo with a grey/white backdrop on a gold or tinted surface.
- Crop 3:4 portrait in catalog cards (`aspect-ratio: 3/4; object-fit: cover`). Keep the piece centered.
- Do not apply filters, saturation boosts or color overlays to gold. Accuracy builds trust.
- Every image has descriptive `alt` text (what it is, not “image of”).
- Filenames: `kind-descriptor.jpg` (e.g. `ring-hearts.jpg`), lowercase, hyphenated.

3D / showcase
- The showcase is a **pre-rendered image sequence** on a canvas (`js/hero-seq.js`), frames in `assets/frames/ring/`
  as transparent WebP so the page background (and its morph) shows behind the piece. No real-time 3D in the browser.
- Frames come from `scripts/blender/ring_scene.py` (placeholder ring) or real turntable photos via
  `scripts/encode-frames.py`. Swapping the source must not require layout code changes.
- The hero piece stands on a white studio floor with one soft contact shadow, lit by softboxes with black flags for
  crisp reflections. No saturated colored lights, no bloom/glow, no particles, no lens flares.
- Gold reads as polished 22k–24k: warm, high metalness, low roughness. Do not exaggerate yellow.
- Background morph: glow position/warmth and the two hairline rings follow scroll progress, using only
  `--glow-wash`, `--glow-deep` and `--line`. Keep it slow and subtle; never add new colors for it.
- No “scroll” prompts, arrows or hint text. The motion should invite scrolling on its own.

## 7. Motion

Tokens: `--ease` `cubic-bezier(0.22, 0.61, 0.36, 1)`, `--dur-1` 200ms, `--dur-2` 450ms, `--dur-3` 900ms.

- Reveal on scroll: fade + 16px upward translate, `--dur-3`, once only. No bounces, no overshoot, no spin-ins.
- Hover: opacity/color/border changes in `--dur-1`. No scale-up of cards.
- Scroll-driven 3D uses eased progress (inertia), never raw scroll position.
- **Always honor `prefers-reduced-motion: reduce`**: show static poses, no pinned scroll, no parallax.
- Pause rendering when the canvas is off-screen or the tab is hidden.

## 8. Components

**Header**: logo left, 3 text links right (Collection, Branches, Reserve). Transparent over hero, becomes
`--paper-raised` with a `--line` bottom border after scroll. On phone: logo + a single “Reserve” text link.

**Primary button** (“Reserve on Messenger”): `--gold` fill, `--ink` text, UI 500, uppercase 0.16em, 14px, height 48px,
padding 0 28px, radius 2px. **Secondary**: transparent, 1px gold border, ink text.

**Catalog card**: image (3:4) → category eyebrow → name (Display `--step-2`) → “Price on request” (muted) →
text link “Reserve”. No badges, no stars, no “sale”.

**Filter chips**: pill, 1px `--line`, muted text; active = gold border + ink text.

**Branch card**: eyebrow “Branch”, mall name (Display), floor line, optional hours/phone **only when provided**.

**Focus**: 2px `--gold` outline, 3px offset, on every interactive element. Never remove outlines.

## 9. Voice and copy

- English, with a warm local feel. Short sentences. No hype words (“amazing”, “best”, “limited time”, “deal”).
- Say what is true: since 1988, three branches in Naga, reserve and view in person.
- Prices: always **“Price on request”**. Never show or imply a price, karat or gram weight unless the owner supplies it.
- Do not invent policies (hold duration, deposits, warranties, return terms). If unknown, leave out or mark `TODO(owner)`.
- Calls to action: “Reserve on Messenger”, “Visit a branch”, “View collection”.
- Delivery is **not offered online**. Everything is reserve → confirm on Messenger → view and collect in person.

## 10. Content facts (verified from owner material)

- Name: Marlyn Jewelry · Since 1988 · Formerly Jaeum Silver and Gold
- Branches: 1st Floor Yashano Mall (Diversion Road, Naga) · 1st Floor 101 Mall · 1st Floor Naga City People's Mall
- Instagram: @marlynjewelry_
- Contact: Messenger only (URL pending → `js/site.config.js`). No phone numbers, hours or email yet.

Everything configurable (Messenger URL, branches, Instagram) lives in `js/site.config.js`. Never hard-code
these in HTML.

## 11. Data and catalog

Products live in `data/products.json`. One object per piece: `id`, `name`, `category`, `images[]`, `alt`,
`price: null` (null renders “Price on request”), `available: true`. Add or edit entries there only — no edits to
HTML to add a product. Categories: `Rings`, `Bracelets`, `Necklaces`, `Earrings`.

Future: Meta Graph API pulls Facebook posts → writes `data/products.json` → redeploy (static site). Keep the schema
stable so the importer can target it.

## 12. Accessibility and performance (non-negotiable)

- Semantic landmarks (`header`, `main`, `section`, `footer`), one `h1`, ordered headings.
- Keyboard reachable, visible focus, 44×44px minimum touch targets.
- Images `loading="lazy"` except above the fold; explicit `width`/`height` or `aspect-ratio` to prevent shift.
- 3D canvas has a text/static-image fallback if WebGL is unavailable.
- Target: LCP < 2.5s on mid-range phone over 4G; initial JS < 200KB excluding three.js (lazy-load three.js).

## 13. Before you ship a change — checklist

- [ ] Only tokens used (run `node scripts/check-style.mjs`; it must pass)
- [ ] Only Cormorant Garamond + Jost; no bold
- [ ] ≤ 1 gold-filled button in view; gold text only for labels/links
- [ ] Looks right at 390px and 1440px
- [ ] Reduced-motion tested
- [ ] No invented facts, prices or policies
