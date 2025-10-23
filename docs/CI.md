# CI/CD with GitHub Actions

This integration provides a CI workflow that runs lint and tests on push/PR, builds the Docker image, and sends optional notifications.

## Triggers
- `push` on `main` and `feature/**` branches
- `pull_request` targeting `main`

## Operating Systems
- Test and lint matrix: `ubuntu-latest`, `macos-latest` (Python 3.12)
- Docker build on `ubuntu-latest`

## Security
- Minimal job permissions: `contents: read`; `packages: write` only in the build job
- Concurrency enabled to avoid overlapping builds/deploys
- Secrets managed via GitHub Secrets (e.g., `SLACK_WEBHOOK_URL`)
- Deploy (image push) only on `push` to `main`

## Variables and Secrets
- `OPENAI_MODEL`: set in the test job (default `gpt-4o-mini`)
- `OPENAI_API_KEY`: not required for tests
- `SLACK_WEBHOOK_URL`: optional, for notifications

## Workflow
Path: `.github/workflows/ci.yml`

Main jobs:
- `test`: checkout, Python setup, dependencies via `uv`, lint with `ruff`, tests with `pytest` + JUnit report and summary
- `build`: Docker Buildx setup, GHCR login (on `main`), build/push image `ghcr.io/<owner>/datapizza-ai-demo:latest`
- `notify`: Slack notification summarizing `test` and `build` results (if `SLACK_WEBHOOK_URL` is present)

## Reporting and Monitoring
- JUnit report (artifact per OS)
- Per-job summary in `$GITHUB_STEP_SUMMARY`
- Slack notifications color-coded by status

## Instructions
1. Configure optional secrets:
   - `SLACK_WEBHOOK_URL` (for notifications)
2. (Optional) Enable GitHub Container Registry in your account/organization
3. Push to `main` or open a PR: the workflow will run automatically

## Troubleshooting
- `uv export --frozen`: Ensure `uv.lock` exists and is up to date
- Lint failures: run `ruff check .` locally and fix errors
- Test failures: check `pytest` logs and the JUnit report
- GHCR login issues: verify `packages: write` permissions and repository visibility on GHCR
- Forked PRs: secrets are unavailable; notifications and image push will be disabled

## Best Practices
- Pin Action versions (e.g., `actions/checkout@v4`)
- Branch protection with required checks (test/lint/build)
- Use Environments and manual approvals for advanced deployments
- Limit job permissions and use secrets only when necessary