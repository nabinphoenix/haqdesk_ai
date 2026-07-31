# HaqDesk AI Frontend Design System and Consistency Audit

Status: audit baseline (2026-07-29)  
Scope: `frontend/app/**` and `frontend/components/**`  
Implementation status: no broad visual changes have been applied. This document records the current system, inconsistencies, and proposed enforcement work for approval.

## 1. Current source of truth

The closest existing source of truth is `app/globals.css`, supplemented by the font setup in `app/layout.tsx`. Many pages bypass these tokens with Tailwind literals, arbitrary pixel sizes, and inline styles. The values below distinguish existing global tokens from recurring values that are only conventions today.

### Color palette

| Role | Light | Dark | Current token |
|---|---:|---:|---|
| Page background | `#F8FAFC` | `#090514` | `--background` |
| Surface | `#FFFFFF` | `#130E22` | `--surface` |
| Surface wash / input background | `#F1F5F9` | `#1E293B` | `--surface-wash`, `--input-bg` |
| Border | `#E2E8F0` | `rgba(255,255,255,.08)` | `--border` |
| Primary text | `#1E293B` | `#F8FAFC` | `--text-primary` |
| Secondary text | `#64748B` | `#94A3B8` | `--text-secondary` |
| Accent purple | `#6D4AE2` | `#6D4AE2` | `--accent` |
| Accent highlight | `#818CF8` | `#818CF8` | `--accent-glow` |
| Accent hover | `#3A2FB8` | `#7166E8` | `--accent-hover` |
| Success | `#10B981` | `#10B981` | `--success` |
| Destructive (recurring, not tokenized) | `#EF4444`, `#DC2626`, `#B91C1C` | same | none |
| Warning (recurring, not tokenized) | Tailwind amber variants | same | none |

Current drift:

- `#5B3BC7` is widely used as the purple hover color instead of `--accent-hover`.
- `purple-400`, `purple-500`, `indigo`, `#818CF8`, and `#6D4AE2` are used interchangeably for focus, links, labels, and accents.
- Many authenticated pages use `white/5`, `white/10`, `slate-*`, and `gray-*` literals instead of semantic surface/text/border tokens.
- Authentication screens hard-code `#090514`, making Register theme-aware while Login, Reset Password, Forgot Password, and Accept Invite are dark-only.
- Error and success colors have no semantic foreground/background/border token set, so validation and status messages vary.

### Typography

Fonts configured in `app/layout.tsx`:

- Heading: Outfit (`--font-outfit`, `font-heading`)
- Body/UI: Plus Jakarta Sans (`--font-jakarta`, `font-body`)
- Global body weight: `500`
- Headings: `letter-spacing: -0.02em`

Sizes currently in use:

| Purpose | Current observed values |
|---|---|
| Page title | `text-4xl sm:text-5xl` on app pages; `text-2xl` or `text-3xl` on auth pages |
| Section heading | `text-sm` uppercase/black; also `text-lg`, `text-xl` |
| Form label | `10px/900/widest/accent`; or `11px/600/wider/gray` |
| Input/body | `13px`, `14px` (`text-sm`), and `13.5px` |
| Supporting/caption | `9px`, `10px`, `11px`, `11.5px`, `12px`, `13px` |
| Button label | `10px/900/uppercase`, `11px/900/uppercase`, `12px/600`, or `13px/600` |

Proposed canonical roles for approval:

- `display`: Outfit, 48/52, 900, tight
- `page-title`: Outfit, 36/40 desktop and 30/36 mobile, 900, tight
- `section-title`: Outfit, 16/24, 800
- `body`: Plus Jakarta Sans, 14/22, 500
- `body-small`: Plus Jakarta Sans, 13/20, 500
- `label`: Plus Jakarta Sans, 11/16, 700, `0.08em`, uppercase
- `caption`: Plus Jakarta Sans, 12/18, 500
- `button`: Plus Jakarta Sans, 13/20, 700

### Spacing

Tailwind's 4px base scale is available, but the application currently mixes it with arbitrary values. Recurring values:

- 4px: `gap-1`, `p-1`
- 6px: `gap-1.5`, `p-1.5`
- 8px: `gap-2`, `p-2`, label-to-input spacing
- 12px: `gap-3`, `p-3`
- 16px: `gap-4`, `p-4`, default form stack
- 20px: `gap-5`, `p-5`
- 24px: `gap-6`, `p-6`
- 32px: `gap-8`, `p-8`
- 40px: `p-10`

Proposed canonical scale: `4, 8, 12, 16, 24, 32, 40, 48, 64px`. Reserve 6px/20px for compact controls or an explicitly documented exception. Avoid new arbitrary values.

