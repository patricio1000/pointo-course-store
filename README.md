# Pointo Store · CSC413

A local, three-app Django e-commerce project based on the course's **Get Basic Model Working** assignment and the Pointo Store requirements proposal.

It sells **fictional** receipt printers, paper rolls, and tablet stands. Checkout saves a practice order in SQLite. It does **not** charge money, send email, ship anything, create customer accounts, or connect to the real Pointo product.

## Quick start

Requires Python 3.10 or newer. Verified with Python 3.12.14 and Django 5.2.19.

### macOS / Linux

Open a terminal in this folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver
```

Open **http://127.0.0.1:8000/**. Keep the terminal running. Press Ctrl+C to stop.

The seed command creates three categories and six products. Repeating it does not overwrite existing products. The product prices, specifications, names, and illustrations are demonstration data, not verified commercial offers.

### Create your own administrator

In the activated environment, run:

```sh
python manage.py createsuperuser
```

On Windows without activation, use `.\.venv\Scripts\python.exe` instead of `python`. Choose your own username and password. No administrator credentials are bundled. Open **http://127.0.0.1:8000/admin/** to manage products, categories, and practice orders.

### Run the tests

```sh
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run
```

The tests create a temporary test database, separate from your demo database.

## What is implemented

- **shop**: Category and Product models, admin management, category filtering, available-product listing, product detail pages, and optional uploaded product images.
- **cart**: A Python `Cart` class stores product IDs and quantities in `request.session`. Its context processor supplies a global cart counter. Customers can add, update, and remove items and review exact Decimal totals.
- **orders**: A form validates contact/address fields, saves an Order and its OrderItems atomically, clears the cart after success, and shows a confirmation with an order ID. OrderItemInline shows line items in the admin.
- **templates and static**: Local HTML/CSS and three original SVG category illustrations. No CDN, frontend framework, third-party analytics, or external image dependency.
- **tests**: Django TestCase coverage of models, views, filters, admin editing, cart sessions/quantities/totals, checkout persistence, and important failure cases.

The project settings package is called `pointo` rather than the guide's `myshop`. The required application names remain `shop`, `cart`, and `orders`.

## Product model and Pointo fields

Every product has category, name, slug, image, description, price, availability, created, and updated fields. The image is optional, as in the course guide; a local category illustration appears when no image is uploaded.

| Category kind | Required extra fields | Demo example |
| --- | --- | --- |
| Receipt printer | `paper_width_mm`, `connection_type` | 80, USB |
| Paper roll | `width_mm`, `length_m` | 80, 80 |
| Tablet stand | `tablet_size_inches`, `mount_type` | 10.2, Freestanding |

Only fill the specifications belonging to the selected category. `Product.clean()` validates them in the admin and when `full_clean()` is called. Field and database constraints reject invalid prices and order quantities. As with ordinary Django models, directly calling `save()` does not automatically run `full_clean()`.

The `Category.kind` field identifies which specification group applies. A category's display name and URL slug can be edited independently of its kind.

## How the main flow works

1. `shop.views.product_list` fetches `available=True` products and optionally filters by category.
2. `shop.views.product_detail` uses both the numeric ID and slug and refuses unavailable products.
3. A POST to `cart:cart_add` validates a quantity from 1 through 99. `override=True` replaces the quantity; otherwise it increments it.
4. The cart stores only IDs and quantities. Prices are read from the database, not from submitted form values. Deleted or unavailable products are removed from stale carts.
5. `orders:order_create` validates the form. Within a transaction it saves the order and its line items, copying each product's current name and price.
6. The cart is cleared, and the browser redirects to the confirmation page. A checkout token prevents an ordinary repeated POST from saving the same order twice. A new checkout receives a new token.
7. Confirmation pages are restricted to the session that placed the order. Changing the order number in another browser does not reveal someone else's receipt.

`Order.paid` always stays false because there is no payment processing. OrderItem keeps a name/price snapshot and uses a nullable product reference so deleting a catalog item does not erase the historical receipt.

## Main routes

| URL | Name | Purpose |
| --- | --- | --- |
| `/` | `shop:product_list` | All available products |
| `/<category-slug>/` | `shop:product_list_by_category` | Category filter |
| `/<id>/<product-slug>/` | `shop:product_detail` | Product details |
| `/cart/` | `cart:cart_detail` | Cart |
| `/cart/add/<id>/` | `cart:cart_add` | Add/update, POST only |
| `/cart/remove/<id>/` | `cart:cart_remove` | Remove, POST only |
| `/orders/create/` | `orders:order_create` | Simulated checkout |
| `/orders/created/<id>/` | `orders:order_created` | Session-restricted receipt |
| `/admin/` | Django admin | Store management |

## Manual acceptance walkthrough

1. Run migrations and `seed_demo`, then start the server.
2. Confirm that all six products and the three category filters appear.
3. Select **Receipt printers**. Only the two printers should appear.
4. Open a printer. Verify its price, description, image/illustration, paper width, and connection type.
5. Add two units. Confirm the cart counter reads 2 and the total is twice the unit price.
6. Change quantity to 3 and click **Update**. Remove an item and verify the count/total again.
7. Add a product and open **Practice checkout**. Use fictional details, such as `demo@example.test`, not real personal data.
8. Submit the form. Verify a practice order ID, line items, total, and cart count of 0.
9. Sign into admin. Open the saved order and confirm its OrderItems exist.
10. Mark a product unavailable in admin. Confirm it disappears from listing and its detail URL returns 404.
11. Try an empty checkout and invalid quantities. They must not create an order or corrupt the cart.
12. Run the automated test commands above.

The proposal's named tests are `shop.tests.ShopTests.test_category_filter` and `cart.tests.CartTests.test_cart_update_and_remove`.

## Project layout

```text
pointo/                   Settings, main URL routing, WSGI/ASGI
shop/                     Catalog models, admin, views, tests, migrations
  management/commands/    Repeatable seed_demo command
cart/                     Session cart, forms, views, context processor, tests
orders/                   Order models, forms, views, admin, tests, migrations
templates/                Shared base, shop, cart, and checkout templates
static/shop/              Local stylesheet and fallback SVG illustrations
manage.py                 Django command entry point
requirements.txt          Pinned runtime dependencies
GUIA_RAPIDA_ES.md          Spanish setup and explanation
VERIFICATION.md           Completed checks and remaining delivery steps
```

## Data and local-only scope

`db.sqlite3`, `media/`, `.venv/`, `.env`, caches, and collected static files are excluded by `.gitignore`. Database migrations and the seed command are included so another machine can recreate the catalog. Uploaded images stay in local `media/`; do not commit private images or customer information.

Development settings default to localhost hosts and a deliberately public, stable local-only key so demo sessions survive restarts. This key is not a production secret. Set a private `DJANGO_SECRET_KEY` in your shell for any non-demo use; startup refuses `DJANGO_DEBUG=0` without one. `.env.example` explains optional environment values; the project does not automatically load `.env` files. **Do not deploy this development configuration publicly.** Production hosting, payment processing, stock control, shipping, and concurrency at retail scale are outside this assignment.

## Coursework scope

This is a local academic demo. Review the code and follow your instructor's rules for outside/AI assistance. No real payments, email, shipping, or live Pointo integration are included.
