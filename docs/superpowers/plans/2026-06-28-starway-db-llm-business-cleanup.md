# Starway DB LLM Business Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Starway use Tianchi core data directly, purge stale runtime data, remove `job_categories`, and keep ML/LLM/assistant flows connected to real backend logic with token-saving defaults.

**Architecture:** `jobs`, `candidates`, and `applications` remain the source of truth. Derived/cache tables such as profiles and histories can keep schema but start empty. Job category UI and APIs read distinct values from `jobs.job_category`; LLM calls go through `LLMClient` with local/Zhipu-first fallback.

**Tech Stack:** Flask, SQLite, unittest, local ML/rule scoring, DeepSeek/Zhipu-compatible HTTP chat client.

---

### Task 1: Regression Tests

**Files:**
- Modify: `backend/tests/test_starway_rebuild.py`

- [ ] Add tests that assert `job_categories` is not protected, active cleanup purges rows from `assessment_results`, `*_history`, `job_profile`, `job_relations`, and drops `job_categories`.
- [ ] Add tests that assert `/api/jobs/categories` returns categories from `jobs.job_category`.
- [ ] Add tests that assert `/api/jobs/<id>/profile` can generate a profile after `job_profile` is empty.

### Task 2: Database Cleanup

**Files:**
- Modify: `backend/services/db_cleanup.py`
- Modify: `backend/db.py`
- Modify: `backend/scripts/cleanup_db.py`

- [ ] Add `PURGE_DATA_TABLES` and `DROP_TABLES`.
- [ ] Implement `cleanup_unused_tables(apply=True, purge_data=True)` to delete data but preserve schema for histories/profile tables.
- [ ] Ensure `init_db()` drops `job_categories` after legacy initialization and does not leave `category_id` as required business logic.

### Task 3: Job Category And Profile Flow

**Files:**
- Modify: `backend/routes/job.py`
- Modify: `backend/services/career_ai_service.py`
- Modify: `backend/services/data_importer.py`

- [ ] Make category endpoints read from `jobs.job_category`.
- [ ] Make job profile generation use raw Tianchi job fields and not depend on `job_categories`.
- [ ] Keep caching into `job_profile` optional and safe after the table is empty.

### Task 4: Admin And Training Compatibility

**Files:**
- Modify: `backend/routes/admin.py`
- Modify: `backend/services/dl_models/train_job2vec.py`
- Modify: `backend/services/dl_models/train_job_classifier.py`
- Modify: `backend/services/dl_models/job_classifier_model.py`

- [ ] Remove hard dependency on `job_categories`.
- [ ] Use `jobs.job_category` or legacy `job.industry` as category source.

### Task 5: Provider And Docs Cleanup

**Files:**
- Modify: `backend/config.py`
- Modify: `backend/API_DOCUMENTATION.md`
- Modify: `backend/STRUCTURE.md`

- [ ] Document `LLM_PROVIDER=local|auto|zhipu|deepseek`.
- [ ] State that token-saving flows use local ML/rules first and Zhipu as preferred remote provider.
- [ ] Remove stale references to removed provider runtime.

### Task 6: Verification

**Commands:**
- `python -m py_compile backend\db.py backend\services\db_cleanup.py backend\routes\job.py backend\routes\admin.py backend\services\career_ai_service.py`
- `python -m unittest discover backend\tests -v`
- Flask test-client smoke for jobs search, profile, assistant chat, LLM QA.
- SQLite table/count check for purge and core data integrity.

