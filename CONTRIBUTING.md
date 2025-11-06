# Development - Contributing

Issues and pull requests are more than welcome: https://github.com/developmentseed/titiler-stacapi/issues

We recommand using [`uv`](https://docs.astral.sh/uv) as project manager for development.

See https://docs.astral.sh/uv/getting-started/installation/ for installation 

**dev install**

```bash
git clone https://github.com/developmentseed/titiler-stacapi.git
cd titiler-stacapi

uv sync
```

You can then run the tests with the following command:

```sh
uv run pytest --cov titiler.stacapi --cov-report term-missing
```

This repo is set to use `pre-commit` to run *isort*, *flake8*, *pydocstring*, *black* ("uncompromising Python code formatter") and mypy when committing new code.

```bash
uv run pre-commit install

# If needed, you can run pre-commit script manually 
uv run pre-commit run --all-files 
```

### Docs

```bash
git clone https://github.com/developmentseed/titiler-stacapi.git
cd titiler-stacapi

# Build docs
uv run --group docs mkdocs build -f docs/mkdocs.yml
```

Hot-reloading docs:

```bash
uv run --group docs mkdocs serve -f docs/mkdocs.yml --livereload
```

To manually deploy docs (note you should never need to do this because Github
Actions deploys automatically for new commits.):

```bash
uv run --group docs mkdocs gh-deploy -f docs/mkdocs.yml
```