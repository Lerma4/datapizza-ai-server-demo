# CI/CD with GitHub Actions

This integration provides a CI workflow that runs lint and tests on push/PR, builds the Docker image for verification, and sends optional notifications.

## Triggers
- `push` on `main` and `feature/**` branches
- `pull_request` targeting `main`

## Operating Systems
- Test and lint matrix: `ubuntu-latest`, `macos-latest` (Python 3.12)
- Docker build on `ubuntu-latest`

## Security
- Minimal job permissions: `contents: read` for all jobs
- Concurrency enabled to avoid overlapping builds
- Secrets managed via GitHub Secrets (e.g., `SLACK_WEBHOOK_URL`)

## Variables and Secrets
- `OPENAI_MODEL`: set in the test job (default `gpt-4o-mini`)
- `OPENAI_API_KEY`: not required for tests
- `SLACK_WEBHOOK_URL`: optional, for notifications

## Workflow
Path: `.github/workflows/ci.yml`

Main jobs:
- `test`: checkout, Python setup, dependencies via `uv`, lint with `ruff`, tests with `pytest` + JUnit report and summary
- `build`: Docker Buildx setup, build image `datapizza-ai-demo:latest` for verification (no push)
- `notify`: Slack notification summarizing `test` and `build` results (if `SLACK_WEBHOOK_URL` is present)

## Reporting and Monitoring
- JUnit report (artifact per OS)
- Per-job summary in `$GITHUB_STEP_SUMMARY`
- Slack notifications color-coded by status

## Instructions
1. Configure optional secrets:
   - `SLACK_WEBHOOK_URL` (for notifications)
2. Push to `main` or open a PR: the workflow will run automatically

## Troubleshooting
- `uv export --frozen`: Ensure `uv.lock` exists and is up to date
- Lint failures: run `ruff check .` locally and fix errors
- Test failures: check `pytest` logs and the JUnit report
- Docker build issues: verify Dockerfile syntax and dependencies
- Forked PRs: secrets are unavailable; notifications will be disabled

## Best Practices
- Pin Action versions (e.g., `actions/checkout@v4`)
- Branch protection with required checks (test/lint/build)
- Limit job permissions and use secrets only when necessary
- Keep Docker images lightweight and secure