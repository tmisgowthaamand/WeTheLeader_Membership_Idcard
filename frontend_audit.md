# Frontend Audit — We The Leaders v5.0
**Date:** June 8, 2026  
**Files Covered:** `templates/user/chatbot.html`, `templates/user/card.html`, `templates/user/verify.html`, `templates/admin/login.html`, `templates/admin/dashboard.html`, `templates/admin/voters.html`, `templates/base.html`

---

## 1. templates/user/chatbot.html — Line-by-Line Audit

### 1.1 Head / Meta Tags
- **OK** — `<meta charset="UTF-8">` and `<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5, user-scalable=yes">` present.
- **OK** — `maximum-scale=5` allows users to zoom manually — good accessibility practice.
- **FIXED (recent)** — Input font-size was `0.9rem` on mobile, now `1rem` — prevents iOS/Android auto-zoom on field focus.
- **OK** — Extensive SEO meta tags (`og:`, `twitter:`, structured data) — good for discoverability.
- **OK** — Canonical URL set to `https://www.wetheleaders.org/`.
- **OK** — `hreflang` alternate tags for English and Tamil locales.
- **NOTE:** `<link rel="apple-touch-icon" href="/static/banner.jpg">` — `banner.jpg` does not exist in `static/` (not listed in file tree). This will result in a 404 for Apple touch icon.

### 1.2 CSS — Chat App Container
- **OK** — `overflow: hidden` on `html, body` prevents unwanted scroll — intentional for full-screen chat UI.
- **OK** — `.chat-app` uses `max-height: 100dvh` — uses `dvh` (dynamic viewport height) unit which handles mobile browser chrome correctly.
- **NOTE:** `dvh` has ~92% browser support. No fallback for older browsers. Should have `max-height: 100vh` as fallback before `max-height: 100dvh`.

### 1.3 Chat Header CSS
- **OK** — `.chat-header` uses `#008069` (WhatsApp green) for brand consistency.
- **FIXED (recent)** — `.brand-name img` height increased from `46px` to `62px`.
- **OK** — `flex-shrink: 0` prevents header from shrinking under content pressure.
- **OK** — `padding: max(12px, env(safe-area-inset-top))` handles iPhone notch correctly.

### 1.4 Chat Messages CSS
- **OK** — `.chat-messages` uses `overflow-y: auto` — scrollable message area.
- **OK** — `padding: 20px 10%` gives generous side margins on desktop.
- **NOTE:** On very wide screens (>1400px), 10% padding means messages are constrained to center 80% — looks fine but `.message .bubble` max-width of 600px also limits bubble width.

### 1.5 Message Bubble CSS
- **OK** — `.message.bot .bubble` uses `rgba(255,255,255,0.65)` with `backdrop-filter: blur(10px)` — glassy effect.
- **NOTE:** `backdrop-filter` is not supported in all browsers (Firefox < 103). A solid fallback color should be set via the non-blur path.
- **OK** — `.bubble .time` uses `float: right` — works but is an older layout pattern. Flexbox would be more robust.

### 1.6 Input Area CSS
- **OK** — `.chat-input-area` uses `env(safe-area-inset-bottom)` for iPhone home indicator.
- **FIXED (recent)** — `.input-wrapper input` font-size changed from `0.95rem` to `1rem` (base).
- **FIXED (recent)** — Mobile override `@media (max-width: 600px)` also changed to `1rem` — fixes iOS zoom-on-focus.
- **NOTE:** `border-radius: 24px` on input field matches WhatsApp design aesthetic.

### 1.7 Dark Mode CSS
- **OK** — Dark mode classes cover all major components: header, bubbles, input area, sidebar.
- **NOTE:** Dark mode is toggled via JS adding `body.dark-mode`. Preference is stored in `localStorage`. Not using `prefers-color-scheme` media query — users who prefer system dark mode won't get it automatically.

### 1.8 Sidebar CSS
- **OK** — Sidebar slides from right, overlay darkens background.
- **OK** — `z-index: 100` for panel, `z-index: 99` for overlay — correct stacking.

