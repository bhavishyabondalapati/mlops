# MLOps Lab 1: Testing and CI with GitHub Actions

My version of GitHub Lab 1 from the [course repo](https://github.com/raminmohammadi/MLOps/tree/main/Labs/Github_Labs/Lab1).
It covers virtual environments, repo structure, unit testing with pytest and unittest, and automated testing with GitHub Actions.

## What I changed from the original lab

- **New module:** replaced the calculator with `src/stats_utils.py`, a small statistics toolkit
  (mean, median, variance, std dev, min-max normalization, z-score, `describe()`, and a CSV column loader).
- **Real data:** added `data/sample_scores.csv` and tests that load from it.
- **Stronger tests:** parametrized pytest tests, edge cases (empty input, constant lists), and tests that
  check errors are raised for bad input or a missing CSV column.
- **Updated workflows:** upgraded the deprecated `@v2` actions to `checkout@v4`, `setup-python@v5`,
  and `upload-artifact@v4`; added a Python version matrix (3.10, 3.11, 3.12), a flake8 lint step,
  and triggers on pull requests as well as pushes.

## Project structure

```
lab1/
├── data/
│   └── sample_scores.csv
├── src/
│   └── stats_utils.py
├── test/
│   ├── test_pytest.py
│   └── test_unittest.py
├── requirements.txt
└── README.md
```

The CI workflows for this lab are at the repo root in `.github/workflows/lab1_pytest.yml`
(pytest + lint across 3 Python versions) and `.github/workflows/lab1_unittest.yml`.

## Setup

Run these from inside the `lab1` folder:

```bash
cd lab1
python -m venv lab_01
source lab_01/bin/activate        # Windows: lab_01\Scripts\activate
pip install -r requirements.txt
```

## Running the tests

```bash
python -m pytest test/test_pytest.py -v
python -m unittest test.test_unittest -v
```

Both suites also run automatically on every push and pull request to `main`. Results are in the repo's **Actions** tab.
