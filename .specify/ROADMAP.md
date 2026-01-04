# DocAssist EMR - Feature Roadmap

> Spec-Driven Development Roadmap

## Vision
Build an EMR that Indian doctors will rely on daily - fast, offline, AI-powered.

## Current State: MVP Complete (95%)
- Core patient management
- Visit recording
- LLM prescription generation
- RAG-based patient search
- PDF export

---

## Phase 1: Production Ready
**Goal**: Safe enough for real clinical use

| # | Feature | Priority | Spec Status |
|---|---------|----------|-------------|
| 1.1 | [Test Suite](specs/01-test-suite/spec.md) | P0 | Ready |
| 1.2 | [Auto-Backup](specs/02-auto-backup/spec.md) | P0 | Ready |
| 1.3 | [Audit Trail](specs/03-audit-trail/spec.md) | P0 | Ready |
| 1.4 | [Settings Persistence](specs/04-settings/spec.md) | P1 | Ready |
| 1.5 | [Edit Operations](specs/05-edit-operations/spec.md) | P1 | Ready |
| 1.6 | [Data Export](specs/06-data-export/spec.md) | P1 | Ready |

---

## Phase 2: Speed & Efficiency
**Goal**: 50+ patients/day feels effortless

| # | Feature | Priority | Spec Status |
|---|---------|----------|-------------|
| 2.1 | [Keyboard Shortcuts](specs/07-keyboard-shortcuts/spec.md) | P1 | Ready |
| 2.2 | [Drug Database](specs/08-drug-database/spec.md) | P1 | Ready |
| 2.3 | [Clinical Templates](specs/09-clinical-templates/spec.md) | P1 | Ready |
| 2.4 | [Quick Phrases](specs/10-quick-phrases/spec.md) | P2 | Ready |
| 2.5 | [Recent Patients](specs/11-recent-patients/spec.md) | P2 | Ready |

---

## Phase 3: Clinical Excellence
**Goal**: Safer, smarter clinical decisions

| # | Feature | Priority | Spec Status |
|---|---------|----------|-------------|
| 3.1 | [Drug Interactions](specs/12-drug-interactions/spec.md) | P1 | Ready |
| 3.2 | [Lab Trends](specs/13-lab-trends/spec.md) | P1 | Ready |
| 3.3 | [Vitals Tracking](specs/14-vitals-tracking/spec.md) | P2 | Ready |
| 3.4 | [Chronic Disease Flowsheets](specs/15-flowsheets/spec.md) | P2 | Ready |
| 3.5 | [Clinical Alerts](specs/16-clinical-alerts/spec.md) | P2 | Ready |

---

## Phase 4: Delight Features
**Goal**: Can't imagine practicing without it

| # | Feature | Priority | Spec Status |
|---|---------|----------|-------------|
| 4.1 | [Voice Input](specs/17-voice-input/spec.md) | P2 | Ready |
| 4.2 | [Dark Mode](specs/18-dark-mode/spec.md) | P3 | Ready |
| 4.3 | [WhatsApp Integration](specs/19-whatsapp/spec.md) | P3 | Ready |
| 4.4 | [Appointment Calendar](specs/20-appointments/spec.md) | P2 | Ready |
| 4.5 | [Patient Reminders](specs/21-reminders/spec.md) | P3 | Ready |

---

## Implementation Order

```
Phase 1 (Production Ready) ────────────────────────────────────►
│
├─► 1.1 Test Suite (FIRST - enables safe changes)
│     └─► All other features depend on this
│
├─► 1.2 Auto-Backup + 1.3 Audit Trail [PARALLEL]
│     └─► Data safety before new features
│
├─► 1.4 Settings + 1.5 Edit Ops + 1.6 Export [PARALLEL]
│     └─► Complete the MVP gaps
│
Phase 2 (Speed) ───────────────────────────────────────────────►
│
├─► 2.1 Keyboard Shortcuts (foundational for speed)
├─► 2.2 Drug Database (most requested)
├─► 2.3 Clinical Templates
└─► 2.4-2.5 [PARALLEL] Quick phrases, Recent patients

Phase 3 (Clinical) ────────────────────────────────────────────►
│
├─► 3.1 Drug Interactions (safety critical)
├─► 3.2 Lab Trends (high value, visual)
└─► 3.3-3.5 [PARALLEL] Vitals, Flowsheets, Alerts

Phase 4 (Delight) ─────────────────────────────────────────────►
│
└─► Order based on user feedback
```

---

## Success Metrics by Phase

### Phase 1 Complete When:
- [ ] 80%+ test coverage
- [ ] Zero data loss scenarios possible
- [ ] All CRUD operations complete
- [ ] Can export all data

### Phase 2 Complete When:
- [ ] New prescription in < 60 seconds
- [ ] All common actions have shortcuts
- [ ] Top 50 drugs autocomplete
- [ ] 10+ templates for common conditions

### Phase 3 Complete When:
- [ ] Drug interaction warnings working
- [ ] Lab trends visualized
- [ ] Chronic disease tracking functional

### Phase 4 Complete When:
- [ ] Voice input achieves 90%+ accuracy
- [ ] Dark mode fully themed
- [ ] WhatsApp sharing functional

---

*Roadmap created: 2026-01-02*
*Next review: After Phase 1 completion*
