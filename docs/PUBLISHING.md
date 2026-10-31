# Publishing diceroll to PyPI

This project uses **PyPI Trusted Publishing** (GitHub Actions + OIDC), not
stored API tokens, PyPI passwords, or a release made from a developer laptop.

The distribution name is **`vicioussquid-diceroll`**, the Python import is
**`diceroll`**, and the initial release in `pyproject.toml` is **`3.0.0`**.

## 0. One-time release preparation

The GitHub workflow is [`.github/workflows/publish.yml`](../.github/workflows/publish.yml).

* **Trigger:** a *published* GitHub Release, tagged `v3.0.0`.
* **Dry-run:** run `Publish diceroll to PyPI` using **Run workflow** in GitHub
  Actions; this builds/checks artefacts **without publishing**.
* **Safety checks:** release tag must match `pyproject.toml`; tagged
  commit must be on the repository default branch; tests and distribution
  checks must pass before the publication job can start.
* **Approval:** the publishing job uses a GitHub Environment named `pypi`,
  configured with manual approval by a reviewer you trust.
* **No secrets:** PyPI grants short-lived credentials through OpenID Connect.

Do **not** publish the same version using Twine and the GitHub release
workflow: PyPI filenames/versions cannot be overwritten after publication.

## 1. Merge the release code

1. Review and merge the [diceroll packaging PR](https://github.com/ViciousSquid/diceroll/pull/1)
   into the repository's default branch (currently `1.0.0.0`).
2. Confirm that the [tests workflow](../.github/workflows/tests.yml) passes on
   the merged commit on all three supported versions.
3. Confirm `pyproject.toml` still declares `version = "3.0.0"`.

**Important:** GitHub only responds to release events using publishing
workflows already present on the default branch. Merge first; tag second.

## 2. Confirm the PyPI name and set up Trusted Publishing

Open [PyPI](https://pypi.org/) and sign in with your **existing PyPI
account**. PyPI project names are global, and name availability must be
confirmed directly on PyPI.

### For a new project name

1. Open [PyPI > Account > Publishing](https://pypi.org/manage/account/publishing/).
2. Under **Add a new pending publisher**, select **GitHub**.
3. Enter exactly:

   | Field | Value |
   | --- | --- |
   | PyPI project name | `vicioussquid-diceroll` |
   | Owner | `ViciousSquid` |
   | Repository name | `diceroll` |
   | Workflow filename | `publish.yml` |
   | Environment name | `pypi` |

4. Save the pending publisher. Its first approved GitHub publication will
   create the new PyPI project automatically.

If the project already exists **and you own it**, navigate to
**Your projects > Manage > Publishing**, and add the same GitHub trusted
publisher to the existing project. If somebody else owns the name, you
must choose another name in `pyproject.toml` and repeat the checks.

### Create the matching GitHub Environment

1. Open
   [GitHub > diceroll > Settings > Environments](https://github.com/ViciousSquid/diceroll/settings/environments).
2. Choose **New environment**, name it **`pypi`** and save.
3. Turn on **Required reviewers** and select your GitHub account (or another
   trusted reviewer), so publication requires an explicit approval.
   If GitHub disallows self-approval, use a second trusted reviewer or adjust
   the environment protection according to the available account controls.
4. Keep the environment name exactly `pypi` so the PyPI configuration
   matches it. Do not create a repository secret named `PYPI_API_TOKEN`.

## 3. Validate before publishing

Once the publishing workflow exists on the default branch, open
[Actions > Publish diceroll to PyPI](https://github.com/ViciousSquid/diceroll/actions/workflows/publish.yml)
and choose **Run workflow** on the default branch.

**This manual dispatch is a safe dry-run:** it creates and verifies a
source distribution and wheel but **does not** upload to PyPI.

For an additional local check, from a clean checkout:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install build twine
python -m unittest discover -s tests -v
python -m build
python -m twine check --strict dist/*
ls -lh dist/
```

Expected outputs for version 3.0.0:

- `dist/vicioussquid_diceroll-3.0.0-py3-none-any.whl`
- `dist/vicioussquid_diceroll-3.0.0.tar.gz`

The `examples/` directory is **not installed as an importable package**;
it is shipped in the source distribution for application developers.
`docs/` also ships in the source distribution.

## 4. Publish the first release

1. Go to
   [GitHub > diceroll > Releases > Draft a new release](https://github.com/ViciousSquid/diceroll/releases/new).
2. Select **Create new tag**: `v3.0.0`.
3. Ensure the target is the **merged default branch**, not a stale or
   unmerged feature branch.
4. Set release title to **diceroll 3.0.0** and use the changelog or release
   notes in this document.
5. Keep **Set as a pre-release** unchecked.
6. Select **Publish release**.
7. Open [Actions](https://github.com/ViciousSquid/diceroll/actions).
   The workflow **Publish diceroll to PyPI** builds, checks and tests the
   exact tagged commit.
8. When the `publish` job requests access to the **pypi** environment,
   approve that deployment in GitHub.
9. The trusted publisher exchanges an OIDC token with PyPI and uploads the
   checked source distribution and wheel.

If the job fails saying the publisher is not trusted, check all five fields
of the PyPI pending publisher, the GitHub environment name and the release
workflow filename; they must match exactly.

## 5. Verify the published project

Open https://pypi.org/project/vicioussquid-diceroll/ and verify version
**3.0.0**, the README, project URLs, and that both wheel and sdist are
available. In a fresh environment:

```bash
python3 -m venv /tmp/diceroll-release-check
source /tmp/diceroll-release-check/bin/activate
python -m pip install --upgrade pip
python -m pip install vicioussquid-diceroll==3.0.0
python -c "from diceroll import DiceRoller, render_svg; r=DiceRoller().roll('2d4+3d6+d8+d10+d12+d20', d6_colour='random'); print(r.total); assert '<svg' in render_svg(r)"
deactivate
```

This is a pure-Python wheel; separate wheels for Windows, macOS, ARM64,
or each Python version are unnecessary.

## 6. Publishing later versions

For each future release, bump `project.version` in `pyproject.toml`
(e.g. `3.0.1`), update docs/changelog, merge and pass CI, then create the
matching GitHub Release tag (`v3.0.1`). **Never reuse** `v3.0.0`
or attempt to replace existing PyPI files.

## Release notes: 3.0.0

- Breaking API cleanup: a single `DiceRoller.roll` interface and typed
  `RollResult`/component types; obsolete compatibility facades removed.
- Any dice combinations with arithmetic modifiers and strict parsing.
- Per-d6 red, white, blue or independent random colours.
- MiniWind d4/d8/d10/d12/d20 artwork plus original coloured d6 artwork.
- Dependency-free, self-contained SVG visualisation.
- Seeded RNG, observer callbacks, exact probability distributions, explicit
  history persistence, and comprehensive API documentation.

## References

- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [Python Packaging User Guide: GitHub Actions](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [Full API reference](API.md)