### 1.9 HTML Body — Chat Header
```html
<div class="chat-header">
  <div class="avatar"><img src="/static/newfavicon.png" alt="Logo"></div>
  <div class="info" style="display: flex; align-items: center;">
    <img src="{{ url_for('static', filename='new-name-logo.png') }}" alt="We The Leaders"
      style="height: 62px; width: auto;">
  </div>
  <div class="actions" ...>
    <i class="bi bi-list" id="sidebarToggle" ...></i>
  </div>
</div>
```
- **OK** — Logo and name image in header.
- **NOTE:** Avatar `<img>` has no explicit `width`/`height` attributes — browser can't reserve space before image loads, causing layout shift (CLS). Should add `width="46" height="46"`.
- **NOTE:** Name logo `<img>` also missing `width` attribute — CLS risk.
- **ISSUE:** `<i class="bi bi-list" id="sidebarToggle">` — an icon used as interactive element has no accessible label (`aria-label`). Screen readers won't announce its purpose.

### 1.10 JavaScript — Chat Flow
- **NOTE:** The JS for the chatbot is extensive (likely 1000+ lines in the `<script>` block). Key points from visible sections:
- **OK** — OTP validation uses regex before API call.
- **OK** — Photo file type checked client-side before upload.
- **ISSUE:** Client-side face validation feedback shown before server response — UX is good, but ensure server always re-validates (it does — `validate_photo_for_id_card` runs server-side).
- **NOTE:** All fetch calls use vanilla JS, no error boundary for network failures beyond generic catch blocks.
- **ISSUE:** `localStorage` used for session data (PIN state, mobile number, voter name). If user opens incognito or clears storage, the chat state resets mid-flow. No server-side session recovery for chat state.
- **MISSING:** No loading state timeout. If the `/api/chat/generate-card` call takes >30s (e.g., Cloudinary slow), the user sees a spinner indefinitely. Should add a timeout with a user-friendly message.

---

## 2. templates/user/card.html — Line-by-Line Audit

### 2.1 Layout
- **OK** — Full page ID card view with 3D flip animation (front/back).
- **OK** — `perspective: 1200px` on `.flip-wrapper` — smooth 3D effect.
- **OK** — Aspect ratio `padding-top: 66.67%` (2:3) matches `1536×1024` card dimensions.
- **NOTE:** The flip is triggered by click. No keyboard trigger (e.g., `Enter`/`Space` on focus) — accessibility issue.

### 2.2 Download Button
- **OK** — Download uses `{{ url_for('user_download_card', epic_no=epic_no) }}` — server-side redirect to Cloudinary attachment URL.
- **NOTE:** The download button is only shown if the user has a valid session (the route checks `session['verified_mobile']`). If a user navigates directly to `/card/<epic_no>`, the flip and view work, but download would redirect to `401`. This is expected but not communicated to the user before they try.

### 2.3 Responsive Design
- **OK** — Bootstrap grid used for responsive layout.
- **NOTE:** Card template (1536×1024) is wide. On mobile screens <400px, the card text may be unreadably small even with CSS scaling.

---

## 3. templates/user/verify.html — Line-by-Line Audit

### 3.1 Head
- **OK** — `<meta name="robots" content="noindex, nofollow">` — correct, verification pages should not be indexed.
- **OK** — `<link rel="canonical" href="https://www.wetheleaders.org/">` — canonical points to home, not the verify URL itself. This is intentional to consolidate link equity.

### 3.2 Top Bar
- **OK** — `brand-name img` has `height: 26px` here (separate from chatbot.html, not updated to 62px). This is the verify page's own header — separate component, consistent with the verify page's overall smaller/lighter design.
- **NOTE:** Verify page `.top-bar .brand-name img` is `height: 26px` while chatbot header is `62px`. The discrepancy is intentional (different pages, different weight).

### 3.3 Verified Chip
- **OK** — `<i class="bi bi-patch-check-fill">` — clear verified indicator.
- **OK** — Animation `chipIn` with `0.5s ease-out` is smooth.

### 3.4 Profile Hero
- **OK** — Photo shown if `voter.photo_url` exists, placeholder icon otherwise.
- **OK** — Avatar ring with gradient border looks polished.
- **ISSUE:** `<img src="{{ voter.photo_url }}" alt="{{ voter.name }}">` — the `voter.photo_url` is a Cloudinary URL. If Cloudinary is down, the image fails silently. No `onerror` fallback.

