# Phase 5: Premium UI Polish - Task List

> Generated from spec.md | Status: IN PROGRESS

## Phase 5A: Design Foundation

### 5A.1 Design Tokens (DONE)
- [x] Create `src/ui/tokens.py` with color palette
- [x] Add typography scale
- [x] Add spacing system (4px grid)
- [x] Add border radius scale
- [x] Add shadow definitions
- [x] Add motion timing constants
- [x] Add helper functions for theme-aware styling

### 5A.2 Enhanced Themes
- [ ] Update `src/ui/themes.py` to import and use tokens
- [ ] Create `create_premium_light_theme()` function
- [ ] Create `create_premium_dark_theme()` function
- [ ] Add panel-specific color getters
- [ ] Deprecate old hard-coded theme values

### 5A.3 Migrate App.py to Tokens
- [ ] Replace hard-coded colors in header
- [ ] Replace hard-coded colors in panel containers
- [ ] Replace hard-coded spacing values
- [ ] Use typography tokens for text
- [ ] Apply premium button styles

---

## Phase 5B: Component Library

### 5B.1 Premium Buttons
- [ ] Create `src/ui/widgets/buttons.py`
- [ ] Implement `PrimaryButton` component
- [ ] Implement `SecondaryButton` component
- [ ] Implement `DangerButton` component
- [ ] Implement `GhostButton` component
- [ ] Add hover/press animations

### 5B.2 Premium Text Fields
- [ ] Create `src/ui/widgets/text_fields.py`
- [ ] Implement `PremiumTextField` with floating label
- [ ] Implement `PremiumTextArea` with auto-resize
- [ ] Implement `SearchField` with icon
- [ ] Add focus state animations

### 5B.3 Premium Cards
- [ ] Create `src/ui/widgets/cards.py`
- [ ] Implement `PremiumCard` base component
- [ ] Implement `PatientCard` for patient list
- [ ] Implement `VisitCard` for history
- [ ] Add selection state with animation

### 5B.4 Premium Dialogs
- [ ] Create `src/ui/widgets/dialogs.py`
- [ ] Implement `PremiumDialog` with backdrop
- [ ] Add entrance/exit animations
- [ ] Standardize button placement

---

## Phase 5C: Panel Redesign

### 5C.1 Header Redesign
- [ ] Premium logo treatment
- [ ] Status indicator improvements
- [ ] User/clinic badge display
- [ ] Subtle bottom shadow

### 5C.2 Patient Panel Redesign
- [ ] Premium search field
- [ ] Today's appointments section
- [ ] Patient card improvements
- [ ] Empty state design
- [ ] FAB for new patient

### 5C.3 Central Panel Decomposition
- [ ] Extract `patient_header.py`
- [ ] Extract `vitals_form.py`
- [ ] Extract `clinical_notes.py`
- [ ] Extract `prescription_view.py`
- [ ] Extract `action_bar.py`
- [ ] Refactor main `central_panel.py` < 300 lines

### 5C.4 Agent Panel Redesign
- [ ] Premium chat bubbles
- [ ] Typing indicator
- [ ] Quick action chips
- [ ] Input area improvements

---

## Phase 5D: Micro-Interactions

- [ ] Button hover animations
- [ ] Card selection transitions
- [ ] Loading skeleton loaders
- [ ] Success/error feedback animations
- [ ] Tab switch animations

---

## Phase 5E: Polish & Refinement

- [ ] Accessibility audit
- [ ] Dark mode contrast check
- [ ] Performance profiling
- [ ] Final visual review

---

*Last updated: 2026-01-04*
