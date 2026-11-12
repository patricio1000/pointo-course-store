# Verification record

Verified on 11 November 2026 in an isolated cloud workspace, not on the owner's personal computer.

## Passed

- Python 3.12.14; Django 5.2.19; Pillow 12.3.0.
- Dependency installation in a project-local virtual environment from the recognized Python package registry.
- `python manage.py migrate`: all bundled migrations apply.
- `python manage.py seed_demo`: creates 3 categories and 6 fictional products.
- `python manage.py check`: no issues.
- `python manage.py makemigrations --check --dry-run`: no missing migrations.
- `python manage.py test`: **48 tests passed**.
- Tests render the catalog, product detail, cart, checkout, confirmation, and admin templates through Django's test client.
- Tests exercise category filtering, unavailable/deleted products, quantity validation, add/update/remove, Decimal totals, session isolation, CSRF/method protection, simulated-order persistence, cart clearing, private receipts, and repeat checkout handling.
- The specific `test_category_filter` and `test_cart_update_and_remove` tests promised in the proposal are included.
- Independent code review found two issues (sessions on restart and duplicate checkout races); both were corrected and covered by the final checks.

## Browser review

On November 12, the local store was opened successfully in Chromium, showing the six demo products and three categories. The owner reviewed the running store before authorizing publication. This is not a claim of full desktop/mobile acceptance testing.

## Scope and remaining delivery steps

- This is a local academic demo, not production software or a live store.
- No deployment, real payment, email, shipping, or live Pointo integration was made.
- No personal computer was available for installation during this task.
- The owner authorized public GitHub publication and Canvas URL submission after reviewing the local store.
- `.gitignore` excludes the local database, environment, uploads, credentials files, and caches. Source migrations and demo-seeding code recreate the project instead of sharing database contents.

The instructor's rubric includes a public GitHub repository and Canvas URL submission. Local implementation and passing tests do not by themselves complete those submission requirements.