### 3.5 Info Blocks
- **OK** — Information organized into logical blocks: Member Info, Relation Details, Electoral Details, Role Status, ID Card.
- **OK** — All optional fields guarded with `{% if voter.field %}` — no empty rows shown.
- **OK** — Auth mobile masked: only shows `****XXXX` format — correct privacy practice.

### 3.6 Card Preview
- **OK** — Card image hover scales `1.015` — subtle and smooth.
- **OK** — Download button points to `{{ url_for('user_download_card', epic_no=voter.epic_no) }}`.
- **ISSUE:** Download button on verify page is for anyone who scans the QR — not the card owner. Download would fail with `401` since the scanner is not authenticated. The button should be hidden or replaced with a "request from member" message for non-authenticated visitors.

---

## 4. templates/admin/login.html — Line-by-Line Audit

### 4.1 Left Panel
- **OK** — Animated ID card illustration with scan line effect is visually distinctive.
- **OK** — Particle animations add depth without being distracting.
- **OK** — Responsive: collapses to stacked layout on mobile.

### 4.2 Login Form
- **OK** — `autocomplete="off"` on form.
- **OK** — `autofocus` on username input.
- **OK** — Password visibility toggle with correct icon swap.

### 4.3 Remember Me — CRITICAL SECURITY ISSUE
```javascript
localStorage.setItem('adminRemember', JSON.stringify({
  u: uInput.value,
  p: pInput.value  // ← PLAINTEXT PASSWORD STORED IN localStorage
}));
```
- **CRITICAL:** The "Remember Me" feature stores the admin **password in plaintext in `localStorage`**. Any JavaScript running on the page (including XSS attacks) can read `localStorage.getItem('adminRemember')`. This completely undermines admin security. Should store only username, never password. Use a server-side remember-me token (signed cookie) instead.

### 4.4 Flash Messages
- **OK** — Flash messages styled correctly with category-based icons.
- **OK** — `alert-danger`, `alert-warning`, `alert-info` all handled.

---

## 5. templates/admin/dashboard.html — Line-by-Line Audit

### 5.1 Stats Cards
- **OK** — 8 stat cards covering: total voters, generated users, total generations, cloud cards, generated voters, referrals, volunteers, booth agents.
- **NOTE:** Labels refer to "MySQL" in the system status card, but the backend uses **MongoDB Atlas**. This is a copy-paste error from a previous MySQL version — misleading to operators.
- **NOTE:** `stats.mysql_size_mb` is referenced in the template but `_get_external_stats()` returns `db1_size_mb`/`db2_size_mb`, not `mysql_size_mb`. The initial render of this value would show blank/undefined.

### 5.2 External Stats Loading
- **OK** — Slow stats (Cloudinary credits, SMS balance, DB sizes) are loaded asynchronously after page render. Good performance pattern.
- **OK** — Cloudinary progress bar color changes based on usage percentage.
- **OK** — Error in fetch is silently caught — dashboard doesn't break if external stats fail.

### 5.3 Generation Rate Bar
- **OK** — Shows `(total_generated / total_voters) * 100` percentage with animated bar.
- **NOTE:** If `total_voters = 0`, the rate shows "N/A" — handled correctly.

---

## 6. templates/admin/voters.html — Line-by-Line Audit

### 6.1 Filter Bar
- **OK** — Search, assembly filter, district filter, per-page selector all present.
- **OK** — Debounced search input (400ms delay) — prevents excessive API calls.
- **OK** — Minimum 2-character search to avoid full-table scans.
- **OK** — Active filter badges with individual clear buttons.

### 6.2 Table Rendering (JavaScript)
- **OK** — `escHtml()` function used to escape voter data before injecting into DOM — XSS safe.
- **OK** — `highlight()` function marks matched text using `<mark>` tags.
- **OK** — `AbortController` used to cancel in-flight requests when user types quickly.
- **OK** — Client-side page cache (`pageCache`) for instant back/forward.
- **OK** — Skeleton rows shown while loading for perceived performance.

### 6.3 Pagination
- **OK** — Supports both cursor-based and page-based pagination.
- **NOTE:** Cursor-based pagination is built into the frontend but the backend `api_voters` endpoint returns `cursor_mode: False` and never sets `next_cursor`/`prev_cursor`. The cursor code path is dead on the frontend. Should be removed or activated.