### Icons

Primary installed library: `lucide-react`.

Current drift:

- Lucide is used throughout most application UI.
- Inline SVGs are used for back arrows and Google branding on auth pages.
- Emoji are used for some platform and priority indicators.
- `SocialIcon` exists for social platforms, but not all platform displays use it.

Rule proposed for approval: use Lucide for all interface icons; allow official brand SVG/artwork only for third-party brands such as Google, Instagram, WhatsApp, and Messenger. Do not use emoji as functional UI icons.

### Radius, border, and shadow

Current observed radii:

- Controls: `rounded-lg` (8px), `rounded-xl` (12px), `rounded-2xl` (16px), `rounded-full`
- Cards/panels: 12px, 16px, `2rem` (32px), `2.5rem` (40px)
- Main page shell: 32px desktop / 16px mobile

Current borders:

- Usually 1px, but `.glass` uses 0.5px.
- Colors alternate between semantic `border`, `surface-border`, `white/10`, and custom accent alpha values.

Current shadows:

- `--card-shadow`: two-layer subtle outline shadow
- `.card-glossy`: large elevation plus inset border
- `.page-shell`: `0 25px 50px -12px rgba(0,0,0,.08)`
- Buttons variously use `shadow-xl`, colored glow, no shadow, or `.hover-glow`

Proposed closure rules:

- Input/control radius: 12px
- Standard card/modal radius: 16px
- Large page shell radius: 24px desktop / 16px mobile
- Standard border: 1px solid `--border`
- Standard card shadow: one semantic `--shadow-card`
- Modal shadow: one semantic `--shadow-modal`
- Avoid 32px/40px card corners except an explicitly named hero/marketing treatment.

## 2. Page-by-page inconsistency audit

### Home (`app/page.tsx`)

- Marketing page uses numerous one-off sizes, radii, gradients, and inline SVGs.
- Its expressive hero treatment can remain a documented marketing exception, but shared buttons, cards, and text roles should still use primitives/tokens.
- Social/brand artwork needs separation from functional icon rules.

### Login (`app/login/page.tsx`)

- Password visibility toggle exists and uses Lucide `Eye`/`EyeOff`, right-aligned inside the input.
- Uses a 12px-radius, 13px-input dark-only form pattern.
- Labels use 11px/semibold/gray/wider, differing from Register and Settings.
- Primary button is 13px/semibold/title case, differing from Register and authenticated pages.
- Google alternative appears before the credential form; Register places it after the primary action.
- Hard-coded dark background and white/gray colors bypass theme tokens.

### Register (`app/register/page.tsx`)

- Neither Password nor Confirm Password has a visibility toggle.
- No live email validity state, password-requirement/strength state, or live match state.
- Validation occurs only on submit; HTML `type=email` is the sole pre-submit email assistance.
- Labels use 10px/black/accent/widest with left padding, unlike Login/Accept Invite.
- Input radius is 16px and vertical padding is 14px, unlike Login's 12px/10px.
- Form uses uniform `space-y-4`, so the related password pair is not perceptually grouped.
- The OR section is inside the same form rhythm and lacks a clearly larger separation from the credential action.
- Register uses a centered glossy card while Login/Accept Invite use split layouts.
- Manual Google SVG differs from Login's separate manual Google SVG implementation.
- Password placeholders contain visibly corrupted encoded bullet text in source.

### Forgot Password (`app/forgot-password/page.tsx`)

- No password field, so no visibility toggle is required.
- Uses the dark auth visual family, not Register's theme-aware glossy card.
- Labels, input sizing, button typography, and feedback styling should be aligned with the shared form primitives.

### Reset Password (`app/reset-password/page.tsx`)

- A visibility toggle is present for the new password.
- The same `showPassword` state changes both password and confirmation input types, but only the first field displays an eye button. This creates non-obvious coupled behavior.
- Confirm Password therefore lacks the identical explicit toggle required by the consistency rule.
- Uses dark-only literals and auth label/input styles that differ from Register and Settings.

### Accept Invite (`app/accept-invite/page.tsx`)

- Password has an eye toggle; Confirm Password has none.
- Only the first password is controlled by `showPassword`; confirm remains permanently masked.
- Labels use 11px/semibold/gray, not the 10px/black/accent style in Register/Settings.
- Uses 12px input/card radii and 13px text versus Register's 16px/14px.
- Validation is submit-only, duplicating Register logic without shared validation components.

### Inbox (`app/inbox/page.tsx`, `components/chat/**`)

