# Backend Structure

Starway backend is a Flask + SQLite service for university career planning.
The current rebuild keeps the existing API paths while moving the data layer to
the Tianchi job, candidate, and application datasets.

## Entry And Config

- `app.py`: creates the Flask app, initializes the database, registers routes,
  and configures CORS.
- `config.py`: centralizes SQLite path, upload path, and LLM provider settings.
  `LLM_PROVIDER` supports `local`, `auto`, `deepseek`, and `zhipu`.
- `db.py`: initializes active business tables and drops unused legacy tables so
  startup does not recreate old planning/resource tables.

## Routes

- `routes/job.py`: job search, job details, job profile generation, and
  recommendation-facing job APIs.
- `routes/match.py`: candidate-job matching, gap analysis, and recommendation
  endpoints.
- `routes/profile.py`: student profile submission and resume-style structured
  profile storage.
- `routes/assessment.py`: career assessment questions, submission, and history.
- `routes/report.py`: career report generation, export, and history.
- `routes/assistant.py`: `/api/assistant/chat` intelligent Q&A endpoint.
- `routes/llm.py`: preserved `/api/llm/*` compatibility endpoints.
- `routes/auth.py`: login, registration, verification code, personal center,
  reports, and browse history APIs.

## Services

- `services/data_importer.py`: creates/imports `jobs`, `candidates`,
  `applications`, and the legacy-compatible `job` table.
- `services/db_cleanup.py`: protects active tables, purges runtime/cache rows,
  and drops unused legacy tables.
- `services/llm_client.py`: provider switch for DeepSeek, Zhipu, local fallback,
  and streaming.
- `services/career_ai_service.py`: business-facing AI facade used by routes.
- `services/ml_recommender.py`: offline Word2Vec/TextCNN-style lightweight
  feature extraction and explainable candidate-job scoring helpers.
- `services/llm_service.py`: thin compatibility facade for older imports; new
  code should use the services above directly.

## Data

Core Tianchi tables:

- `jobs`
- `candidates`
- `applications`

Compatibility and active business tables:

- `job`, `student`, `users`, `verification_codes`
- `job_profile`, `job_relations`
- `assessment_questions`, `assessment_results`
- `match_history`, `report_history`, `reports`
- `content`, `user_profiles`, `user_browse_history`

Unused legacy tables such as old planning templates, mentor/resource tables,
and obsolete interest/ability caches are removed by `cleanup_db.py` and are not
left behind after app startup.

`job_categories` has also been removed. The source of truth for category search
is `jobs.job_category`, which is already present in the Tianchi dataset.
