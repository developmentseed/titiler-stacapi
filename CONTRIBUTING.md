# Development - Contributing

Issues and pull requests are more than welcome: https://github.com/developmentseed/titiler-stacapi/issues

**dev install**

```bash
git clone https://github.com/developmentseed/titiler-stacapi.git
cd titiler-stacapi

python -m pip install pre-commit -e .["dev,test"]
```

You can then run the tests with the following command:

```sh
python -m pytest --cov titiler.stacapi --cov-report term-missing
```

This repo is set to use `pre-commit` to run *isort*, *flake8*, *pydocstring*, *black* ("uncompromising Python code formatter") and mypy when committing new code.

```bash
$ pre-commit install
```
