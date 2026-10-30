# Dependencies and provenance

- Runtime and tests use Python and its standard library only. Python is provided
  by the user's environment, not vendored or distributed in this repository.
  Python software and documentation use the [PSF License Version 2](https://docs.python.org/3/license.html),
  with additional terms for some incorporated components as documented there.
- There are no third-party Python packages, JavaScript packages, fonts, images,
  datasets, or copied library implementations in the application.
- GitHub CI uses GitHub's `actions/checkout` and `actions/setup-python` actions,
  each pinned to a reviewed release commit. These actions are not vendored.
  Their own repositories retain their respective MIT license notices:
  [checkout](https://github.com/actions/checkout/blob/main/LICENSE),
  [setup-python](https://github.com/actions/setup-python/blob/main/LICENSE).
- The project license is [MIT](https://spdx.org/licenses/MIT.html). It covers this
  project's original files, not the Python interpreter or external CI actions.
- The code, examples, documentation, and report styling were created with AI
  assistance in Codex in an empty isolated folder. Example traces are synthetic.
  No employer repository, private source, or external project implementation was
  read or copied to build this project. Debouncing algorithms are established
  techniques; this project does not claim their invention.

There are no production adoption, accuracy, hardware validation, or benchmark
claims. Interview discussion should accurately distinguish code generation,
review, testing, and any later personal modifications.
