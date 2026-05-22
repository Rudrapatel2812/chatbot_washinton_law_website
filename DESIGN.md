# Washington Legal Chatbot — Design System

## Brand Identity
Professional, trustworthy, authoritative. Inspired by law firm and government websites.
Dark navy primary with clean white content areas. No playful elements.

## Colors

### Primary
- `--color-primary: #0A2540` — deep navy (main brand, headers, sidebar)
- `--color-primary-hover: #0D3063` — navy hover state
- `--color-accent: #1A56DB` — professional blue (links, buttons, focus)
- `--color-accent-hover: #1648C0` — accent hover

### Neutrals
- `--color-bg: #F8F9FA` — off-white page background
- `--color-surface: #FFFFFF` — card/panel background
- `--color-border: #E2E8F0` — subtle borders
- `--color-muted: #64748B` — muted text, placeholders
- `--color-text: #1E293B` — primary body text
- `--color-text-light: #475569` — secondary text

### Status
- `--color-success: #0D7A4E` — green
- `--color-warning: #B45309` — amber
- `--color-error: #B91C1C` — red
- `--color-info: #1A56DB` — same as accent

### Chat Bubbles
- User bubble bg: `#0A2540` (navy), text: `#FFFFFF`
- Assistant bubble bg: `#FFFFFF`, text: `#1E293B`, border: `#E2E8F0`

## Typography

- Font family: `'Inter', system-ui, sans-serif`
- Base size: `16px`
- Line height: `1.6`

| Use | Size | Weight |
|-----|------|--------|
| Page title | 24px | 700 |
| Section heading | 18px | 600 |
| Body | 16px | 400 |
| Small / caption | 14px | 400 |
| Label | 12px | 500 |

## Spacing
- Base unit: `4px`
- Component padding: `16px` / `24px`
- Section gap: `32px`
- Border radius: `8px` (cards), `6px` (inputs/buttons), `20px` (chat bubbles)

## Components

### Chat Input
- Full-width input bar pinned to bottom
- Rounded pill shape, border `--color-border`
- Send button in navy `--color-primary`
- Placeholder: "Ask a question about Washington State law..."

### Chat Bubble (User)
- Right-aligned, navy background, white text
- Max width 70%, border-radius 20px 20px 4px 20px

### Chat Bubble (Assistant)
- Left-aligned, white background, dark text, light border
- Max width 85%, border-radius 20px 20px 20px 4px
- Citations shown below as small navy tags

### Citation Tag
- Small pill: border `#1A56DB`, text `#1A56DB`, bg transparent
- On hover: bg `#EFF6FF`
- Links to official RCW source

### Sidebar
- Background: `--color-primary` (#0A2540)
- Text: white / `rgba(255,255,255,0.7)` for secondary
- Width: 260px
- Shows conversation history list

### Button (Primary)
- Background: `--color-accent` (#1A56DB)
- Text: white, font-weight 500
- Padding: 8px 16px, border-radius 6px

### Disclaimer Banner
- Thin bar at top or bottom of chat
- Background: `#FEF9C3`, text: `#92400E`
- Text: "This is legal information only, not legal advice."
