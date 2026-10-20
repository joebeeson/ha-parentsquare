# Releasing

Update the integration version in `custom_components/parentsquare/manifest.json`
and `pyproject.toml`, run the test and quality checks, then push a matching tag
such as `v0.1.2`. The tag workflow packages the HACS component and creates a
GitHub release with generated notes.

This repository is GitHub/HACS-first and does not publish a Python distribution
to PyPI. The shared client and dlt adapter own Python package publishing.
