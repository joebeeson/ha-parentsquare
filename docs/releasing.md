# Releasing

Update the integration version in `custom_components/parentsquare/manifest.json`
and `pyproject.toml`, run the test and quality checks, then push a matching tag
such as `v0.1.2`. The tag workflow packages the HACS component and creates a
GitHub release with generated notes.

This repository is GitHub/HACS-first and does not publish a Python distribution
to PyPI. The shared client and dlt adapter own Python package publishing.

## HACS publication

The repository is installable as a HACS custom repository while it is being
reviewed. HACS validation and Hassfest run in
`.github/workflows/hacs.yml` on pushes, pull requests, and a weekly schedule.

To request default HACS catalog inclusion after the integration has a tested
release:

1. Confirm the HACS Action and Hassfest workflows pass with no ignored checks.
2. Confirm the repository is public, has its description, topics, issues, MIT
   license, README, root `hacs.json`, one integration under
   `custom_components/`, a valid `manifest.json`, and the local brand icon.
3. Publish a full GitHub release, not only a tag.
4. Fork [`hacs/default`](https://github.com/hacs/default), create a branch from
   `master`, and add `joebeeson/ha-parentsquare` alphabetically to its
   `integration` list.
5. Open the pull request from the owner account and wait for the automated
   checks and HACS review.

Until that pull request is merged, users install it through HACS's Custom
repositories flow or the HACS install link in the README.
