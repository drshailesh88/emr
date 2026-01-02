# Feature: Comprehensive Test Suite

> Establish testing foundation to enable safe, confident development

## Status
- [x] Specified
- [ ] Planned
- [ ] Tasks Generated
- [ ] Implemented
- [ ] Tested
- [ ] Released

## Problem Statement

The codebase has 2,467 lines of production code with 0% test coverage. Any change risks breaking existing functionality. Medical software requires high reliability - we cannot ship bugs that affect patient care.

## User Stories

### Primary User Story
**As a** developer
**I want to** have comprehensive tests for all services
**So that** I can make changes confidently without breaking existing functionality

### Additional Stories
- As a developer, I want unit tests for database operations so that data integrity is verified
- As a developer, I want tests for LLM service so that prescription generation is validated
- As a developer, I want tests for RAG service so that search accuracy is maintained
- As a developer, I want integration tests so that the full workflow is verified

## Requirements

### Functional Requirements
1. **FR-1**: Unit tests for all database service methods (CRUD for patients, visits, investigations, procedures)
2. **FR-2**: Unit tests for LLM service (model selection, prescription parsing, RAG queries)
3. **FR-3**: Unit tests for RAG service (indexing, search, reindexing)
4. **FR-4**: Unit tests for PDF service (prescription generation)
5. **FR-5**: Integration tests for complete workflows (new patient → visit → prescription → PDF)
6. **FR-6**: Mock Ollama responses for deterministic testing

### Non-Functional Requirements
1. **NFR-1**: Minimum 80% code coverage for services layer
2. **NFR-2**: Minimum 60% code coverage for UI layer
3. **NFR-3**: All tests must pass in < 60 seconds
4. **NFR-4**: Tests must run without Ollama (mocked)
5. **NFR-5**: Tests must not leave residual data

## Acceptance Criteria

- [ ] `pytest` runs successfully with 80%+ coverage on services
- [ ] All database operations have unit tests
- [ ] LLM responses are mocked and tested
- [ ] RAG indexing and search are tested
- [ ] PDF generation produces valid output
- [ ] Integration test covers: add patient → add visit → generate Rx → save
- [ ] CI-ready: can run in isolated environment

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_database.py     # Database service tests
│   ├── test_llm.py          # LLM service tests
│   ├── test_rag.py          # RAG service tests
│   ├── test_pdf.py          # PDF service tests
│   └── test_schemas.py      # Pydantic model tests
├── integration/
│   ├── test_patient_workflow.py
│   └── test_prescription_workflow.py
└── fixtures/
    ├── sample_patients.json
    ├── sample_visits.json
    └── mock_llm_responses.json
```

## Out of Scope

- UI/Flet component testing (complex, lower priority)
- Performance/load testing
- Security testing

## Dependencies

- pytest
- pytest-cov
- pytest-mock
- freezegun (for date mocking)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mocking Ollama incorrectly | Tests pass but real LLM fails | Use realistic mock responses from actual Ollama |
| Database tests affecting each other | Flaky tests | Use fresh temp database per test |
| Tests too slow | Developers skip them | Optimize fixtures, use in-memory SQLite |

## Open Questions

- [x] Should we test Flet UI components? **Decision: No, too complex for MVP**
- [x] In-memory SQLite or temp file? **Decision: Temp file for realism, deleted after**

---
*Spec created: 2026-01-02*
