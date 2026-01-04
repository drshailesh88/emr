# DocAssist EMR - Constitution

> Governing principles that guide all development decisions

## Mission Statement

Build a local-first EMR that Indian doctors will rely on daily - one that respects their time, protects patient data, and enhances clinical decision-making through AI, all without requiring internet connectivity.

---

## Core Principles

### 1. Privacy First
- **No network calls** except to localhost:11434 (Ollama)
- All data stored locally (SQLite, ChromaDB, PDFs)
- No telemetry, no analytics, no cloud sync
- Patient data never leaves the doctor's machine

### 2. Speed is Respect
- Every interaction must feel instant (<100ms for UI feedback)
- LLM operations run in background threads, never block UI
- Keyboard shortcuts for all frequent actions
- Minimize clicks: if it takes 3 clicks, find a way to make it 1

### 3. Safety Above Convenience
- LLM output is always a **draft** - doctor must confirm
- Drug interactions must warn, never silently proceed
- Audit trail for all clinical data changes
- Auto-backup before any destructive operation
- Graceful degradation when Ollama unavailable

### 4. Indian Medical Context
- Support Hinglish (Hindi+English) in clinical notes
- Common Indian drug names and formulations
- Prescription format familiar to Indian pharmacists
- Units in metric (not imperial)
- Handle common abbreviations (OD, BD, TDS, HS, SOS)

### 5. Offline-First Architecture
- App must work 100% without internet
- Ollama runs locally - RAM-based model selection
- No features that require cloud services
- Data portability through local export

---

## Technical Standards

### Code Quality
- **Test Coverage**: Minimum 80% for services, 60% for UI
- **Type Hints**: 100% coverage, enforce with mypy
- **Docstrings**: All public functions documented
- **Error Handling**: Specific exceptions, never bare except

### Architecture
- **Separation of Concerns**: UI → Services → Models → Database
- **Dependency Injection**: Services injected, not imported globally
- **Threading Model**: All LLM/DB heavy operations off main thread
- **State Management**: Single source of truth per component

### Database
- **Migrations**: Version-controlled schema changes
- **Transactions**: Atomic operations for data integrity
- **Indexes**: On all foreign keys and search fields
- **Soft Deletes**: Never hard-delete clinical data

### UI/UX
- **Flet Only**: No other GUI frameworks
- **Responsive**: Works on 1366x768 minimum
- **Keyboard First**: All actions accessible via keyboard
- **Feedback**: Loading states, success/error messages
- **Consistency**: Same patterns across all panels

---

## Quality Gates

### Before Any Feature is "Done"
1. [ ] Unit tests written and passing
2. [ ] Integration test for happy path
3. [ ] Error handling for edge cases
4. [ ] Keyboard shortcut assigned (if applicable)
5. [ ] Loading states implemented
6. [ ] Works offline (Ollama unavailable)
7. [ ] No regressions in existing tests
8. [ ] Code reviewed against constitution

### Before Any Release
1. [ ] All tests pass
2. [ ] Manual testing on Windows, macOS, Linux
3. [ ] Backup/restore verified
4. [ ] Performance check (<100ms UI response)
5. [ ] Memory usage acceptable (under 500MB baseline)

---

## Non-Negotiables

These are absolute requirements that cannot be compromised:

1. **Never lose patient data** - Backup before any write, transaction for multi-step
2. **Never block the UI** - Thread all heavy operations
3. **Never auto-save LLM output** - Always require doctor confirmation
4. **Never make network calls** - Except localhost Ollama
5. **Never hard-delete** - Soft delete with audit trail

---

## Development Workflow

### For Each Feature
1. **Specify** - Write spec.md with user stories and requirements
2. **Plan** - Create plan.md with technical approach
3. **Task** - Break into tasks.md with ordered steps
4. **Implement** - Build with tests
5. **Verify** - Check against constitution and spec

### Commit Standards
- Conventional commits: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`
- Reference spec in commit: `feat(backup): add auto-backup [spec:backup]`
- No commits without tests for service layer

---

## Feature Prioritization Framework

### P0 - Critical (Must have for production)
- Data safety (backup, audit trail)
- Core clinical workflow
- Basic search functionality

### P1 - High (Required for daily use)
- Speed optimizations
- Keyboard shortcuts
- Common templates

### P2 - Medium (Differentiators)
- Drug interactions
- Lab trends
- Clinical decision support

### P3 - Nice to Have (Delight)
- Voice input
- Dark mode
- Integrations

---

## Success Metrics

A doctor should be able to:
- Add a new patient in < 30 seconds
- Complete a prescription in < 2 minutes
- Find any patient in < 5 seconds
- Answer "what was last creatinine?" in < 10 seconds
- Print prescription in < 3 seconds

---

*This constitution guides all development decisions. When in doubt, refer back to these principles.*
