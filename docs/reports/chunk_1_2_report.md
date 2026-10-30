# Chunk 1.2 — Landing Page and Cinematic Background

**Repository:** `parthiv-doraswamy/ShadowLens`  
**Branch:** `main`  
**Scope:** Public-facing product landing page and CSS-only visual atmosphere. This chunk does not add backend integrations or imply live monitoring.

## Implemented
- Replaced the root bootstrap screen with a responsive ShadowLens landing page.
- Added restrained cinematic atmosphere using local CSS gradients, a subtle grid, and an animated orbital signal illustration. No remote stock imagery, external fonts, video, or image requests are required.
- Added navigation to Platform, Visibility model, Principles, and the existing design-system preview.
- Added product capability sections for discovery, sensitive-data detection, and explainable risk.
- Explained T1 observed metadata, T2 inferred behaviour, and T3 authorized plaintext separately.
- Explicitly labelled the hero visualization as illustrative, not live data; described source/permission/platform limitations.
- Added privacy and trust principles: no claims of encrypted-body inspection, no raw secret/prompt persistence by default, deterministic findings remain authoritative, and local-first least-privilege collection.
- Added Playwright coverage for page content, anchor navigation, design-system navigation, and visibility/privacy copy.
- Preserved the `/design-system` route.

## Design and accessibility
- Uses existing Obsidian / Warm Paper / Deep Forest / Muted Amber design tokens.
- Responsive desktop and mobile layouts; semantic landmarks and navigation labels; reduced-motion handling; visible focus inherited from the design system.
- The orbital diagram is decorative and hidden from assistive technology; equivalent status labels are provided in text.
- No remote visual assets or tracking calls are introduced.

## Boundaries
- The visual is a static illustration, not a live telemetry panel.
- No demo metrics, API calls, user tracking, authentication, or collection functionality was added.
- No TLS MITM/decryption or passive HTTPS body inspection is claimed.

## Validation
- CI runs frontend typecheck, production build, and Playwright smoke tests; results must be checked on the final commit before marking this chunk verified.
