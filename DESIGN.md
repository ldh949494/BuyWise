---
name: BuyWise
description: A task-first AI shopping guide and catalog operations interface.
colors:
  primary: "#1f6f5b"
  primary-deep: "#185746"
  primary-soft: "#e3f2ea"
  secondary: "#245bff"
  secondary-soft: "#eaf1ff"
  accent: "#7c5a00"
  accent-soft: "#fff1cd"
  danger: "#a33a32"
  danger-soft: "#f6dedb"
  surface: "#f6f7f8"
  panel: "#ffffff"
  panel-alt: "#f6f7f8"
  ink: "#222222"
  muted: "#687174"
  border: "#d9dddf"
typography:
  headline:
    fontFamily: "ui-rounded, SF Pro Rounded, Nunito Sans, MiSans, HarmonyOS Sans SC, Microsoft YaHei UI, Segoe UI, ui-sans-serif, system-ui, sans-serif"
    fontSize: "28px"
    fontWeight: 760
    lineHeight: 1.2
    letterSpacing: "0"
  title:
    fontFamily: "ui-rounded, SF Pro Rounded, Nunito Sans, MiSans, HarmonyOS Sans SC, Microsoft YaHei UI, Segoe UI, ui-sans-serif, system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "0"
  body:
    fontFamily: "ui-rounded, SF Pro Rounded, Nunito Sans, MiSans, HarmonyOS Sans SC, Microsoft YaHei UI, Segoe UI, ui-sans-serif, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0"
  label:
    fontFamily: "ui-rounded, SF Pro Rounded, Nunito Sans, MiSans, HarmonyOS Sans SC, Microsoft YaHei UI, Segoe UI, ui-sans-serif, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 700
    lineHeight: 1.35
    letterSpacing: "0"
rounded:
  sm: "6px"
  md: "8px"
  lg: "12px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  xxl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.panel}"
    rounded: "{rounded.sm}"
    padding: "10px 14px"
  button-secondary:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.primary}"
    rounded: "{rounded.sm}"
    padding: "10px 14px"
  input:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "9px 11px"
  card:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "16px"
---

# Design System: BuyWise

## 1. Overview

**Creative North Star: "The Shopping Workbench"**

BuyWise is a product UI system for repeated shopping and operations tasks. It should feel calm, legible, and specific: a place where products, recommendation reasons, and readiness states are easier to compare than they were before.

The system is restrained by default. Color is used for action, selection, and status, while surfaces stay quiet and structured. It explicitly rejects SaaS landing-page theater, decorative AI glow, purple-blue gradient dashboards, glassmorphism, and oversized rounded cards.

**Key Characteristics:**
- Dense but readable product evidence.
- Shared state vocabulary across Android and web admin.
- Crisp borders and tonal surfaces instead of decorative shadows.
- Direct copy with action-oriented labels.

## 2. Colors

The palette is the original BuyWise product palette: catalog green for web admin action and selection, vivid blue for Android primary action, amber for commerce emphasis, and red for destructive or failing states.

### Primary
- **Catalog Green**: Used for web admin primary actions, selected navigation, focus, and high-confidence status.

### Secondary
- **Android Blue**: Used as the Android client's primary action color and for product-assistant emphasis.

### Tertiary
- **Commerce Amber**: Used for price, rating, and important shopping signals.

### Neutral
- **Cool Surface**: The default app background for both admin and mobile UI.
- **Panel White**: Main containers, cards, tables, and input backgrounds.
- **Readable Ink**: Primary text and data.
- **Operational Muted**: Secondary labels and helper copy.
- **Soft Border**: Structural dividers and control outlines.

### Named Rules

**The Evidence Color Rule.** Accent color must point to a real state, action, or shopping signal. It is not decoration.

## 3. Typography

**Display Font:** Rounded system sans stack
**Body Font:** Rounded system sans stack
**Label/Mono Font:** System sans; native monospace only for commands and code.

**Character:** A rounded system sans stack carries the product. Hierarchy comes from softer weights, generous line-height, spacing, and grouping, not decorative font changes.

### Hierarchy
- **Headline** (600, 28px, 1.28): Page titles and major mobile screen headings.
- **Title** (600-700, 18px, 1.35): Cards, panels, table group headings, and mobile section headers.
- **Body** (400, 14px, 1.55): Explanatory text, descriptions, and table cells.
- **Label** (700, 12px, 1.35): Form labels, table headers, chips, and compact metadata.

### Named Rules

**The Product Type Rule.** Do not use display typography in labels, buttons, data, or navigation.

## 4. Elevation

The system is flat by default. Depth is communicated through panel tone, border, spacing, and sticky surfaces. Shadows are reserved for overlays and floating affordances such as the Android compare basket or chat input bar.

### Shadow Vocabulary
- **Floating Action** (`0 10px 24px rgba(15, 118, 110, 0.18)`): Only for floating controls that must sit above content.

### Named Rules

**The Border Or Shadow Rule.** A component can use a border or a meaningful shadow, never a decorative pairing of both.

## 5. Components

### Buttons
- **Shape:** Compact rounded rectangle (6px on web, 12px or pill for native Material controls).
- **Primary:** Catalog Green background with white text on web admin; Android Blue for native primary controls.
- **Hover / Focus:** Subtle tonal shift and visible focus ring.
- **Secondary / Ghost:** White background, teal text, and a soft border.

### Chips
- **Style:** Tonal background with matching semantic text.
- **State:** Chips identify status or filters; they should not be used as decorative badges.

### Cards / Containers
- **Corner Style:** 8px on web panels, 12px on Android cards.
- **Background:** Panel White on Cool Surface.
- **Shadow Strategy:** Flat by default, border for structure.
- **Border:** Soft Border at 1px.
- **Internal Padding:** 16px to 24px depending on density.

### Inputs / Fields
- **Style:** White panel fill, soft border, 6px radius.
- **Focus:** Teal border with a visible, non-layout-shifting ring.
- **Error / Disabled:** Error uses red text on a soft red field. Disabled controls keep readable labels.

### Navigation
- **Style:** Top navigation on admin web and Material bottom navigation on Android. Active state uses primary teal and soft teal fill. Labels stay short and task-oriented.

## 6. Do's and Don'ts

### Do:
- **Do** keep admin tables dense and scannable.
- **Do** show product evidence before recommendation language.
- **Do** keep touch targets at least 44px on Android and mobile web.
- **Do** use borders and tonal surfaces as the default container language.

### Don't:
- **Don't** use SaaS landing-page theater.
- **Don't** add decorative AI glow.
- **Don't** use purple-blue gradient dashboards.
- **Don't** use glassmorphism.
- **Don't** use oversized rounded cards.
- **Don't** make the admin console look like a consumer storefront.
