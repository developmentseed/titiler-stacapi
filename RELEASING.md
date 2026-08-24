# Releasing

Releases are automated with [release-please](https://github.com/googleapis/release-please).

1. Merge pull requests to `main` using [Conventional Commit](https://www.conventionalcommits.org/) style titles (`feat: ...`, `fix: ...`, `docs: ...`, etc.). This is enforced by the "Validate PR Title" check.

2. release-please watches `main` and keeps a single "release PR" up to date, bumping the version (in `.release-please-manifest.json` and `titiler/stacapi/__init__.py`) and updating `CHANGELOG.md` from the merged PR titles.

3. When you're ready to release, review and merge that release PR.

4. Merging it makes release-please create a GitHub release and a matching `X.Y.Z` tag (no `v` prefix) on `main`.

5. That tag push triggers `release.yml` (build + publish to PyPI) and `cicd.yml` (build + push the Docker image), with no further manual steps.