### 6.4 EPIC Copy to Clipboard
- **OK** — `navigator.clipboard.writeText()` — modern clipboard API.
- **NOTE:** No fallback for browsers/contexts where clipboard API is unavailable (e.g., non-HTTPS, older browsers).

### 6.5 IST Timestamp Conversion
- **NOTE:** `toIST()` function is referenced in the voters table JS but not defined in `voters.html`. It must be defined in `base.html` or a shared script. If it's missing, `last_generated` would show as undefined or cause a JS error.

---

## 7. templates/base.html — Line-by-Line Audit

### 7.1 CSS Variables
- **OK** — Complete design token system: `--bg-root`, `--bg-surface`, `--brand`, `--font-display`, `--font-body`, etc.
- **ISSUE:** CSS `:root` block is duplicated identically (appears twice in the file). One copy should be removed — adds ~200 lines of dead CSS.

### 7.2 Sidebar
- **OK** — Fixed sidebar, 260px wide, sticky brand header.
- **OK** — Mobile: sidebar hidden off-screen (`transform: translateX(-100%)`), shown via `.show` class.
- **OK** — `.sidebar-overlay` blocks interaction when sidebar is open on mobile.

### 7.3 Top Bar
- **OK** — `backdrop-filter: blur(12px)` gives frosted-glass appearance.
- **OK** — `position: sticky; top: 0; z-index: 1020` — stays visible on scroll.

### 7.4 Component Styles
- **OK** — `stat-card`, `status-badge`, `gen-pill`, `voter-avatar`, `filter-bar` all well-defined.
- **ISSUE:** `.stat-card` icon colors are set inline (e.g., `style="background:#fff8e1; color:#f57f17;"`) rather than using CSS variables. Breaks dark mode theming.

---

## 8. Cross-Cutting Frontend Issues

### 8.1 Accessibility (WCAG)
- **ISSUE:** Interactive icons (`<i class="bi bi-list">`, sort icons, copy icons) have no `aria-label` or `role="button"`.
- **ISSUE:** Color alone used to indicate status (green = confirmed, amber = pending, red = rejected) — fails WCAG 1.4.1 (Use of Color). Should add text or icon alongside color.
- **ISSUE:** Admin table has no `<caption>` element — screen readers won't announce table purpose.
- **ISSUE:** Modal/overlay elements (admin voter detail panel) have no `role="dialog"` or `aria-modal="true"`.
- **NOTE:** Focus management not implemented for modals — keyboard users cannot Tab through modal content properly.

### 8.2 Performance
- **ISSUE:** Bootstrap Icons (`@1.11.3`) loaded via CDN on every page. No subsetting — the full icon font (250KB) is loaded even though each page uses ~20 icons.
- **ISSUE:** Google Fonts loaded on every page via two separate `<link>` tags (`Bricolage Grotesque + Sora` for admin, `Inter` for user pages). Should use `font-display: swap`.
- **OK** — Static assets have `Cache-Control: public, max-age=31536000, immutable` (set in `app.py`).
- **NOTE:** No Service Worker / PWA manifest for the user chatbot page. Users cannot add to home screen with a proper icon/name.

### 8.3 Security
- **CRITICAL:** `admin/login.html` stores plaintext password in `localStorage` under "Remember Me". (Detailed above.)
- **OK** — All user-entered data is escaped before DOM injection in admin tables (`escHtml()`).
- **OK** — Jinja2 templates auto-escape output by default (`{{ }}` syntax).
- **ISSUE:** `verify.html` download button is accessible to unauthenticated QR scanners but the download endpoint requires authentication — creates a confusing dead-end UX.

### 8.4 Mobile Responsiveness
- **OK** — All pages have responsive breakpoints.
- **OK** — `env(safe-area-inset-*)` used for iPhone notch/home bar on chatbot.
- **ISSUE:** `card.html` has no safe-area inset handling — card may be obscured by iPhone home bar.
- **NOTE:** `verify.html` content padding doesn't adjust for very small screens (320px width) — some text may overflow.

### 8.5 Browser Compatibility
- **NOTE:** `backdrop-filter` not supported in Firefox < 103. Used on chat bubbles, top bar, sidebar. Graceful degradation: elements become opaque instead of frosted — acceptable.
- **NOTE:** `100dvh` not supported in Safari < 15.4. Fallback to `100vh` should be added.
- **NOTE:** `CSS clip-path`, `CSS grid` — used correctly with broad support.