- Uses many compact arbitrary type sizes: 9px, 9.5px, 10px, 11.5px, and 13.5px.
- Card/control radii range from 8px through 32px.
- Mixes semantic CSS variables with hard-coded gray/slate/white and accent values.
- Conversation deletion correctly uses the shared `ConfirmModal` and success/error toasts.
- Priority selection uses emoji, conflicting with the single-icon-system goal.
- Chat components introduce additional one-off border, radius, label, and button treatments.

### Knowledge (`app/knowledge/page.tsx`)

- Uses the shared page shell but includes multiple local card/control styles.
- Document deletion correctly uses `ConfirmModal` and success/error toasts.
- List delete control is hidden until hover, which needs keyboard/focus visibility review.
- Cards, detail panels, upload areas, and modal/editor treatments do not all share one closure radius/shadow rule.

### Analytics (`app/analytics/page.tsx`)

- Page header follows the shared shell convention.
- Cards use 32px and 40px corners while standard controls use 12px.
- Buttons use 10px/black/uppercase, unlike auth buttons.
- Uses literal accent/slate/white values alongside semantic tokens.
- Dense use of 9px/10px uppercase copy reduces consistency and readability.

### Settings (`app/settings/page.tsx`)

- Business labels use the 10px/black/accent/widest convention, but the email integration fields have no labels.
- App-password field has no visibility toggle.
- Current/New/Confirm New Password fields have no visibility toggles.
- Security password fields are currently uncontrolled and the Change Password button has no implemented handler, so this UI appears non-functional.
- Input radii vary between 12px and 16px within the same page.
- Tab panel and main panel use 32px corners; child panels alternate 12px/16px.
- Connected-platform buttons call the same connect flow even when already connected; no disconnect/remove action is implemented.
- Notification changes are saved instantly to local storage without a toast; profile saves use toasts.

### Team (`app/team/page.tsx`)

- Removing a member sends `DELETE` immediately with no confirmation modal. This is the critical destructive-action gap.
- Success/error toasts exist after the action.
- Invite form labels match Settings (10px/black/accent), but inputs and buttons use the 12px/13px family.
- Team cards and invite modal use hard-coded dark surfaces and borders rather than semantic tokens.

### Super Admin (`app/super-admin/page.tsx`)

- No delete/deactivate/suspend mutation is implemented; status appears only as display/filter data.
- Uses a separate hard-coded dark admin visual language with 12px controls and white/gray literals.
- Export control appears presentational and needs behavior verification.
- If account suspension/deletion is later added, it must use the shared confirmation workflow.

### OAuth callback (`app/oauth/callback/page.tsx`)

- Transitional/loading/error surface should use the same status colors, type roles, and card treatment as other system feedback.

### Shared layout and components

- `page-shell`, `page-header`, `page-body`, and `page-padded` provide a useful partial page system.
- There are no shared `FormField`, `PasswordField`, `Button`, `Card`, or validation-feedback primitives.
- `ConfirmModal` is shared but hard-coded dark; it does not use the light/dark semantic surface tokens.
- `ConfirmModal` lacks `role="alertdialog"`, `aria-modal`, title/description associations, initial focus, focus trapping, and an async-disabled confirm state.
- Global `input, textarea, select` styles use `!important`, which can mask page-level intent and contributes to unpredictable composition.

## 3. Gestalt findings and enforcement plan

### Proximity

- Register's five inputs and submit action share a uniform 16px vertical rhythm.
- The password pair should become a named field group with 12px internal spacing and 24px separation from preceding/following unrelated groups.
- The alternative-auth block should have 32px separation above it and its own grouped divider/button spacing.
- Similar grouped-field semantics should be used for Settings password change and Accept Invite.

### Similarity

- Form labels currently have at least two competing styles.
- All forms should use one `FormLabel` role and one shared `FormField` structure.
- Buttons currently have at least three competing text/radius patterns; define primary, secondary, ghost, and destructive variants.
- Validation must use shared error/success/warning tokens and the same icon/typography structure.

### Closure

- Card radii currently range from 12px to 40px without semantic names.
- Standardize controls, cards, modals, and page shells as separate named closure levels.
- Use one border thickness and semantic border color; reserve accent borders for selected/focus/status states.

## 4. Password-field audit

| Screen/context | Fields | Current status |
|---|---|---|
| Login | Password | Has toggle |
| Register | Password, Confirm Password | Both missing |
| Reset Password | New, Confirm | One visible toggle controls both types; confirm has no explicit toggle |
| Accept Invite | Password, Confirm | Password has toggle; confirm missing |
| Settings / email integration | App Password | Missing |
| Settings / security | Current, New, Confirm New | All missing; change action also appears unimplemented |
| Forgot Password | Email only | Not applicable |

Proposed component: `PasswordField`, using Lucide `Eye`/`EyeOff`, a 44px minimum icon target, right inset, independent state per field, `aria-label`, `aria-pressed`, preserved focus, and identical behavior everywhere.

## 5. Destructive and important-action audit

### Implemented destructive actions

| Action | Location/API | Confirmation before request | Result feedback | Status |
|---|---|---:|---:|---|
| Delete conversation | Inbox / `DELETE /inbox/conversations/{id}` | Shared `ConfirmModal` | Success/error toast | Has confirmation |
| Delete knowledge document and indexed chunks | Knowledge / `DELETE /knowledge/documents/{id}` | Shared `ConfirmModal` | Success/error toast | Has confirmation |
| Remove team member | Team / `DELETE /team/members/{id}` | None | Success/error toast | **Missing confirmation** |

### Requested examples not currently implemented

| Potential action | Audit result |
|---|---|
| Remove/disconnect integration | No frontend action and no backend delete/disconnect endpoint found. Connected items currently reuse the connect button flow. |
| Delete business account | No frontend action and no backend delete endpoint found. |
| Permanently purge deleted conversation | No UI/API action found; current conversation delete appears to be recoverable because a restore action exists, despite modal copy saying “permanently deleted.” Copy/behavior mismatch must be resolved. |
| Suspend/deactivate business | Status values are displayed/filtered in Super Admin, but no mutation action was found. |

Important non-destructive actions to consider for confirmation or explicit feedback:

- Logout clears local session state immediately; confirmation is optional, but feedback/navigation should be consistent.
- Changing AI mode can materially change automated customer responses and should have explicit save confirmation or a carefully worded warning.
- Connecting an integration transfers the user into OAuth/setup; it needs clear progress/success/error feedback but not destructive confirmation.
- Restoring a conversation is reversible and currently uses a success toast; no confirmation is needed.

Shared modal work needed:

- Retain one `ConfirmModal` rather than page-specific dialogs.
- Add semantic variants (`danger`, `warning`, `important`), pending/disabled state, accessible dialog semantics, focus management, and theme tokens.
- Make the action copy accurately reflect soft-delete versus permanent deletion.
- Add it to Team member removal after scope approval.

## 6. Register validation scope

Proposed behavior:

- Email: validate on blur and then live while editing; show neutral help before interaction, error for invalid format, and success for a valid format.
- Password: display a live minimum-requirement checklist. Initial minimum should match current backend behavior (at least 6 characters) unless product requirements are intentionally strengthened. Recommended future policy: 8+ characters with multiple character categories, enforced in both frontend and backend.
- Confirm Password: show neutral state when empty, live success when matching, and live error when non-empty and mismatched.
- Submission: block only on invalid required fields, move focus to the first error, and retain the server-error summary.

Proposed semantic feedback:

- Error: red icon/text/border/background tokens
- Success: `--success` plus semantic success foreground/border/background tokens
- Warning/strength: amber semantic tokens
- Neutral help: `--text-secondary`
- Use Lucide `AlertCircle`, `CheckCircle2`, and checklist indicators consistently.

The same validation-message primitive should later replace one-off error/status styling in Login, Reset Password, Accept Invite, Settings, and Team forms.

## 7. Proposed implementation phases (awaiting approval)

### Phase 1 — consistency-critical, narrow

1. Add semantic color, radius, shadow, typography, and spacing tokens to `globals.css`.
2. Create shared `FormField`, `PasswordField`, `ValidationMessage`, and button/card style primitives.
3. Apply identical password toggles to every audited password field.
4. Add Register email/password/match live validation.
5. Apply Register proximity changes to the password group and alternative-auth group.
6. Add shared confirmation to Team member removal and correct conversation-delete copy.
7. Upgrade `ConfirmModal` accessibility and pending state without changing its API unnecessarily.

### Phase 2 — authenticated forms and panels

1. Normalize labels and inputs in Settings and Team.
2. Normalize card/panel closure across Inbox, Knowledge, Analytics, Settings, and Team.
3. Replace literal colors and one-off button variants with semantic tokens/primitives.
4. Resolve or remove the non-functional Settings change-password UI.

### Phase 3 — wider visual convergence

1. Align Login, Register, Forgot Password, Reset Password, and Accept Invite on one auth layout system.
2. Normalize Super Admin and OAuth status surfaces.
3. Replace functional emoji/inline icons with Lucide or approved brand icons.
4. Add visual regression and interaction tests for shared fields, validation, and confirmation flows.

## 8. Verification limitation

This audit is based on complete source inspection. Rendered browser verification was unavailable in the current session, so responsive behavior, computed contrast, keyboard focus order, and visual regressions must be verified in the implementation phase before sign-off.
