# Change Log

> **Append-only.** Never rewrite the past. Newest entry at the top of *History*.
> This file records every change to the agreed plan, with its rationale. The current truth
> lives in [`PLAN.md`](PLAN.md); this file records how we got there.

## History

### 2026-10-13 — v0.1.50 — `M5.2`: the operator's runbook, and two comments that had gone stale

**What landed.** `RUNBOOK.md` §9, the operator's side of the console: how to make an operator, why
`is_staff` on its own is not enough, signing in, the day-to-day catalog work, and how an order moves.
`M5` closes here.

**Numbered §9, after Troubleshooting.** §7 and §8 are cited by number from outside this file —
`ADR-0014` pins §8 as the reverse-accessor gotcha, the roadmap and this log point at §7.8 — so the
section was appended rather than slotted in before §7. A runbook whose numbers move is a runbook whose
cross-references rot, and those cross-references live in documents that may not be rewritten.

**Two comments that were true when written and are not any more.** `accounts.User`'s docstring said
`is_staff` "currently selects nothing, because `django.contrib.admin` is not installed yet" — exactly
the kind of sentence that is right until the milestone lands and then quietly lies. It now says what
the flag does and, just as usefully, what it still does not: only `AdminSite` reads it, and `/auth/me`
reports it and never checks it. The second is smaller: `ImageCreditAdmin`'s docstring claimed an image
"cannot be added" without a credit, and `ProductImage.credit` is nullable. Both are the same failure in
miniature — a comment describing an intention rather than the code beneath it — and both were written
for `M5.1`, two commits ago.

**The part of §9 worth repeating here.** `is_staff` gets an account into `/admin/` and grants it
nothing; `is_superuser`, or explicit per-model grants, is what opens the tables. The operator fixture
first written for `M5.1a` met exactly that — it reached the index and was refused every changelist —
and because it reads like a broken login rather than a permission model, §9 spells it out.

**How to run.** No behaviour changed; the docstrings and the runbook are the whole diff. The gates in
`RUNBOOK.md` §3 are unchanged and the suite still reports 332 passing.

### 2026-10-13 — v0.1.49 — `M5.1b`: the orders half, and a status an operator cannot type

**What landed.** `orders/admin.py`, and with it the console's other half (`US-5.4`, `US-5.5`): the
order list with a filter and a search box, the lines and the event timeline on the change page, and
four actions — paid, shipped, delivered, cancelled — that move an order along `ALLOWED_TRANSITIONS`.
`M5.1` closes here.

**An order is a receipt, so the page is read-only.** Every column is in `readonly_fields`, `status`
among them, and the change form has no editable field at all. That is the mechanism, not a nicety: the
way an order moves is an action, each action calls the `transition_order` the API calls, and
`ALLOWED_TRANSITIONS` stays a rule because there is nowhere to type a status into. The test that holds
this is that the form's `base_fields` is empty — the day someone adds `status` to a fieldset without
`readonly_fields`, the guard gains an end-run around it, and that is the change this catches.

**A Save button that cannot save.** With nothing editable, Django's submit row would still offer Save
— a control that appears to write and does not, which is the kind of small lie this codebase refuses
elsewhere. `render_change_form` turns the flag off and the row reads as Close instead. Add and delete
are shut for the same reason: an order is what checkout writes, and a receipt is not a thing to remove.
Cancelling is how an order is undone, and cancelling is recorded.

**Cancelling is also a stock event.** The cancel action calls `cancel_order` rather than transitioning
the order itself, which is the reason `orders/services.py` gives for the function existing. Creation
took the stock (`ADR-0017`), so an action that assigned `cancelled` would leave the shelf short — and
a shop whose sellable quantity shrinks a little with every cancellation is a failure nobody notices
for months. The test watches the stock go from 5 to 3 and back to 5.

**A selection is not all or nothing.** `transition_order` raises rather than returning a flag, and an
operator who ticks two orders and finds one already shipped should be told which of them moved and
which did not, not shown an error page. Each action collects both and reports them; an order that
refused keeps the timeline it had, and no event claims otherwise.

**How to run.** Unchanged from `M5.1a`: `uv run python manage.py check`,
`uv run ruff format --check .`, `uv run ruff check .`, `uv run basedpyright`, `uv run pytest` (332
passing, +10).

### 2026-10-13 — v0.1.48 — `M5.1a`: the console, installed and pointed at the catalog

**What landed.** Django admin as the v1 operator console (`ADR-0007`, `SCOPE.md` §8 D1) at `/admin/`
(`API.md` §9): the framework's `admin`, `sessions` and `messages` apps with the middleware and the
template context processors they need; `accounts/admin.py` and `catalog/admin.py`; and the tests that
hold the console to what `ADR-0007` asks of it.

**The app is Django's, so the wiring is the work.** The REST API is stateless (`ADR-0009`) and wants
neither sessions nor messages; the console is where they belong. `MIDDLEWARE` gained four entries —
`Session`, `Csrf`, `Auth`, `Message` — and `XFrameOptions` for the one page here that renders
server-side HTML a person signs into. The cost to an API request is the length of that list:
`SessionMiddleware` loads lazily and does not touch the database without a session cookie, and
`AuthenticationMiddleware` sets a lazy `request.user` the API never reads.

**`CsrfViewMiddleware`, in front of everything, and the API did not notice.** `django-ninja` sets
`csrf_exempt` on every operation at the view, so the middleware adds a check to the admin's forms and
to nothing else. That is a claim worth a test rather than a comment, so one test registers a user
through `Client(enforce_csrf_checks=True)` with no token and expects a `201`.

**The user model had to be registered by hand.** Installing `admin` makes Django register *its* user
model — `django.contrib.auth.models.User`, the swapped-out default — and not `AUTH_USER_MODEL`, so
`accounts.User` arrives at the console unregistered. The framework's `UserAdmin` is built for a user
with a `username`, whose absence is an `admin.E108` system-check error, so `accounts/admin.py`
supplies the fieldsets this model has plus `is_staff` — the operator flag `ADR-0007` gates on.

**"Genuinely usable", per `ADR-0007`.** A filter and a search box on every catalog table; variants and
images inline on the product that owns them; stock editable from the variant list, because `US-5.3`'s
"set stock levels" is a page of edits, not one SKU at a time; and a low-stock column with a filter
beside it, said in words rather than colour (`NFR-2`).

**What the tests had to learn.** `is_staff` opens the console but grants no model permissions — the
first operator fixture reached the index and was refused every changelist — so the fixture is a
superuser, the shape `createsuperuser` produces and `M5.2` will document. The orders half of the
console (`US-5.4`, `US-5.5`) is `M5.1b`; `M5.1` stays `[~]` until it lands.

**How to run.** `uv run python manage.py check`, `uv run ruff format --check .`, `uv run ruff check .`,
`uv run basedpyright`, `uv run pytest`; `uv run python manage.py migrate` applies the framework apps'
own migrations (no project migration — `makemigrations --check` reports none).

### 2026-10-13 — v0.1.47 — `M4` closes: the retrospective

`M4`'s exit criterion is "order created, paid, history shown", and that path now runs end to end: the
quote prices a cart, creation reserves its stock and answers one order per idempotency key, the mock
capture moves it to `paid` and enqueues its receipt, and `/orders` reads it back. Six increments,
committed and green; `ROADMAP.md` §2 marks `M4` `[x]`.

**The milestone's spine was decided before any of it was built.** `ADR-0017` reversed the cart to
require sign-in and, with it, moved the binding race-safe stock decrement from capture to *order
creation* — which is what made `M4.3` one transaction instead of two, and deleted an increment from
`M3`. Everything after had to respect that one place: `M4.2` prices *without* checking stock, because a
second, weaker check elsewhere could only disagree with the transaction that binds; `M4.3`'s cancel
releases the reservation, so a decline cannot shrink the shop; and `M4.2` corrected `API.md` §6 to
`access` where the pre-reversal contract still said "optional".

**A receipt is not a cart.** `M4.1` snapshots what was bought rather than referencing it, and turns on
the `SET_NULL`/`PROTECT` line between the two: a cart is live intent, so withdrawing a SKU may not
silently rearrange one, while an order is evidence, so neither may it be deleted. The money arithmetic
(`total = subtotal + shipping`, `line_total = unit_price × quantity`) is a `CheckConstraint` rather
than code that happens to agree.

**The interface was the decision, three times.** The quote prices and creation sells; the four checkout
steps live in one route because a half-finished order has nothing for a URL to mean; and the history and
detail make the caller's scope the authorisation, so a foreign order is the same `404` as one that never
existed rather than a `403` that would confirm it does.

**What the code proved, in the order it bit:**

1. **A gate is only a gate over what it includes.** `basedpyright`'s `include` named five directories
   but not `cart` or `orders`, so `M3.1`'s "0 errors" was true of code the gate had never opened.
   `M4.2` added both, and the first run found the implicit-`order_id` reads `ADR-0014` predicts. The
   same lesson `M3` learned about a suite that passed for the wrong reason, one layer down.
2. **Some claims can only be checked off the machine that wrote them.** `M4.3`'s "stock, order and
   payment land together" is a claim about three rows in one transaction, and no test sharing a process
   with the code can show it. Driving the *deployed* stack showed the rows, the `200` replay of an
   idempotency key, and the second capture's `409` — and found what an in-process test could not:
   `M4.4`'s receipt fails *silently* (`immediate` catches the exception onto an unread `TaskResult`,
   the production mailer discards by design), so a customer would get no confirmation and the logs
   would say nothing. Written into `RUNBOOK.md` §7.8 and filed as `M6.4`.
3. **The build is a gate.** `M4.5`'s idempotency key was minted during render, which `pnpm test` was
   content with and `next build` refused outright — the same shape as (1), at the top of the stack.

**Where the documents had drifted from the code, the milestone corrected them:** `ARCHITECTURE.md` §6
moved the decrement to creation (`ADR-0017`), §3 and `M7.1` lost a worker that never existed, and
`RUNBOOK.md` §8 retired a rate-limit explanation the founder had by now disproved. A gate is also where
the documents are held to what actually runs.

**Risk register, re-scored at the gate.** No risk changed status. The one this milestone touched is
`RISK-6` (async complexity): `M4.4`'s tasks are the first async hop, and their silent-failure mode is
that risk in miniature — it already has its response filed (`M6.4`) and written down (`RUNBOOK.md`
§7.8).

**Evidence.** Backend **306** tests against PostgreSQL (260 at `M4.2`); `ruff format --check`,
`ruff check`, `basedpyright` (0 errors, over `cart` and `orders` for the first time) and the
`export_openapi_schema` drift check green. The contract test `test_openapi_documents_every_api_path`
grew by each of `M4`'s paths as they landed. Frontend **141** tests (119 at `M3`); `tsc --noEmit`,
`eslint`, `prettier` and `next build` green, with `/checkout`, `/orders` and `/orders/[number]` among
the built routes. The end-to-end evidence is `v0.1.43` (the deployed checkout) and `M4.6`'s API suite;
the browser sign-in journey remains the one step that needs a person, as `M2.7` first noted.

### 2026-10-13 — v0.1.46 — M4.6: the orders a customer can read back

**What landed.** `GET /orders` and `GET /orders/{number}` (`US-4.5`, `US-4.6`): the history as rows,
the detail as the receipt the confirmation carried plus its status timeline. In `orders/api.py` the two
routes, in `orders/schemas.py` the four schemas they answer with; in the browser `src/api/orders.ts` is
the wire, `src/lib/orders.ts` the status words and the dates (6 tests), and `/orders` and
`/orders/[number]` the two routes over `order-history-screen.tsx` and `order-detail-screen.tsx`.

**One receipt, two readers.** `POST /orders` and `GET /orders/{number}` answer from the same field
mapping, so the detail page cannot show an order that differs from the one the confirmation showed;
only the detail adds the timeline. The history is deliberately not that mapping — a row is a number, a
date, a status, a count and a total, because naming every line and address for a page of orders is the
whole receipt repeated to render five fields.

**The scope is the authorisation.** Both routes read the caller's orders by filtering on the caller,
and there is no "every order" route for the filter to be the wrong half of. The detail answers a `404`
for a number that is not the caller's — the same body as a number that never existed — rather than a
`403` that would confirm the number is real, the reasoning the address book already gives.

**Reachable, or it is not delivered.** The header grows an Orders entry beside Cart, and the checkout
confirmation's order number becomes a link to its detail page — a number the customer can already read
off the receipt, now also somewhere to go.

**Two corrections the first cut needed.** The aggregate that counts a row's items is invisible to the
type checker, so `order.item_count` needed the same `pyright: ignore` the account model already
carries. And a grouped query drops `Order.Meta.ordering`, so the history spells `-created_at, -id` out
— the first version had no `ORDER BY` at all and answered in whatever order the database returned,
which is not the same order twice.

**How to run.** Backend: `uv run ruff format --check .`, `uv run ruff check .`, `uv run basedpyright`,
`uv run pytest`, and the `export_openapi_schema` drift check. Frontend: `pnpm typecheck`, `pnpm lint`,
`pnpm format:check`, `pnpm test`, `pnpm build`. All green; `openapi.json` carries the two routes and
the four schemas.

### 2026-10-13 — v0.1.45 — M4.5: the checkout, and the four places it could have gone wrong

**What landed.** `/checkout` (`US-4.1`-`US-4.4`): one route holding the four steps — address, shipping,
payment, confirmation. `src/api/checkout.ts` is the wire, `src/lib/checkout.ts` is the sequence and the
address rule (13 tests), and `checkout-screen.tsx` is the screen. The cart's disabled "Proceed to
checkout" — the placeholder that said it was waiting for somewhere to go — is now a link to it.

**One route, not four.** A half-finished order is not a page anyone can be linked to, reload into or
share, so there is nothing for a URL to mean. Keeping the steps in one component also keeps the chosen
address and the chosen method in scope when the payment is taken, instead of passing them through a
query string the customer could edit.

**The build caught what the tests could not.** `useRef(newIdempotencyKey())` ran during render, so
`crypto.randomUUID()` was evaluated while the page was being prerendered — and `next build` refuses an
unstable value in a Client Component outright. The key is now made on the click that needs it, which is
also the only moment it means anything. `pnpm test` was green throughout; only `pnpm build` was not, and
it named the line. That is the case for keeping the build in the gates rather than trusting the suite.

**A replay is not a second order.** Placing and settling are two calls, so the first can land while the
second's response is lost — the customer sees a failure, presses again, and `Idempotency-Key` answers
with the *same* order. Settling it twice is a `409`, which would be reported to someone who has already
paid. `needsSettlement` reads the order's own status instead, so a retry is quiet and correct.

**Both mock outcomes are controls.** A decline cancels the order and returns its stock, and the
confirmation says so; a failed settle leaves the customer on the payment step with the buttons still
live, which is the "payment failure with retry" `UX.md` flow C asks for.
**How to run:** `pnpm typecheck`, `pnpm lint`, `pnpm format:check`, `pnpm test` (132 passing) and
`pnpm build` — all green. No API changed, so the backend gates and `openapi.json` are untouched.

### 2026-10-13 — v0.1.44 — one item filed, one explanation retired

**A new plan item, from the cloud check.** `M6.4` now carries the fix for `M4.4`'s blind spot: a
`task_finished` receiver that logs a failed task. Filed rather than built, because it belongs with the
observability work instead of bolted onto the increment that revealed it — but written down now, while
the reason is still concrete.

**And an explanation retired.** The open rate-limit action in `RUNBOOK.md` §8 blamed the dashboard's
`NINJA_NUM_PROXIES` value. The founder checked it — it **is** `2` — and redeployed, and the limit still
does not count. So the value is wrong rather than overridden, and `2` counts infrastructure instead of
the visitor. The action is rewritten to say that, and to say how to settle it: log the resolved ident
once and read it out of Render's logs, rather than reasoning the number out a third time.
**How to run:** nothing; a roadmap item and a corrected diagnosis.

### 2026-10-13 — v0.1.43 — the checkout, verified where it actually runs

**What was done.** The `M4` checkout path was driven end to end against the deployed stack — not the
localhost one, and not a test — because `M4.3`'s claim is that stock, an order and a payment land
together in one transaction, and no test sharing a process with the code can show all three rows
arriving in Supabase.

**What it showed.** Everything it was asked to: the quote; the order at `pending` with the shipping cost
carried into its total; the same `Idempotency-Key` answering `200` with the *first* order instead of
creating a second; the mock capture moving the order to `paid`; and a second capture refused with `409`.
The deployed schema advertises all three `M4.3` routes, which also proves the boot path's `migrate`
created their tables.

**What it could not show — which is the finding.** `M4.4`'s email. The deployed mailer discards the
message by design, and the `immediate` task backend catches a task's exception onto a `TaskResult`
nobody reads rather than raising it. A broken receipt is therefore invisible from outside the stack *and*
from its logs. The blind spot is now written down in `RUNBOOK.md` §7.8 with the fix it suggests, rather
than left for a customer who never gets a confirmation to discover.

**Left behind.** A smoke account, its cart and a paid order in the demo database, plus one unit off one
variant — the same footprint `M2.7`'s smoke left, and §7.5 says how to delete it.
**How to run:** §7.8's table is the checklist; the smoke is a dozen `curl`s against the two public hosts.

### 2026-10-13 — v0.1.42 — docs: the worker that was never there

**What was wrong.** `ARCHITECTURE.md` §3 drew a `Worker` container and listed it in the container
table; `ADR-0006`'s consequences said a worker process is needed in production (a Render background
worker); `ROADMAP.md` `M7.1` promised to deploy one; `TODO_cloud-engineer.md` named it as a target. None
of it was true. `render.yaml` declares a single `type: web` service, and Django 6 ships only the
`immediate` and `dummy` task backends — so `immediate` runs a task in the web process that enqueued it,
and there has never been a queue for a worker to consume or a second service to host one.

**What changed.** The §3 diagram and its table now show one Render service carrying the off-request
jobs, with a paragraph saying why; `M7.1` and the cloud TODO match reality. `ADR-0006` keeps its
original wording and carries a dated correction beside it, because `ADR-0000` permits only the status
line to change later and a decision record that quietly rewrites itself stops being a record.

**Deliberately left alone.** `ARCHITECTURE.md` §9 still has a worker draining a queue — that is Phase 2's
ingestion outline, a design for work that does not exist yet rather than a claim about the deploy.
**How to run:** nothing; documentation only.

### 2026-10-13 — v0.1.41 — `M4.4`: the receipt, off the request path

**What landed.** The order-confirmation email, as a `Task` (`ADR-0006`). `orders/tasks.py` holds it and
`orders/templates/orders/confirmation_email.txt` is its body; the mock payment's `confirm` route
enqueues it once the order is `paid` (`SCOPE.md` `US-4.4`).

**Enqueued on the outcome, not the attempt.** The enqueue sits after the transition, guarded by the
status the transition *returned*, so a payment the provider declined — or a decline the caller asked
for — sends nothing. A receipt for an order nobody paid for would be worse than a late one.

**The task takes an id, not an order.** Whatever crosses a queue boundary has to be serialisable, so the
task re-reads the row on the far side. Passing the object would work only for the backend that happens
to run in-process, which is exactly the accident that becomes a bug the day the backend changes.

**Neither transport is SMTP, and neither is accidental.** `locmem` in dev and tests collects messages in
`django.core.mail.outbox`, which is what lets a test assert *one* email went to *that* address;
production uses `dummy`, because `locmem`'s outbox is an unbounded list in a long-lived process. Email
and tasks are both values — `DJANGO_MAILER_BACKEND`, `DJANGO_TASK_BACKEND` — and `immediate` runs a task
in the calling process, so dev needs no worker and no broker.

**`MAILERS`, not `EMAIL_BACKEND`.** Django 6.1 deprecates `EMAIL_BACKEND` (removed in 2028) in favour of
a mailer registry, so this landed as the current shape rather than as a deprecation debt taken on in
2026. The warning surfaced only because the new module runs green under `-W error::DeprecationWarning`.

**Verified.** 6 new tests, 295 in total, against PostgreSQL; `ruff check`, `ruff format --check`,
`basedpyright` (0 errors) and `makemigrations --check` clean — no model changed, so no migration. **How
to run:** nothing extra. The gates in `RUNBOOK.md` §3 suffice, and `backend/.env` needs no new key
unless a real transport is wanted.

### 2026-10-13 — v0.1.40 — `M4.3`: the order, and the money it waits on

**What landed.** `POST /orders` and the `payments` context. Placing an order turns the caller's cart
into an order — reserving its stock, snapshotting its lines and its address, and starting a payment —
and the mock provider's two routes settle that payment either way (`US-4.4`, `NFR-4`, `ADR-0010`).

**Order creation is one transaction, and the stock decrement is inside it.** `ADR-0017` puts the
binding, race-safe decrement at order creation rather than at the cart or at capture, so the cart is
locked, the named variants are locked *in a deterministic order*, checked, and only then written —
either every line is taken and the order exists, or nothing moved. The cart's cap is an affordance;
this is the guarantee. `ARCHITECTURE.md` §6's diagram had the decrement at capture; it now says what
the code does, which is what `ADR-0017` asked for.

**Cancelling returns the stock, or a decline shrinks the shop forever.** Because creation reserved it,
`cancel_order` releases it — so the mock's fail route does not leak a reservation for a purchase that
never happened. `M5.5`'s operator cancel goes through the same function, which is why the rule lives in
`orders/services.py` rather than in the payments endpoint.

**`Idempotency-Key` (`NFR-4`).** A key already seen answers `200` with the order it produced and
touches nothing; a fresh one answers `201`. The check is a read, so a simultaneous double submit can
race it: the unique index is the arbiter and the endpoint catches the `IntegrityError` and re-reads. No
key is simply not idempotent.

**The mock is a port, not a special case.** `PaymentGateway` has the mock adapter behind it and
`PAYMENT_PROVIDER` selects it — configuration, not code. The two mock routes are the exception they were
always meant to be: they let a caller *state* a capture's outcome, which no real provider's contract
contains, so off the mock they answer `404` as if unmounted. `base.py` had never read
`PAYMENT_PROVIDER` at all — `payments/providers.py` expected a setting nothing set — so the wiring is
part of this increment.

**Verified.** 29 new tests, 289 in total, against PostgreSQL — including one that commits
(`transaction=True`) and races two real connections for the last unit, where exactly one order
survives; `ruff check`, `ruff format --check`, `basedpyright` (0 errors) and `makemigrations --check`
clean; the OpenAPI snapshot gained three paths and the contract test names them. **How to run:** the
four gates in `RUNBOOK.md` §3, with `PAYMENT_PROVIDER=mock` in `backend/.env` for the mock routes.

### 2026-10-13 — v0.1.39 — `M4.2`: the quote, and the contract it corrected

**What landed.** `POST /checkout/quote`: the caller's cart priced as a subtotal, plus every shipping
option with the total that choosing it produces (`US-4.1`, `US-4.2`). The address is required and
validated; `orders/shipping.py` holds the simulated methods, so a rate is a value to change rather
than a number buried in a view.

**Exactly one address, and it is a precondition rather than a result.** A saved `address_id` is read
through the caller's own scope, so somebody else's is a `404` and not a `403` that would confirm the
id exists; an inline `address` is checked against the schema, the same constraints the address book
uses. Sending neither, or both, is a `400`. An empty cart — no cart, or a cart with no lines — is a
`409`: there is nothing to price. The address is validated and then dropped, because the answer is
money and echoing an address back would invite a client to read it from here instead of from where the
shopper set it.

**The quote prices; `M4.3` sells.** Stock is deliberately not checked. `ADR-0017` puts the binding,
race-safe decrement in the order-creation transaction, so a check here would be a weaker second one in
a different place — answering `409` for a cart that order creation might well accept. What the quote
*does* hold is the arithmetic the order's own constraint will later enforce:
`total_cents = subtotal_cents + shipping_cents`, per option, never a number a client has to add.

**`API.md` §6 said "optional", and `ADR-0017` had already made that wrong.** A quote reads the
caller's cart; a cart needs an account; so the route carries a bearer token and the contract now says
`access`. `POST /orders` inherits the correction, which `M4.3` will exercise. Shipping is a fixed set
of flat rates (`ADR-0010`) and address-independent on purpose: this module is the seam a real carrier
would slot into, and a rate that ignored the address it was handed would only be pretending otherwise.

**Two gate gaps closed on the way past.** `basedpyright`'s `include` named `config`, `core`,
`accounts`, `catalog` and `tests` but not `cart` or `orders`, so neither context had ever actually
been type-checked — the `M3.1` entry's "basedpyright 0 errors" was true of code the gate never opened.
Both are in scope now, which surfaced exactly what `ADR-0014` predicts: `OrderItem.__str__` and
`OrderEvent.__str__` read the implicit `order_id` attname, invisible to the checker, and read
`self.order.pk` instead.

**Verified.** 11 new tests in `tests/test_checkout_api.py`, and the contract test in
`tests/test_catalog_api.py` grown by the one new path; 260 tests pass against PostgreSQL; `ruff
check`, `ruff format --check`, `basedpyright` (0 errors, over `cart` and `orders` for the first time)
and `makemigrations --check` clean; the OpenAPI snapshot regenerated with exactly one added path.
**How to run:** `uv run python manage.py export_openapi_schema` after any route change, then the four
gates in `RUNBOOK.md` §3.

### 2026-10-12 — v0.1.38 — `M4.1`: the order, and the state it is in

**What landed.** The `orders` app: `Order`, `OrderItem` and `OrderEvent`, their constraints, and the
guarded transition (`US-5.5`) in `orders/services.py`. No endpoints yet — `M4.2` spends the models on
a quote and `M4.3` spends them on creation — so this increment is the shape a receipt has to have
before anything is allowed to write one.

**A receipt is not a cart.** Everything mutable is snapshotted onto the order rather than referenced:
the product name, the variant name, the unit price, and the address it went to. The line's `variant`
is a nullable `SET_NULL` where the cart's is a `PROTECT`, and that difference is the design decision
this increment turns on — a cart is live intent, so withdrawing a SKU may not silently rearrange one,
while an order is a receipt and `PROTECT` would make catalogue maintenance impossible for any product
that had ever sold, with `CASCADE` deleting the evidence instead. The order's `user` is `SET_NULL` for
the same reason: closing an account must not delete what was bought.

**Arithmetic the database holds.** `total_cents = subtotal_cents + shipping_cents`, and
`line_total_cents = unit_price_cents × quantity`, as `CheckConstraint`s rather than as code that
happens to agree. `DATA-MODEL.md` section 4 asks for non-negative money; `PositiveIntegerField` gives
that on Postgres but not on SQLite, so it is stated again where both have to obey.

**The transition is an event.** `transition_order()` reads the *locked* row, refuses a move the table
does not allow, writes the status and appends the `OrderEvent` in one transaction. A guard that
returned a flag would leave every caller to decide what "refused" means; an exception is what carries
that decision outward to the `409` it should become. `OrderEvent` refuses edits and deletes, which the
docstring is honest about: a `QuerySet.update()` or a cascade is one level below the guard — but every
ordinary use of the object goes through it, and the trail cannot be rewritten by accident.

`any → cancelled` is implemented literally, including from `delivered`, because `DATA-MODEL.md`
section 3 says *any* and a return is exactly what that records. `cancelled` therefore has to be
terminal, which is what keeps the table acyclic. The reading is pinned by a test so it can be reversed
deliberately rather than by accident at `M5.5`.

**Two lint rules decided something rather than being silenced.** `DJ001` forbids `null=True` on a
string field, so an event's `from_status` is `""` on the creation event — the one event with no
previous state — rather than `NULL`. And `ADR-0014` held: the tests reach `OrderEvent` through
`OrderEvent.objects.filter(order=...)`, never through `order.events`.

**Verified.** 34 new tests (the constraints by breaking each one, the two `SET_NULL` survivals, the
four status-machine directions, the refusals asserting *no record* as well as no change, and the guard
reading the locked row rather than a stale handle); `ruff format --check`, `ruff check`,
`basedpyright` and the full suite; `makemigrations --check` reporting no drift, which CI does not
check and which is how a model lands without its migration; and the OpenAPI snapshot unmoved, because
a model is not a route. The row lock's behaviour under real concurrency is **not** tested here: with
no endpoint yet, a threaded test would be testing Django, so it belongs with `M5.5`, where two
operators can actually race.

### 2026-10-12 — v0.1.37 — `M3.2`: the cart a customer uses, and the close of `M3`

**What landed.** The browser half of the cart: `lib/cart.ts` (the store the header's count and the
page both read, plus the rules the stepper obeys), `api/cart.ts` over `M3.1`'s four endpoints,
`/cart` with line items, a quantity stepper and totals, and a real add-to-cart on the product page
in place of the disabled placeholder `M1.6` left behind. `M3` closes with it.

**One cart, two readers.** The store is a module variable read through `useSyncExternalStore`, the
shape `lib/session.ts` uses, because the header shows a count on every page and the cart page shows
the same cart. A payload copied into each component would let the two disagree the moment an add
landed on one of them. Every mutation answers with the whole cart, so `api/cart.ts` writes that
response into the store: nothing increments a count by hand, and no total is computed in the browser.

**The colour choice is not decoration.** Every product carries three colour variants with stock and
price of their own — 95 variants over 91 distinct prices in the seeded data. `catalog/models.py`
already draws the line: `base_price_cents` is the display price, the variant's `price_cents` is what
a purchase is made at. So each option carries its own price, and an option with no stock is disabled
with "Out of stock" in words (`NFR-2`). The initial selection is the first *purchasable* variant
rather than the first row, and when no colour has stock the button says so beside itself instead of
pretending.

**The stepper refuses rather than reports.** `+` is disabled at `available_stock`, with "Only N
available" beside it, and `−` stops at one — zero on this cart is removal (`US-3.3`), not a quantity.
If the API refuses anyway, because stock moved or another tab got there first, the `409` message is
shown as written: it names both the stock and the number asked for.

**Session-shaped.** The store follows the session: read on `authenticated`, cleared on `anonymous`,
untouched during `restoring` — clearing there would throw away a cart that is about to be read again,
on every navigation. A read's failure is held in the same store as the cart and cleared by the same
events, which is why a retry panel cannot outlive what it was about, and why the provider holds no
React state: the one `setState` in an effect body came out rather than being deferred past a lint
rule.

**Two deviations, both recorded rather than silent.** `US-3.4` asks for "estimated shipping", and
`API.md` section 5 carries a subtotal and nothing else, so the summary says "Calculated at
checkout" — the options and their prices are `US-4.2`'s — and `SCOPE.md`'s `US-3.4` now carries that
note. "Proceed to checkout" is a disabled control with its reason stated in text, the same call
`M1.6` made for add-to-cart, until `M4` gives it somewhere to go.

**Verified.** 20 tests on the store's rules (the stock cap, the floor at one, first-purchasable,
units against lines, and a failure cleared both by the cart that answers it and by a session
ending); the frontend suite at 119; and the five gates CI runs, run here the same way — `prettier
--check`, `eslint`, `pnpm typecheck` (which regenerates the OpenAPI types first, so a cart call that
no longer matches the snapshot fails the build rather than the browser), `vitest`, and `next build`,
which now lists `/cart` among its routes.

**Corrected while passing through:** `lib/session.ts` justified `credentials: "include"` with
`ADR-0008`'s guest cart cookie, which `ADR-0017` deleted. The refresh cookie is the reason it stays,
and the comment and its test title now say so.

**M3 retrospective.** The milestone changed shape before a line of it was written — `ADR-0017`
dropped the guest cart and its login merge, deleting an increment and leaving `ADR-0008`'s signed
cookie with no reader. Three things it taught, in the order they bit:

1. **The contract test earned its keep.** `test_openapi_documents_every_api_path` failed the moment
   the cart's three paths existed. That is the first time `M1.3`'s drift guard has caught anything,
   and it caught it while the increment was still open rather than a milestone later.
2. **A green suite is only as good as the run behind it.** The cart's first "all green" was false:
   a second `pytest` process was still holding `test_lysheim`, so the run that reported success had
   actually errored at database setup, and its exit code had been piped into `tail`. The code was
   fine; the verification was not. One database-touching run at a time, and read the exit code.
3. **A guard that cannot fail is not evidence.** The row lock was mutated back to no lock and
   observed to fail before it was trusted, which is the same standard `M2.7`'s throttle test was
   held to.

### 2026-10-12 — v0.1.36 — `M3.1`: the cart, behind the bearer token

**What landed.** A `cart` app with `Cart` and `CartItem` built to `DATA-MODEL.md` §2, the four
endpoints from `API.md` §5, and the authentication `ADR-0017` decided earlier the same day. A cart
belongs to an account, holds one line per variant, and stores no price at all: prices resolve from
the variant live, which is what the data model asks for and what leaves `M4` free to snapshot them
onto the order, where a price that must not move belongs.

**The rules the schema holds rather than the code.** A partial unique index allows one *active* cart
per user — and does not block the next one after checkout converts it. `(cart, variant)` is unique,
so adding a variant already on the cart adds to its quantity rather than starting a second line.
`quantity >= 1` is a check constraint, because removal is an endpoint and a zero line is a row every
total would have to remember to skip. The variant is `PROTECT`ed, so withdrawing one from the catalog
is refused while carts hold it instead of silently emptying them. `catalog` gained the
`stock_qty >= 0` check that `DATA-MODEL.md` §4 lists and `PositiveIntegerField` already implied, so
the schema now states what the document states — it is the invariant `M4`'s decrement relies on.

**Stock.** A cart line is capped by available stock, and a request above it is refused with `409`
naming both numbers, which is what `US-3.2` asks for. The check is an affordance and not a guarantee:
stock moves between the cart and checkout, and `ADR-0017` records that `M4`'s conditional decrement
inside a transaction is the binding one.

**Concurrency, tested rather than asserted.** Adding takes a row lock on the cart, because two
concurrent adds of the same variant would otherwise both read the same quantity and write the same
increment over each other. `test_two_concurrent_adds_do_not_lose_an_increment` runs two real
connections; it is marked for PostgreSQL, since SQLite ignores `SELECT … FOR UPDATE` and would
pretend the lock was there — and it closes each thread's connection, which is exactly what its first
version failed to do, leaving pytest unable to drop the test database afterwards.

**Verified.** 25 API tests and 8 model tests on PostgreSQL; `ruff format`, `ruff check`,
`basedpyright` 0 errors, `makemigrations --check` clean, and the whole suite green.
`frontend/openapi.json` was regenerated with the three new paths — Backend CI diffs that snapshot, so
an endpoint missing from it is a red build rather than a missing type — and
`test_openapi_documents_every_api_path`, which pins the exact set of documented paths, was updated to
name them: shipping an endpoint is a decision the contract test should register, not a change it
should absorb.

**Not here:** the cart UI, which is `M3.2`, and the guest cart, which no longer exists. One path
departs from `API.md`: `PATCH`/`DELETE` use `/cart/items/{line_id}` rather than `{id}`, so the
parameter cannot be confused with the `variant_id` in the request body, and `API.md` §5 was updated
to say so.

### 2026-10-12 — v0.1.35 — the cart requires sign-in: `D2` reversed before it was built

**The decision.** `ADR-0008` chose a cookie-keyed guest cart merged on login, on the grounds that
~8 in 10 carts are abandoned and the primary persona shops on mobile. The Founder reversed it while
`M3.1` was being built: the catalog stays public, and every cart operation — read, add, update,
remove — requires an access token. `ADR-0017` records the reversal; `ADR-0008` keeps its text and
changes only its status line, which is all `ADR-0000`'s template allows after acceptance.

**What it removed.** The guest cart, its signed cookie, its 30-day expiry, the login merge and the
`cart.session_key` column — so the roadmap's guest-merge increment is deleted rather than deferred
and the cart UI is renumbered to `M3.2`. `SEC-FIND-1.12` (forged guest cart identifiers) closes by
design rather than by mitigation: there is no cart cookie to forge.

**What it costs, recorded rather than glossed.** A visitor's first add meets a sign-in screen, and
Phase 2's abandonment analysis can only ever see shoppers who had already signed in. That is exactly
the friction the earlier decision was protecting against, and this one accepts it knowingly.

**Amended:** `SCOPE.md` (`US-3.1`, `US-3.5`, `D2`), `API.md` §5, `DATA-MODEL.md` §2 and §4
(`cart.user_id` NOT NULL, no `session_key`, one active cart per user), `ROADMAP.md` `M3`,
`SECURITY-BASELINE.md`, `_working/TODO_backend.md`. The `PATCH` row in `API.md` said "stock-capped"
while its own `409` note and `US-3.2` said refused above stock; the two now agree on refusal.

**Settled for `M4` while deciding this.** The cart's stock check is an affordance, not a guarantee —
stock moves between the cart and checkout — so `ADR-0017` records that the authoritative decrement is
a conditional `UPDATE … WHERE stock_qty >= n`, or `SELECT … FOR UPDATE` over the variants in a
deterministic order, inside one transaction. `M4` inherits the requirement instead of rediscovering
it, and cannot oversell.

### 2026-10-12 — v0.1.34 — the deployment recorded, with the numbers that matter to a reviewer

**What changed.** The root `README.md` no longer claims "Status: planning" — it carries the two live
URLs, what a visitor can do today, and the cold-start expectation that `ADR-0011` asks to be
documented for a reviewer. `RUNBOOK.md` gained section 7.8, the deployment as it stands: each check
with the thing it actually asserts, because several of them assert a header or a redirect rather than
the status code that appears first.

**Why the check table is written that way.** Two of these were nearly recorded backwards. A preflight
from a foreign origin answers `200` — the *absence* of `access-control-allow-origin` is the assertion,
and the browser is what refuses it. And `/healthz` answering `200` over plain `http` is the
`SECURE_REDIRECT_EXEMPT` working, not the redirect failing. A table that lists the status alone would
have taught the next reader the wrong lesson.

**Measured.** CORS verified in both directions from the real origin, which is what the earlier pass
could not do: the preflight carries
`access-control-allow-origin: https://ecommerce-project-five-psi.vercel.app` with credentials and the
five methods, where the same request from a foreign origin carries no `access-control-allow-*` header
at all. First-visit latency, which is a reviewer's first impression: 48s for the first page load, 2s
warm, 28s for a route's own first hit, 1s from the API when awake. The rate limits are still
uncounted on the deployed instance — the corrected `NINJA_NUM_PROXIES` needs its redeploy.

**Impact.** Documentation only; no code. `M2.7` remains `[~]` for the redeploy and a browser sign-in.

### 2026-10-12 — v0.1.33 — M2.7 is live, and the limits were counting Cloudflare

**What happened.** The deployment went green. Render built the image, the start-up script migrated
and seeded the Supabase database, and the catalogue is served through the Vercel app. Verified from
outside the stack rather than from the deployment log: `/healthz` answered `200` with a request id,
the public URL served all 46 products, `http` redirected to `https` with `301`, and every response
carried HSTS (`includeSubDomains; preload`), `nosniff` and `strict-origin-when-cross-origin` — the
hardening in `prod.py` applied rather than merely written. Also checked, because they are the parts
that fail quietly: an authenticated route answered `401` without a token, the refresh origin guard
answered `403` to a foreign origin, and a preflight from a foreign origin came back with no
`access-control-allow-origin` at all.

**The defect that only testing from outside could find.** Forty rapid `POST /auth/login` attempts
from one client produced **one** `429`, at attempt 23 — a limit of ten per minute behaving like a
lottery. `NINJA_NUM_PROXIES` was `1`, and at `1` Ninja's `get_ident` takes the *last*
`X-Forwarded-For` entry: the address the nearest proxy appended. Render serves `.onrender.com`
through Cloudflare (the API's own `server` header says so), so that entry belongs to Cloudflare's
edge and rotates between requests, and the attempts spread across buckets that never filled. The
key was neither the client nor a bucket anyone shares. At `3` it would be whatever an attacker wrote
in their own header, which is a bypass, so the value has to match the chain rather than err upward:
it is `2`. Note what the tests could not see — they establish *whose* requests are counted using
`REMOTE_ADDR` alone and never `X-Forwarded-For`, so the only dimension that differed between the
suite and the deployment was the untested one.

**A test worth more than the fix.**
`test_the_counted_address_is_the_client_and_not_a_hop_in_front_of_it` asserts that a swapped hop
address does not open a new window and that a forged leading entry cannot move the key. Checked by
mutation rather than assumed: at `1` it fails with `401 == 429`, and at `3` it fails on the forged
entry, so it guards both directions. Writing it turned up a smaller thing: this file's older throttle
tests replace `NINJA_DEFAULT_THROTTLE_RATES` wholesale, and Ninja resolves *every* scope's rate while
building its operation list lazily on a process's first request — so they fail when run in isolation.
The new test extends the mapping instead, and says why in a comment.

**Impact.** `M2.7` is deployed and verified from outside, with one item left: a sign-in through the
live stack, which needs a browser. The proxy count is corrected in `prod.py`, `render.yaml`,
`.env.example` and the reasoning in `base.py`; the deployed service needs one redeploy for it to
take effect, and the forty-attempt check is what confirms it.

### 2026-10-12 — v0.1.32 — M2.7 first deploy: the start command was unparsable, and a redirect loop behind it

**What changed.** The compound start command moved out of `render.yaml` and into
`backend/docker-entrypoint.sh`, which the Dockerfile's `CMD` now runs; `dockerCommand` names that
file with a single token. `prod.py` gained `SECURE_PROXY_SSL_HEADER` and a `SECURE_REDIRECT_EXEMPT`
entry for `/healthz`.

**The defect, reproduced rather than guessed at.** Render's "Docker Command" is a string the platform
parses: it strips a leading `/bin/sh -c` and hands the remainder to its own shell, so the double
quotes that hold a `&&` chain together made the entire command a single word. The deploy died with
`python manage.py migrate --noinput && … --port 10000: not found`. Reproduced without Render in two
lines — `docker run --rm alpine sh -c '"echo a && echo b"'` gives `sh: echo a && echo b: not found`,
while the same string unquoted prints both lines — which also explains why Render's documented
*unquoted* example works and a quoted one cannot: after the prefix is stripped, quotes turn the
command into a program name. The field is one token now, and the work sits in a file that can be read,
tested and linted.

**The blocker behind it, found by testing instead of by deploying.** `prod.py` sets
`SECURE_SSL_REDIRECT = True`, and nothing told Django that TLS is terminated in front of it. Render's
balancer forwards plain HTTP with `X-Forwarded-Proto`, so every request — ones that arrived over
HTTPS, and Render's health probe — would have been redirected to the HTTPS URL it was already
serving, forever. `SECURE_PROXY_SSL_HEADER` removes the loop. `SECURE_REDIRECT_EXEMPT` for `/healthz`
means the probe answers `200` over either scheme, so a redirect can never be the reason a deploy does
not come up. Trusting the header is safe for the same reason `NINJA_NUM_PROXIES = 1` is: the app is
not reachable except through the balancer.

**Verified.** The image was built and booted against an empty PostgreSQL with `PORT=9999`. First
boot: 19 migrations applied to nothing, 46 products and 7 categories seeded, uvicorn bound 9999
rather than 8000. The three scheme behaviours: `/healthz` `200` with no header,
`/api/v1/products` `301` to `https://` with no header, `200` with `X-Forwarded-Proto: https` and real
rows in the body. Second boot, which is the shape every wake takes: nothing to migrate, the seed a
no-op, serving about 9s after `docker run`, most of it container start. Backend gates after the
settings change: `ruff format`, `ruff check`, `basedpyright` (0 errors) and 181 `pytest` tests.

**Impact.** `M2.7` stays `[~]` — the deploy still needs the three accounts and the values pasted into
two dashboards. Nothing outside production settings changed behaviour.

### 2026-10-12 — v0.1.31 — M2.7 deployment configuration

**What changed.** `render.yaml`, a Render Blueprint for the API: Docker runtime on
`backend/Dockerfile`, `plan: free` in the region matching Supabase, `/healthz` as the health check,
`DJANGO_SECRET_KEY` generated by the platform rather than pasted, `DATABASE_URL` and
`CORS_ALLOWED_ORIGINS` as `sync: false` prompts, and `DJANGO_ALLOWED_HOSTS` read from
`RENDER_EXTERNAL_HOSTNAME` so the service knows its own hostname. `RUNBOOK.md` section 7 is the
procedure now rather than a placeholder, with the expected first-deploy failures written down as
anticipated rather than observed.

**Decisions.** Migrations and the seed run in the **start command**, because Render's pre-deploy
command is limited to paid instance types, so a free service has no separate stage to run them in.
Render's own Docker documentation suggests this shape, and `compose.yml` already used it locally.
`seed` is idempotent by contract, so it runs on every boot too — `--reset` must never appear there,
because it would wipe the catalogue on each cold start. Concurrent migrations were **accepted**
rather than guarded: the free plan runs one instance with no autoscaling, and the runbook records
the condition that would invalidate that. `compose.yml` stays a local-only tool: Render builds from
a Dockerfile or a prebuilt image, and a compose file is neither, so the Dockerfile is the only thing
the two share.

**Verified.** The Blueprint validates with **zero errors** against Render's published schema
(`render.com/schema/render.yaml.json`, draft 2020-12), field names, region and plan included — worth
doing because the platform ignores an unknown field silently rather than complaining. The start
command's cost, measured on a throwaway database so the dev one was untouched: `migrate` 1.18s cold
and 0.74s when there is nothing to apply; `seed` 0.98s and 0.91s. Both are dominated by Django's
interpreter boot, and both disappear beside a cold start measured in tens of seconds.

**Impact.** No application code changed. `M2.7` is `[~]`: the configuration and the procedure are
done, and the deploy itself needs three external accounts plus values pasted into two dashboards,
which is the founder's half. `M7` still owns custom domains, backups and the full production
journey. One ADR wording was found to overstate the code: `ADR-0011` describes `CONN_MAX_AGE` as
"tuned", and nothing sets it — Django's default of `0` is the right value behind a pooler, so the
runbook records the setting as correct by omission rather than inventing the knob.

### 2026-10-12 — v0.1.30 — M2.6 account screen; the milestone closes

**What changed.** `/account` (`UX.md` section 3) with `ProfileForm`, `AddressList` and `AddressForm`;
`frontend/src/api/account.ts`, the first client that needs a token and therefore the first to go
through `lib/session.ts`; `lib/address-form.ts`, the fields' rules and the camelCase-to-snake_case
translation; the sign-in form now lands on `/account` rather than the home page, and the header's
name is the link to it.

**Decisions.** One route with two sections, because `UX.md` gives one route. The default flag is a
three-way choice rather than a checkbox — offered when an account already has an address, replaced by
a sentence for the first one (the API defaults it anyway), and absent when editing (`API.md` §8
refuses to let a default be cleared), so `toUpdatePayload` sends no `is_default` at all. The default
is a word, not a colour (`NFR-2`). The server sends the *restoring* state, never the signed-out one,
because that is the flash `M2.4`'s three-state model exists to prevent; the cost, accepted, is that a
visitor without JavaScript sees only the loading line. `PATCH /auth/me` writes the new name into the
session store, since the header renders from it. The envelope reader and the labelled input were
extracted to `lib/api-failure.ts` and `components/text-field.tsx` when a second form needed them,
rather than imported across from the auth form.

**Found while building it.** The end-to-end check's assertion that no session-bound content reaches
the server HTML passed for the wrong reason: it searched for the words "Profile" and "Addresses",
which the page's meta description carries in prose, and reported two rendered sections that were not
there. It matches section ids now. Separately, `react-hooks/set-state-in-effect` refuses a mount fetch
called directly even when its state lands after the `await`; the async IIFE `session-provider` already
uses is the shape it accepts. And the first version of the end-to-end script killed the `pnpm`
wrapper instead of the `next-server` child, leaving a process holding the port — it uses `setsid` and
a process-group kill now.

**Impact.** Frontend gates green: `prettier`, `eslint`, `tsc --noEmit`, **99 vitest tests (up from
79)** across 13 files, and a production build of 10 routes with `/account` **static**. Backend
untouched. Verified over HTTP against PostgreSQL: `/account` answered `200` with one `<h1>` and its
own title, carrying the restoring state and no `<h2>` from the signed-in screen; a body built exactly
as the add form builds it answered `201` and became the default unasked; the edit payload (no
`is_default`) answered `200` and left it default; `PATCH /auth/me` answered `200`; the list came back
default-first; `/`, `/products`, `/login`, `/register` and `/pages/credits` unregressed; 0
tracebacks, 0 `500`s, 0 web errors. The seven interactive cases (`QA-C56`–`QA-C62`) are recorded as
not run: they need a browser, which is also true of `QA-C43`–`QA-C51` from the two increments before
this one. `M2.6` is `[x]`.

### 2026-10-12 — v0.1.29 — M2.6 profile and the address book (API)

**What changed.** `PATCH /auth/me` (`US-2.4`) and the `/addresses` routes (`US-2.5`) with their
schemas; `AccessTokenAuth` moved to `accounts/auth.py` so the two routers share one authentication
instead of one importing the other; `API.md` §2 gained the `PATCH` row and §8 the payload, the
`404`-not-`403` rule and the default rule; the OpenAPI snapshot was regenerated.

**Decisions.** An address is reached through the caller's own scope rather than fetched and then
checked, so the ownership check has no branch to forget (`QA-C31`); another account's address is
`404`, not `403`, which would confirm the id exists; the routes hold *exactly one* default where the
database's partial index holds *at most one*; clearing the default is `409`, because it is the
resource's state rather than a field error and `400` is what the frontend maps onto inputs; required
fields carry a floor of one character, which the database does not enforce.

**Found by the tests.** Pydantic's own errors arrived as `body.payload.country` while errors raised by
hand produced `body.email` — one contract, two spellings, and a client that strips the source prefix
as `API.md` instructs would match one and quietly fall back to a form-level message for the other.
`core/errors.py` now drops the view parameter's name, and a test pins both paths to the same shape. It
had survived because every existing field-error test exercised the hand-raised path, so nothing had
ever asserted a pydantic-generated body error.

**Impact.** Backend gates green: `ruff format --check`, `ruff check`, `basedpyright` (**0 errors**),
**181 tests, 30 new** (24 for the address book, 6 for the profile). Frontend gates re-run green
against the regenerated snapshot: `prettier`, `eslint`, `tsc --noEmit`, 79 vitest tests. Verified over
HTTP against PostgreSQL: the first address is created `201` and becomes the default unasked, a second
is not, promotion moves the default and leaves exactly one, clearing it answers `409` `CONFLICT`; a
second account lists nothing and gets `404` on both `PATCH` and `DELETE`, with the row unchanged
afterwards; deleting the default promotes the survivor; `PATCH /auth/me` edits the name and an empty
body changes nothing; and all three field-error shapes now report `body.<field>`. 0 tracebacks, 0
`500`s. The UI half of `M2.6` is still to come.

### 2026-10-12 — v0.1.28 — Lean increment ceremony; roadmap recut (M2.6–M7)

**Context.** Two costs were slowing the build without buying anti-slop: a ~500-word change-log essay
per increment, and an ADR for every micro-decision. The defects this project actually caught came
from the gates and from running the code, not from the narrative. Separately, the deploy was parked
at `M7`, so nothing was publicly visible for half the roadmap.

**What changed.**

- `decisions/ADR-0016-lean-increment-ceremony.md` — new. Terse per-increment log entries; long-form
  rationale once per milestone; an ADR only for hard-to-reverse decisions; gates unchanged.
- `WORKING-AGREEMENT.md` — rule 1 and a new rule 9 encode the leaner cadence; the DoD gains a
  change-log line.
- `04-delivery/ROADMAP.md` — `M2.6`–`M7` recut into fewer, coarser increments (`M3` 4→3, `M4` 7→6,
  `M5` 3→2, `M6` 5→3, `M7` 6→3), a new `M2.7` that deploys the walking skeleton early, and a
  milestone retrospective at each gate. Overview statuses corrected (`M1` was already done).
- `PLAN.md` — re-baselined to v0.1.5.

**Decisions taken.** Per `ADR-0016`; the substantive one is that the deploy moves from the end
(`M7`) to a checkpoint at `M2.7`, so a public URL exists roughly halfway through Phase 1.

**Impact.** No code changed. Phase 1 increments fall from 50 to 43, and the prose burden per
increment drops to a compact entry. Gates and QA provenance are unchanged.

### 2026-10-11 — v0.1.27 — M2.5 sign-in and registration pages

**Context.** `M2.5`. `US-2.1` and `US-2.2` ask for registration and sign-in with validation, and
`UX.md` flow D names the states that must exist — bad credentials, an address already registered, and
the rate-limit message. `M2.4` had left a session nobody could reach: the token was renewed on load
and no page could start or end one.

**What changed.**

- `frontend/src/lib/auth-form.ts` — new: the field rules, the mapper from the API's `details` onto
  inputs, and the message for each failure status. Tested in `auth-form.test.ts`.
- `frontend/src/components/auth-form.tsx` — new: one form for both endpoints, field errors wired to
  their inputs, the form-level failure as a `role="alert"`, and the busy state.
- `frontend/src/app/login/page.tsx`, `frontend/src/app/register/page.tsx` — new: the two routes,
  statically generated.
- `frontend/src/components/site-header.tsx` — new: the wordmark and the session-aware actions, in the
  three states `M2.4` defined; `frontend/src/app/layout.tsx` renders it above the page content.
- `docs/03-architecture/API.md` — §3's `details` example corrected: the field arrives carrying its
  source (`body.email`), which is what the code has always sent.

**Decisions taken.**

- **One form, two pages.** Mode-driven, because the error handling is the part that must exist once.
- **The server's answer wins.** Client validation runs first to save a round trip, and a rejection
  replaces it field by field, so the client can never insist on something the server refused.
- **A field error with no matching input still reaches the customer**, as the form-level message, so
  an unrecognised name is visible rather than dropped.
- **`noValidate`, and no `required`.** The browser's own bubble would otherwise be a second voice on
  the page, saying something different from every other message on it.
- **The header renders no session state until the session is restored**, rather than flashing "Sign
  in" at a signed-in customer and taking it back.
- **Sign-out tells the API first and forgets locally in a `finally`**, per `ADR-0009`: a logout that
  failed because the token was already dead has still logged the user out.

**Impact.** Frontend gates green: `prettier`, `eslint`, `tsc --noEmit`, **79 vitest tests** (17 new)
and a production build of all 9 routes, with `/login` and `/register` static. Verified over HTTP:
both pages answered `200` with their form already in the HTML and `autocomplete="new-password"` on
the register password field; the header carried no session state; a duplicate address was reported as
`body.email` and a weak password as `body.password`; a failed sign-in returned `401`
`UNAUTHENTICATED` with the sentence the form shows. 0 tracebacks, 0 `500`s, 0 web errors. The check
found the `API.md` discrepancy above, which no test could have: the contract and the code disagreed
about the field name, and only asking the running API exposed it. The four browser-level cases
(`QA-C48`–`QA-C51`) are recorded as not run, and `QA-C43`'s blocker moved to `M2.6` — the pages here
are the ones a signed-out visitor uses.

### 2026-10-11 — v0.1.26 — M2.4 frontend session and cross-origin access

**Context.** `M2.4`. `US-2.3` asks for token refresh to be silent and for logout to clear session
state; `ADR-0009` puts the access token in memory and the refresh token in a cookie, which decides
everything here. The frontend could not call the API at all before this increment.

**What changed.**

- `frontend/src/lib/session.ts` — new: the in-memory session, the three-state model, and
  `authorizedFetch`/`renew` behind one shared in-flight refresh.
- `frontend/src/api/auth.ts` — new: login, register, refresh, logout, each leaving the store correct;
  failures come back as values, with the API's per-field `details` preserved for the forms.
- `frontend/src/components/session-provider.tsx` — new: the React binding and the silent refresh on
  load; `frontend/src/app/layout.tsx` wraps the app in it.
- `backend/config/settings/base.py`, `backend/pyproject.toml` — `django-cors-headers` added, its
  middleware installed above `CommonMiddleware`, credentials allowed.
- `frontend/src/lib/session.test.ts` — 12 tests; `backend/tests/test_cors.py` — 5.
- `docs/decisions/ADR-0015-continuous-increments.md` — new: amends how the working agreement of
  `ADR-0004` is applied. Increments still land as small, gated, tested commits, but they now run
  continuously, and the assistant stops only when a founder decision is genuinely required.

**Decisions taken.**

- **One refresh at a time.** Not an optimisation: rotation plus reuse detection turns two concurrent
  refreshes into a forced logout, so this guard is what makes concurrent authenticated calls safe.
- **Three session states, not two.** "Restoring" exists because losing the token on reload is normal
  and must not render as signed out.
- **CORS added here rather than deferred.** `CORS_ALLOWED_ORIGINS` had existed since `M0.6` with
  nothing reading it, so the increment that first needs a browser call is the one that has to fix it.
- **Errors as values, and the envelope narrowed rather than asserted**, so a proxy returning HTML
  produces "please try again" instead of a crashed page.

**Impact.** Backend gates green: 145 tests, `basedpyright` 0 errors, plus the 5 new CORS tests.
Frontend gates green: `prettier`, `eslint`, `tsc --noEmit`, **62 vitest tests** (12 new) and a
production build of all 7 routes. Verified over HTTP: both preflights `200` with `authorization`
allowed, a credentialed registration `201` with one cookie, the silent refresh `200` rotating one
cookie, an unlisted origin receiving no allow-origin header while its refresh was refused `403`, and 0
tracebacks with 0 `500`s. The first version of one interceptor test failed because of the test, not
the code: the mocked refresh resolved instantly, so the two calls never overlapped.

### 2026-10-11 — v0.1.25 — M2.3 rate limiting and the refresh origin guard

**Context.** `M2.3`. `US-2.2` asks for a rate-limited sign-in and `NFR-3` for auth rate limiting
generally; `ADR-0009` asks the refresh endpoint to enforce an origin check *in addition to* the cookie,
because a cookie is a credential the browser attaches by itself and the production cookie is
`SameSite=None` for the Vercel-to-Render call.

**What changed.**

- `accounts/throttling.py` — new: one scope per endpoint, on a base that re-reads its rate per request.
- `accounts/api.py` — a throttle on all five endpoints, `_origin_is_trusted()`, and the `403` it
  returns from `/auth/refresh` before the cookie is read.
- `config/settings/base.py`, `prod.py` — `NINJA_DEFAULT_THROTTLE_RATES`, `NINJA_NUM_PROXIES`, and an
  explicit `CACHES` naming the throttle store.
- `tests/test_accounts_api.py` — 14 more tests: the limits, the key, and the guard.
- `API.md` section 2 — the limits and the origin check written into the contract.

**Decisions taken.**

- **Per client, not per account.** A limiter keyed on the submitted address would let anyone lock a
  known account out of its own sign-in screen, which turns a rate limit into a denial-of-service tool.
  The cost is that a distributed attack is not stopped by this alone.
- **Ninja's throttles, with the rate re-read per request.** `SimpleRateThrottle` resolves the rate in
  `__init__` and Ninja attaches instances built at import, so the shipped limit would have been
  whatever the settings held at import, and no test could lower one to watch it trip. A failing test
  found that, not a reading.
- **`NINJA_NUM_PROXIES` set explicitly.** The default trusts `X-Forwarded-For` verbatim, which would
  make every limit bypassable with a forged header — so the setting *is* the control. `0` locally,
  `1` on Render, whose load balancer terminates TLS and forwards to a port that is not reachable
  directly.
- **`AuthRateThrottle`, not `UserRateThrottle`**, on the authenticated endpoints: the latter reads
  `request.user`, which does not exist without `AuthenticationMiddleware`, so it would raise instead of
  limiting anything.
- **A shared cache is a scale-out prerequisite, not a now problem.** The store is LocMemCache, so the
  limits are per process. Recorded as `QA-G6`.

**Impact.** Gates green: `ruff format --check`, `ruff check`, `basedpyright` (**0 errors**) and
`pytest` (**145 tests, up from 132**). Verified over HTTP against PostgreSQL: the eleventh login with a
wrong password answered `429` with `RATE_LIMITED` and `Retry-After: 51`, exactly the configured
`10/min`; the correct password was refused too, because the limit is on the endpoint; two forged
`X-Forwarded-For` values were both refused (so the header buys nothing) while a request bound to a
second loopback address got its own window; and the tenth bulk registration answered `429`, matching
`10/hour`. `/auth/refresh` from a foreign `Origin`, or from a foreign `Referer` with no `Origin`,
answered `403` `FORBIDDEN`; a request with neither was allowed; and the session survived both refusals,
because the next trusted refresh answered `200`. 0 tracebacks and 0 `500`s.

### 2026-10-11 — v0.1.24 — M2.2 auth endpoints

**Context.** `M2.2`. `US-2.1`-`US-2.3` are the acceptance criteria: register with email, password
validation and a duplicate-email error; sign in with a rate-limited endpoint and a clear error on bad
credentials; and stay signed in or log out, with silent refresh. `ADR-0009` fixes the shape — access
token in the body and held in memory, refresh token as an httpOnly cookie — and requires logout to
invalidate that refresh token *server-side*.

**What changed.**

- `accounts/tokens.py` — new: JWT issuing, verification, rotation and revocation, with reuse
  detection.
- `accounts/models.py` — new `RefreshToken`: one row per issued token, keyed by `jti`, so a signature
  can be revoked.
- `accounts/schemas.py`, `accounts/api.py` — new: the five endpoints and an `HttpBearer` guard.
- `config/api.py` — the accounts router mounted at `/auth`.
- `config/settings/base.py`, `prod.py` — JWT key, both TTLs and the refresh cookie's attributes;
  production raises `Secure` and `SameSite=None` for the cross-site Vercel-to-Render call.
- `tests/test_accounts_api.py` — 30 contract tests.
- `docs/03-architecture/DATA-MODEL.md`, `API.md` — the new table and the token payload documented.

**Decisions taken.**

- **The refresh token is a JWT *and* is recorded server-side.** `US-2.2` asks for a "JWT access +
  refresh pair" and `ADR-0009` asks for server-side invalidation; a `jti` claim plus a row satisfies
  both without inventing an opaque token scheme.
- **Rotation with reuse detection.** Presenting a revoked token revokes every live token for that
  user, because a copy in circulation is the only way a revoked token reappears.
- **A failed refresh returns its `401` rather than raising `HttpError`.** Raising hands the response to
  Ninja's exception handler, which builds a fresh one, so a cleared cookie would never reach the
  browser and a dead token would be re-presented on every page load forever. This was found by a test.
- **One message for both sign-in failures**, so the endpoint cannot enumerate registered addresses.
- **`/auth/refresh` does not accept an access token**, so a leaked access token cannot extend itself.
- **Only the `jti` is stored, never the token.** A leaked table cannot be replayed without the signing
  key.

**Impact.** Gates green: `ruff format --check`, `ruff check`, `basedpyright` (**0 errors**) and
`pytest` (**132 tests, up from 102**), plus no migration drift. The OpenAPI snapshot was regenerated,
so the five routes are in the contract and the frontend's generated types now know them. Verified end
to end over real HTTP: registration lower-cases the address and returns `201` with a JWT access token
and an `HttpOnly; Path=/api/v1/auth` cookie; `/auth/me` answers `200` with the token and `401` without
one; refresh rotates the cookie; replaying the old cookie answers `401` and leaves the user with zero
live tokens; logout answers `204`, clears the cookie and kills the session server-side; duplicate
registration is a `400` naming `body.email`; a weak password is refused with all three reasons; a wrong
password and an unknown address are identical; the catalog is unregressed; and the server logged no
tracebacks and no `500`s. It now also runs on the engine that will serve production: `docker compose up
-d db` plus a `backend/.env` carrying `DATABASE_URL`, then `migrate`, `seed` and the suite. PostgreSQL
17.11 passes all **132 tests**, the seeded counts match SQLite exactly (7 categories, 46 products, 95
variants, 46 images, 46 credits), and the guard SQLite cannot exercise is verified on it — with one
process holding `SELECT ... FOR UPDATE` on the token row for 5s, `rotate()` blocked **3.52s** and
returned only after the holder committed. One behaviour surfaced there and is recorded rather than
changed: two concurrent refreshes with the same cookie serialise, so the first answers `200` and the
second takes the reuse path and answers `401` — and reuse revokes every live token, including the
winner's, so a two-tab refresh signs the user out. `QA-G4` in `TODO_qa-tester.md` asks for a decision.

### 2026-10-11 — v0.1.23 — M2.1 accounts models

**Context.** `M2.1`. `M2` opens with the custom user model, the one schema decision in this project
that cannot be revisited cheaply: `AUTH_USER_MODEL` has to be settled before anything depends on the
user table, and moving it afterwards means rebuilding the database and repairing migration history
by hand.

**What changed.**

- `accounts/` — new app: `User`, `UserManager`, `Address`, and `accounts/migrations/0001_initial.py`.
- `config/settings/base.py` — `django.contrib.auth` and `accounts` added to `INSTALLED_APPS`,
  `AUTH_USER_MODEL = "accounts.User"`, and `AUTH_PASSWORD_VALIDATORS` set to Django's four defaults.
- `tests/test_accounts_models.py` — 20 tests: the swap itself, password hashing, case-insensitive
  identity, both uniqueness rules, the cascade, and the timestamps.
- `docs/03-architecture/DATA-MODEL.md` — the `accounts.user` table corrected to what was built.

**Decisions taken.**

- **The swap was cheap, and that is worth recording.** `django.contrib.auth` had never been
  installed, so no `auth_user` table existed and no migration referred to the default user. The
  migration is therefore *additive*: `migrate` created the auth tables and `accounts_user` beside
  the catalog, and the 46 seeded products were untouched. Had `auth` been installed at `M0`, this
  milestone would have been a database rebuild instead.
- **Lower-casing replaces `citext`.** `DATA-MODEL.md` asked for a case-insensitively unique `email`
  and named Postgres's `citext`. The tests run on SQLite, which has no `citext`, so the manager
  lower-cases on write and `get_by_natural_key` lower-cases on lookup; uniqueness then rests on an
  ordinary unique constraint. `DATA-MODEL.md` was updated rather than left describing a column that
  does not exist.
- **`get_by_natural_key` carries that case-insensitivity into `authenticate()`**, so sign-in does not
  depend on every caller normalising the address first.
- **The default-address rule is enforced by a partial unique index**, not by application code:
  `CREATE UNIQUE INDEX ... ON accounts_address ("user_id") WHERE "is_default" = 1`. Two addresses
  marked default for one user is a genuine inconsistency, so the database refuses it; the index is
  per user, and a test exists purely to prove a second user's default is still allowed.
- **Django's four default password validators are adopted.** `US-2.1` requires "password with
  validation" without naming rules; the defaults give a length floor and reject common and
  all-numeric passwords.
- **Two scoped `pyright: ignore` directives are accepted on the user model.** `django-stubs` types
  `AbstractBaseUser.Meta` and `PermissionsMixin.Meta` nominally, so every custom user model built
  the documented way is reported as an incompatible override. The alternative — subclassing
  `AbstractUser` — would add columns `DATA-MODEL.md` does not specify, which is the worse trade.

**Impact.** Gates green: `ruff format --check`, `ruff check`, `basedpyright` (**0 errors**) and
`pytest` (**102 tests, up from 82**), plus `makemigrations --check` reporting no drift. Verified
against the development database: the model resolves to `accounts.User`, the columns match
`DATA-MODEL.md`, a mixed-case email is stored lower-cased, `authenticate()` resolves
`ADA@EXAMPLE.COM` and refuses a wrong password, a case-variant duplicate registration is refused by
the database, a second default address is refused while a second user's default is allowed, `12345`
is rejected by the validators, and the 46 seeded products survived the migration. No `auth_user`
table was created, so there is no dead table left behind by the swap.

### 2026-10-10 — v0.1.22 — M1.9 image credits page

**Context.** `M1.9`. `US-6.1` (`Must` — a licensing requirement, per `SCOPE.md`) is the whole
specification: "renders the attribution (creator, license, source URL) for every shipped image from
the manifest". The `ImageCredit` rows, the seed that fills them and the `/pages/credits` route row in
`UX.md` section 4 all already existed; what was missing was a way to read the credits and a page to
render them.

**What changed.**

- `backend/catalog/api.py`, `backend/catalog/schemas.py` — `GET /api/v1/credits`, a public catalog
  route returning all credits unpaginated, with the committed OpenAPI snapshot regenerated.
- `backend/tests/test_catalog_api.py` — three tests: full coverage of the shipped set, the four
  fields `US-6.1` names, and that no shipped image is `ND`-licensed. The existing assertion on the
  exact set of documented paths was deliberately extended.
- `frontend/src/app/pages/credits/page.tsx` — the page: a static shell with the list streamed behind
  a `<Suspense>` boundary.
- `frontend/src/lib/licences.ts` — licence code → Creative Commons deed URL, `null` when unmapped.
- `frontend/src/components/product-gallery.tsx`, `product-card.tsx` — the `BY-ND` comments corrected
  (see below).

**Decisions taken.**

- **The credits are read from the database, not from `manifest.csv` again.** `ADR-0012` keeps the
  manifest as the provenance record, but rendering the imported `ImageCredit` rows means the page and
  the shipped images cannot drift apart.
- **The endpoint is unpaginated.** `US-6.1` wants every image, the catalog ships 46, and they belong
  on one page. `page_size` exists on `/products` because it is a browse surface; this is a legal
  annex.
- **Licence codes link to their deed.** CC's attribution guidance asks for the licence to link to its
  deed wherever the medium allows; `ADR-0012` only requires that the page "demonstrates licence
  awareness". An unmapped code renders as plain text, because a guessed deed URL would claim terms
  the image does not carry.
- **A correction to `M1.6`.** The `M1.6` notes and the gallery's comment claimed 8 of the 46 shipped
  images were `BY-ND`. That was wrong: the vendored manifest holds 100 rows and 8 `BY-ND` images, but
  none of the eight ship — curation drops them, which is what `ADR-0012` requires. The
  `object-contain` rule stands unchanged; the *justification* was wrong, and the comment and the
  `M1.6` runbook bullet now say what is true. A new test asserts no shipped image is `ND`-licensed.

**Impact.** Gates green: backend `ruff format --check`, `ruff check`, `basedpyright` (**0 errors**)
and `pytest` (**82 tests, up from 79**); frontend `typecheck`, `lint`, `format:check`, `test`
(**50, up from 48**) and `build`. `/pages/credits` builds as Partial Prerender (`◐`) like `/` and
`/products`. Verified on ports isolated from the development instance against the seeded SQLite
catalog: the endpoint returns 46 credits with the licence mix 33 `BY-2.0` / 11 `BY-SA-2.0` /
1 `CC0-1.0` / 1 `PDM-1.0` and no `ND`; the page renders one `<h1>`, the count line, 46 credit rows,
all four deed URLs and 46 labelled source links, with `BY-ND` appearing nowhere in the HTML; one page
view costs exactly one API request; `/`, `/products` and a product detail page are unregressed; and
no server-side errors are logged. Regenerating the OpenAPI snapshot is byte-for-byte identical, so
`Backend CI`'s drift check passes.

### 2026-10-10 — v0.1.21 — M1.8 home page

**Context.** `M1.8`. `US-1.5` (`Should`) is the entire specification for this page: "hero plus a
featured grid; fast LCP; primary CTA into the catalog". The hero has no specified content or image,
the home page has no row in the `UX.md` states matrix, and **"featured" is defined nowhere** — not a
model field, not an API parameter, not a curation rule. It appears in the ROADMAP line, that
acceptance criterion and one `UX.md` IA row, and nowhere else. So this milestone had to define it.

**What changed.**

- `app/page.tsx` — the hero in the static shell, the featured row behind a `<Suspense>` boundary.
- `lib/featured.ts` — `selectFeatured`: one piece per category from a price-ordered pool.
- `components/product-card-skeleton.tsx` — extracted, now shared by the catalog grid and the home
  page's row so the two reservations cannot drift from the card they stand in for.

**Decisions taken.**

- **"Featured" is derived, not stored.** An `is_featured` column, a migration, a seed that marks
  products and a `featured` filter on `/api/v1/products` is a backend task with no milestone in the
  ROADMAP, and it would commit a new OpenAPI snapshot inside a page milestone. The row is instead
  selected from what the catalog already says: the priciest product of each category.
- **One piece per category, because variety is the point of the row.** The seed inserts category by
  category, so "newest four" would render four Decor pieces and "priciest four" two Bedroom and two
  Living Room pieces. Measured against the shipped catalog, one per category gives Bedroom
  ($2,185.00), Living Room ($1,881.00), Dining Room ($1,065.00) and Storage ($872.00).
- **It is labelled for what it is.** The heading is "Statement pieces" over "The highest-priced piece
  from each part of the collection". Calling a derived row "featured" would assert something about
  the catalog that nothing in the data supports, and the honest heading reads better anyway.
- **The hero is text and nothing else.** `US-1.5` asks for a "fast LCP"; text keeps the largest paint
  on a heading in the static shell. A photograph would additionally need an LCP decision, a pick from
  the licence-clean set, and — since `ADR-0012` routes attribution to `/pages/credits` rather than
  inline — a visible gap at the page's focal point.
- **No hero display serif.** `UX.md` section 2 offers an optional display face for hero headings;
  staying with Inter keeps the type system to one family and the font payload to one request.
- **The section heading sits outside the Suspense boundary** so the shell reserves the section, and
  the loading state is `FEATURED_COUNT` card skeletons matching the grid's own shapes.
- **The empty state reuses the catalog's copy.** With no products the row renders "No products yet"
  — the string `UX.md` section 5 already fixes — rather than inventing a second way to say it.

**Impact.** `/` builds as Partial Prerender (`◐`), not static: the hero ships in the shell and the
featured row streams. Gates green: `typecheck`, `lint`, `format:check`, `test` (48 tests, up from
42), `build`. Verified against the seeded SQLite catalog on ports isolated from the development
instance: one page view costs exactly one API request (no category list is needed here); exactly one
`<h1>`; the hero, both calls to action and the loading skeleton all ship in the shell; the featured
row renders exactly four cards — Heia Ash Chest Of Drawers $2,185.00, Heia Birch Side Table
$1,881.00, Brisk Ash Dining Chair $1,065.00, Ravn Birch Coat Rack $872.00 — matching the
database-computed expectation for the one-per-category rule precisely, prices descending and four
distinct categories; cards link through to the detail pages; `/products` is unregressed (24 cards,
46 products, filter form intact); and no server-side errors are logged.

### 2026-10-10 — v0.1.20 — M1.7 search, filter and sort

**Context.** `M1.7`. `US-1.3` (Must) asks for keyword search that matches names and keywords, with
an explicit "no results" state carrying a recovery suggestion. `US-1.4` (Should) asks for category
and **price band** filtering plus price/newest sorting, with "the URL reflects the filter state so
results are shareable and back-button safe".

**What changed.**

- `lib/catalog-query.ts` — the URL contract: parse, validate and rebuild the listing state.
- `lib/search-params.ts` — one place that unwraps a repeated query parameter.
- `lib/categories.ts` — flattens the category tree into the options a `<select>` needs.
- `components/catalog-filters.tsx` — search, category, price and sort in one GET form.
- `components/sort-select.tsx` — applies a sort on change, without leaving the form or the URL.
- `Pagination` now carries the filters; `EmptyState` gained a description and an action; the
  skeleton mirrors the filter panel so the grid does not move when it appears.
- `api/client.ts` — `fetchProducts` takes the parsed query; `fetchCategories` feeds the category
  control.

**Decisions taken.**

- **Price bands are links, not form controls.** A band is *two* parameters, and a radio group or a
  `<select>` can submit only one value. A single-value band parameter would create a second
  vocabulary for the URL that could no longer round-trip a hand-typed `min_price`/`max_price` — and
  the URL is precisely what `US-1.4` requires to be shareable. The bands therefore carry `API.md`
  section 4's own parameters, while search, category and sort sit in one GET form that also works
  with JavaScript off.
- **The bands' bounds ride along as hidden inputs.** The form cannot display them, so without this a
  search would silently drop the price filter. Verified in the rendered HTML.
- **Band thresholds are measured, not guessed.** The catalog runs $40–$2,185 with p25 $113, p50 $216
  and p75 $837; $100 / $250 / $750 splits it 11 / 13 / 8 / 14, so no band is decorative. A price
  exactly on a boundary belongs to both neighbours, because `max_price` is inclusive — round numbers
  in a shared URL are worth more than exclusivity on a value no product actually has.
- **Price *bands*, because that is what the acceptance criterion says.** Arbitrary `min_price`/
  `max_price` still work in the URL and still round-trip; the UI simply offers four useful choices
  instead of a pair of money inputs, whose units no form could convert to cents without JavaScript.
- **An unknown category is passed through, not validated away.** The API answers it with zero
  results rather than an error, so validating it in the storefront would turn `US-1.3`'s no-results
  state into a silently unfiltered listing.
- **Anything the API would reject falls back rather than being sent** — a bad `sort`, a `page` below
  one, a negative bound — so a stale or hand-edited link degrades to a valid listing instead of a
  `400` and a retry panel.
- **`SortSelect` submits its own form.** A client component only so that sorting applies on change;
  it calls `requestSubmit()` rather than pushing a URL, keeping the navigation identical to the
  Apply button's and the URL the single source of state.
- **The no-results copy is authored, because the specification does not supply it.** Every reference
  asks for "a recovery suggestion" and never gives the sentence. The state distinguishes an empty
  catalog ("No products yet", fixed by `UX.md` section 5) from a search or filter that matched
  nothing ("No products match", plus a way out).
- **`UX.md` section 8's mobile drawer is deliberately partial.** The panel is a `<details>`, open by
  default, so a phone reader can collapse it with no JavaScript at all. A true overlay drawer —
  focus trap, scroll lock, focus return — belongs to the `M6.2` accessibility pass, where it can be
  tested rather than guessed.

**Impact.** `/products` carries its entire state in the URL. Gates green: `typecheck`, `lint`,
`format:check`, `test` (42 tests, up from 22), `build`, with `/products` still building as Partial
Prerender. Verified end to end against the seeded SQLite catalog on ports isolated from the
development instance: one page view costs exactly two API requests (products + categories); `q=chair`
returns 3 and `q=zzzz` renders the no-results state with its recovery suggestion; the filter counts
match the database exactly (`textiles` 11, `living-room` 6, `max_price=10000` 11, `min_price=75000`
14); `sort=-price` starts at $2,185.00 and `sort=price` at $40.00, with page two of the descending
sort starting at $197.00, which the database independently confirms is the 25th price; the pager link
on a sorted view is `/products?sort=-price&page=2`, so filters survive paging; and
`?sort=cheapest&page=0&min_price=-5` degrades to a valid unfiltered listing rather than a `400`.

### 2026-10-10 — v0.1.19 — M1.6 product detail page

**Context.** `M1.6`. `US-1.2` fixes the content — image gallery, price, description, availability,
and an add-to-cart action, with correct `<title>`/metadata. `UX.md` section 5 gives the PDP a
skeleton for loading and "n/a (404 page)" for empty.

**What changed.**

- `app/products/[slug]/page.tsx` — the gallery beside price, availability, description, material,
  colour and dimensions, with per-product `generateMetadata` (`NFR-6`).
- `app/products/[slug]/not-found.tsx` — what a withdrawn or mistyped slug gets.
- `components/` — `ProductGallery`, `AddToCartButton`, `ProductDetailSkeleton`.
- `lib/dimensions.ts` — labelled dimensions, pure and covered by tests.
- `ProductCard` is now a link to the detail route, which `M1.5` deliberately left out.
- `api/client.ts` — `fetchProduct`, which separates a missing product from an unavailable service.

**Decisions taken.**

- **The `notFound()` check runs inside the `<Suspense>` boundary.** This is the shape the Next docs
  recommend for keeping the shell and loading UI while data loads. The consequence is that a
  missing slug answers `200` rather than `404`, because the response is already streaming by then —
  and Next compensates with `<meta name="robots" content="noindex">`, verified present on a missing
  product and absent on a real one. Blocking the route would buy a `404` status at the cost of the
  skeleton `UX.md` asks for; the noindex tag makes that trade the right way round.
- **The add-to-cart control is genuinely disabled, with its reason in visible text** wired via
  `aria-describedby`. Nothing is specified for a placeholder, and `US-3.1` owns the real behaviour
  at `M3`; a control that pretends to work would be worse than one that explains itself.
- **Nothing is cropped, anywhere.** `ADR-0012` excludes `BY-ND` images "from any cropping or
  alteration", the payload carries no licence for the UI to branch on, and 8 of the 46 shipped
  images are `BY-ND` — so the gallery and the card both use `object-contain`. This also corrects the
  card, which shipped with `object-cover` at `M1.5`. The source ratios are genuinely mixed, so the
  cost is letterboxing.
- **`generateMetadata` is per product**, which `US-1.2` asks for explicitly, and costs no extra
  request: Next memoises the underlying `fetch` across the metadata and the page. Verified by
  counting backend access-log lines for one page view.
- **Material, colour and dimensions are surfaced** because `UX-GOAL-1` asks for price, dimensions
  and stock to be visible before the cart. Dimensions are labelled rather than joined into
  `W × D × H`, since the three fields are independently nullable.
- **The gallery renders one image.** The source set holds one per product; multi-image galleries are
  a deferred decision, not an oversight, and the component renders from the list so more images is a
  data change.

**A bug the tests caught.** `fetchProduct` passed every case while never using the stubbed `fetch`:
`openapi-fetch` captures `globalThis.fetch` when the client is *created*, which happens at module
load, before a test can stub it. So the tests were hitting a real socket and taking the
transport-failure path, and the `503` case only appeared to pass because both paths return
`unavailable`. The client now resolves `fetch` per call, which fixes the tests and removes a real
production risk: a reference captured at import time can predate Next's replacement of `fetch`,
which is what provides the request memoisation above.

**Impact.** `/products/[slug]` builds as Partial Prerender (`◐`), like the listing. Gates green:
`typecheck`, `lint`, `format:check`, `test` (22 tests, up from 14), `build`. Verified end to end
against a real server on ports isolated from the development instance: a real product renders its
name in `<title>` and `<h1>`, its price, "In stock", description, material/colour/dimensions, the
disabled add-to-cart with its note, and a gallery image with `alt` text; exactly one API request
serves the entire view; a missing slug renders the not-found page with `noindex`; catalog cards link
to the detail route; and no server-side errors are logged.

### 2026-10-10 — v0.1.18 — M1.5 catalog listing page

**Context.** `M1.5`, the first page to read the API. Two facts discovered up front shaped it:
`cacheComponents: true` makes the app partial-prerendered by default, and `UX.md` section 5 already
asks for a loading state that this architecture provides for free.

**What changed.**

- `app/products/page.tsx` — the listing. The heading renders from the static shell; the result
  count, the grid, and the pager stream in behind one `<Suspense>` boundary.
- `components/` — `ProductCard`, `ProductGrid`, `ProductGridSkeleton`, `Pagination`, `EmptyState`,
  `RetryPanel`, `RetryButton`. `ProductGrid` exports its column classes so the skeleton reserves the
  identical shape rather than a similar one.
- `api/client.ts` — the `openapi-fetch` client, typed from `paths` in the generated schema.
- `lib/money.ts` and `lib/pagination.ts` — price formatting and page arithmetic, both pure and
  covered by tests.

**Decisions taken.**

- **One `<Suspense>` boundary, and no `loading.tsx`.** The boundary is required — with Cache
  Components an uncached fetch or a `searchParams` read outside one is a build error — and it is
  also the card-skeleton loading state the spec asks for. `loading.tsx` would have replaced the
  heading along with the grid.
- **The listing is deliberately uncached.** `use cache` would place the grid in the static shell,
  but nothing invalidates the catalog yet, so a reseed would keep serving withdrawn products until
  the lifetime expired. Caching wants an invalidation story to go with it.
- **The pager is links, not buttons.** Paging then works with no client JavaScript, and the page
  number lives in the URL — the ground `US-1.4` needs for shareable filter state.
- **A page past the end shows the empty state with the pager intact.** The API returns an empty page
  rather than a `404` precisely so the client need not special-case it; dropping the pager would
  strand a visitor who arrived on such a URL.
- **The grid's column count is a decision, because the spec does not make it.** `UX.md` section 8
  fixes the breakpoints and `ADR-0013` the tokens, but not the columns: one on the smallest screens
  for the large imagery section 1 asks for, then two, three, and four.
- **`parsePage` clamps only to a minimum of one.** A page past the end passes through on purpose,
  because that is the case the empty state exists for.
- **`ProductCard` is neither a link nor a stock indicator.** The detail route arrives at `M1.6`, so
  a link would point at a `404`; `in_stock` belongs to `US-1.2`'s acceptance criteria, not the
  listing's.
- **`PAGE_SIZE` is sent explicitly** rather than relying on the API default, so the skeleton
  reserves exactly as many cards as will arrive.

**A bug that verification caught.** Every build logged six lines of `catalog: GET /api/v1/products
did not complete … During prerendering, fetch() rejects when the prerender is complete`. The
blanket `try`/`catch` in the read client was catching React's *intentional* abort of the deferred
render under Partial Prerendering and reporting it as an unreachable backend — a false alarm that
would have sent someone hunting an outage that never happened. The fix is `unstable_rethrow(error)`
at the top of the catch, which the Next docs prescribe for exactly this case and which name `fetch`
with `cache: 'no-store'` among the APIs concerned. Build noise went from six to zero, while a
genuinely dead backend still logs and still renders the retry panel. `RUNBOOK.md` section 8 records
it.

**Impact.** `/products` builds as Partial Prerender (`◐`) — a static shell with the listing
streamed in — and serves 24 cards per page from a 46-product catalog with a working pager. Gates
green: frontend `typecheck`, `lint`, `format:check`, `test` (14 tests), `build`. Verified end to end
against a real server on ports isolated from the development instance: page one renders 24 cards
and "46 products"; page two renders 22; `?page=99` renders the empty state with a usable pager;
`?page=abc` falls back to page one; with no backend listening the retry panel renders and the page
heading survives; and starting the backend against the same build makes the grid appear with no
rebuild, confirming the read is not cached.

### 2026-10-10 — v0.1.17 — OpenAPI snapshot and generated frontend types

**Context.** `M1.4`. The frontend has to consume the `M1.3` contract without the two drifting
apart, which `API.md` section 10 already commits to. Two constraints decided the shape: `Frontend
CI` runs with no backend and is path-filtered to `frontend/**`, and a Vercel build cannot fetch a
schema from a live API.

**What changed.**

- `manage.py export_openapi_schema` writes the contract to `frontend/openapi.json`. django-ninja
  ships a command of its own, but Django only discovers management commands from applications in
  `INSTALLED_APPS`, and `ninja` is not one; its default also resolves the API instance at `/api/`,
  where this project mounts `/api/v1`. The wrapper pins both.
- `frontend/openapi.json` — the committed snapshot: 19.6 KB, four paths, fourteen schemas.
- `openapi-typescript` generates `frontend/src/api/schema.d.ts` from it via `pnpm codegen`, wired
  into `pnpm dev`, `pnpm build`, and `pnpm typecheck`. The generated file is gitignored, so a fresh
  clone needs no extra step.
- `Backend CI` regenerates the snapshot and fails on any difference, and `frontend/openapi.json` is
  now a path trigger for that workflow, so a hand-edited snapshot is caught as well.

**Decisions taken.**

- **The snapshot lives inside `frontend/`.** Vercel builds with `frontend` as its root directory, so
  `../backend/openapi.json` would not exist during a deploy. That one constraint rules out keeping
  the snapshot beside the API it describes.
- **The generated TypeScript is not committed.** The snapshot is the artifact under review; a
  committed generated file would be a copy of a copy, and `pnpm typecheck` rebuilds it anyway.
- **Formatting of the snapshot is owned by the generator, not Prettier.** `prettier --check` failed
  on it — Prettier collapses short arrays onto one line where `json.dumps` does not — so it is in
  `.prettierignore`. Without that the drift check could never pass, because the two tools disagree
  about the same bytes by construction.
- **`indent=2` and sorted keys** in the export, so a contract change shows up as the lines that
  actually changed rather than a reordered file.

**Corrected.** `RUNBOOK.md`'s `M1.3` section did not land with `v0.1.16`: that patch contained two
hunks, the second failed to anchor, and the tool discards the whole file when any hunk fails. The
section is added here, together with the `M1.4` one.

**Impact.** The contract has one source and a check that enforces it. Gates green — backend:
`ruff format --check` (39 files), `ruff check`, `basedpyright` (0 errors), `makemigrations --check`,
79 tests; frontend: `typecheck`, `lint`, `format:check`, `test`, `build`. The drift check was
verified in both directions: exit 0 on a matching snapshot, and exit 1 with the diff printed when
the snapshot is stale.

### 2026-10-10 — v0.1.16 — M1.3 catalog read API and the error envelope

**Context.** `M1.3` turns the seeded catalog into a contract the storefront can consume. It is the
first API surface, so the cross-cutting pieces land with it: the error envelope and the generated
OpenAPI schema.

**What changed.**

- `catalog/api.py` — four public routes under `/api/v1`: `GET /categories`, `GET /categories/{slug}`,
  `GET /products`, and `GET /products/{slug}`. The listing route carries pagination, filtering
  (`category`, `q`, `min_price`, `max_price`), and sorting (`name`, `price`, `-price`, `newest`).
- `catalog/schemas.py` — the response shapes. **The listing does not nest variants; the detail
  route does**, by decision: a grid never renders variants, and nesting them would multiply every
  card payload for data it does not show.
- `core/errors.py` — one error envelope, `{"error": {code, message, details, request_id}}`, per
  `API.md` section 3 (`NFR-4`). Ninja's defaults are replaced on three counts: it answers request
  validation with `422` and `{"detail": ...}` where the contract says `400` with the envelope, it
  reports a bare list rather than `{field, issue}` pairs, and in production it *re-raises* an
  unhandled exception, which produces an error body that is not JSON at all. The `request_id`
  matches the `X-Request-ID` header the middleware already sets.
- `config/api.py` — installs the error handlers and mounts the catalog router at the API root.

**Decisions taken.**

- **Filters and pagination belong to `M1.3`.** Shaping the contract once is cheaper than adding
  query parameters after `M1.4` has generated client types from it.
- **`min_price` and `max_price` are integer cents**, matching the payload convention in `API.md`
  section 1, so no client converts to a decimal in order to filter.
- **An unknown `category` filter returns zero results, not an error**; an unknown *slug* on a detail
  route is a `404`. The storefront needs a no-results state (`US-1.3`), not an error state.
- **`category` also matches descendants.** The model supports nesting even though the seed is flat,
  and a parent filter that silently dropped its children would be a latent bug.
- **`page_size` caps at 100, `page` must be at least 1, and `sort` is an enum**; anything else is a
  `400`. A page past the end is an empty page rather than a `404`, so the client renders "no more
  results" without special-casing.
- **Ordering always ends with a tiebreaker**, so a page boundary cannot shuffle between requests.
- **The listing omits `attributes`.** It holds seed bookkeeping — the curated keyword and series —
  rather than anything customer-facing.

**One `M1.1` assumption corrected.** `ADR-0014` recorded that `basedpyright` cannot see reverse
foreign keys, and suggested `prefetch_related` as part of the workaround. Writing this API showed
the limitation is wider, and the suggestion does not work: an implicit primary key (`id`) and
foreign-key attnames (`parent_id`, `product_id`) are equally invisible, because django-stubs
generates all of them in its *mypy* plugin and its own stub file states that other type checkers
will not understand them; and reading prefetched rows still needs the inaccessible accessor. So
`catalog/api.py` reads rows with `values()` and reaches related rows through
`filter(product__slug=...)`, never touching a plugin-synthesised attribute. `RUNBOOK.md` section 8
now carries both halves of the limitation.

**Impact.** The storefront has a contract: 46 products, 7 categories, and 95 variants behind four
public routes, with the OpenAPI schema at `/api/v1/openapi.json` for `M1.4` to generate types from.
Gates green: `ruff format --check` (38 files), `ruff check`, `basedpyright` (0 errors),
`makemigrations --check` (no drift), and 79 tests passing on both SQLite and PostgreSQL 17 — the
suite grew from 49. The CLI was exercised against PostgreSQL 17 as well, which confirmed the
JSON-keyword search behind `?q=` behaves identically on JSONB and on SQLite. That was the one
genuinely database-specific risk in the contract, and it is now covered by a test on both.

### 2026-10-10 — v0.1.15 — BY-ND images dropped; reverse-relation typing recorded

**Context.** Three founder decisions taken immediately after `v0.1.14`. The first reverses a
decision recorded there, and is recorded here rather than by editing that entry, because this
file is append-only.

**What changed.**

- **No `BY-ND` image ships.** `v0.1.14` shipped the bed frame, bookshelf, and dining table under
  `BY-ND-2.0`, on the grounds that `ADR-0012` permits that licence when the work is never
  altered. That reading is correct, but it hands every future layout a constraint that nothing
  checks: a grid which crops or resizes one of those files has created a derivative, and no gate
  would catch it. All three are now dropped — files removed from `frontend/public/images/`
  (49 → 46 images, 3.4 MB → 3.2 MB) and their keywords removed from the curation, so 54 of the
  100 source keywords ship rather than 51. Every vendored image is `BY`, `BY-SA`, `PDM`, or
  `CC0`, and safe to crop and resize.
- **Products fall 49 → 46 and variants 100 → 95.** "Dining Room" seeds two products now, and
  "Bedroom" and "Storage" one fewer each. `SEED` is untouched, but removing curated entries
  shifts the order that the every-tenth out-of-stock rule counts along; the number of
  out-of-stock products stays five, which the tests assert.
- **`ALLOWED_LICENCES` no longer admits `BY-ND-2.0`**, and
  `test_no_derivative_restricted_image_ships` fails if one ever reappears, so the reversal
  cannot be undone by accident.
- **`ADR-0014` records the reverse foreign-key strategy: query explicitly.** `basedpyright`
  cannot see accessors such as `product.images` — django-stubs supplies reverse relations
  through a *mypy* plugin, and pyright has no plugin mechanism — so code reaches relations
  through the manager (`ProductImage.objects.filter(product=product)`), which stays fully typed.
  Relation names as strings are allowed where the query wants them
  (`prefetch_related("images")`); casting a reverse accessor is not. The alternative was
  replacing the type checker, which `M0` had settled.
- **Single-image products stand, by decision.** The source set holds exactly one image per
  keyword, so `M1.6`'s gallery renders one image per product for now. Multi-image galleries are
  deferred deliberately, not overlooked.
- Counts in `ROADMAP.md`, `RUNBOOK.md`, and the `seed_data.py` docstring follow the new curation.

**Impact.** `manage.py seed` builds the 46-product catalogue in one command and stays safe to
re-run. Gates green: `ruff format --check` (34 files), `ruff check`, `basedpyright` (0 errors),
`makemigrations --check` (no drift — the curation change needed no migration), and 49 tests
passing on both SQLite and PostgreSQL 17. The CLI was exercised against a real PostgreSQL 17
database with the same result every time: `migrate`, `seed`, a second `seed` leaving the counts
untouched, and `seed --reset`, each ending at 7 / 46 / 95 / 46 / 46.

### 2026-10-10 — v0.1.14 — M1.2 catalog seed landed

**Context.** `M1.2` turns the `M1.1` schema into a browsable catalog and settles the
`some_source/` question: the reference image set lives outside the repository, while `ADR-0012`
requires `manifest.csv` to be kept inside it.

**What changed.**

- **The image set is vendored into the repository.** 49 curated images move to
  `frontend/public/images/` (3.4 MB), and `manifest.csv` is copied byte-for-byte to
  `backend/seed_data/manifest.csv`. `ADR-0012`'s provenance requirement now holds, and the seed
  can run in CI and on the deployed demo instead of only on the founder's machine.
- `catalog/seed_data.py` — curation as data: which of the 100 source keywords ship, into which of
  7 categories, plus the series/material/finish, price-band, and dimension vocabulary. The source
  set covers a whole house, so appliances, cleaning tools, and kitchenware are excluded by
  omission; 51 keywords never ship.
- `catalog/seeders.py` — 7 categories, 49 products, 100 variants, 49 images, 49 credits.
- `catalog/migrations/0002` and `0003` — uniqueness on `ImageCredit.source_page_url` and
  `(ProductImage.product, path)` so upserts are idempotent, plus `ImageCredit.title` widened to 300.
- `core/seeding.py` — rewritten as declarative discovery. `M0.8` registered steps as an import
  side effect, which is unsound: Python caches modules, so after any registry reset the step
  vanished silently and `manage.py seed` would do nothing without erroring.
- `tests/test_catalog_seed.py` added; `tests/test_seed.py` now injects steps per test instead of
  mutating global state.

**Decisions taken.**

- **Curation is data, not code.** One mapping drives the seed, the vendored images, and `M1.9`'s
  credits page, so they cannot disagree. `seed()` fails loudly when a curated keyword is absent
  from the manifest.
- **`random.Random(SEED)`, not Faker.** `DATA-MODEL.md` §7 says "a deterministic Faker seed".
  Faker is not used: its prose is generic, and `UX.md` §9 asks for plain, warm copy. Determinism —
  the actual requirement — comes from a seeded generator plus curated copy templates.
  `seeders.SEED` changes the whole catalog.
- **Out-of-stock is deliberate.** Every tenth curated product is seeded with no stock, so the
  storefront always has that state to render. Left to `randint(0, 40)` it never occurred at all.
- **Three `BY-ND` images ship unaltered.** `ADR-0012` permits `BY-ND` only if never modified, and
  dropping them would strip the dining table, bookshelf, and bed frame. They are copied verbatim
  and must never be cropped or re-rendered; a test pins the exact set.
- **Images are served by Next.js, not Django.** `ProductImage.path` holds a root-relative URL
  (`/images/armchair.webp`) — cheaper than streaming files through the API, and it matches the
  Vercel deployment.
- **`--reset` clears the whole catalog**, because nothing yet distinguishes seeded rows from
  operator-created ones. That becomes a real hazard at `M5`.

**Two problems PostgreSQL found that SQLite could not see.**

1. `alt` text overflowed `varchar(200)`. It concatenated the product name with the photo's source
   title, and those titles run to 255 characters — while the median is 24.5, so the silent SQLite
   run looked like success. `ImageCredit.title` had the same latent overflow and was widened.
2. The missing out-of-stock state above: a case the UI needs that the generator happened not to
   produce.

Both are now guarded by `full_clean()` over every seeded row, since SQLite does not enforce
`max_length`.

**Impact.** `manage.py seed` builds the catalog in one command and is safe to re-run. Gates green:
`ruff format --check` (34 files), `ruff check`, `basedpyright` (0 errors), `makemigrations --check`
(no drift), and 49 tests passing on both SQLite and PostgreSQL 17. The CLI was also exercised
against a real PostgreSQL 17 database: `migrate`, `seed`, a second `seed` with identical row
counts, and `seed --reset`, ending at 7 / 49 / 100 / 49 / 49.

**A tooling note worth recording.** The `M1.1` RUNBOOK section that `apply_patch` reported as
applied in `v0.1.12` was never written to disk. It was found missing during this increment,
confirmed absent from the `9389b73` commit, and is now added together with the `M1.2` section.
Every other document change from that patch did land. Document edits now get read back rather than
trusted.

### 2026-10-10 — v0.1.13 — M0 complete, CI confirmed green

**Context.** `M0` could not be closed while its second exit criterion was unverifiable. The
founder pushed `9389b73`, which closed the loop and confirmed the `v0.1.11` CI fix.

**What was confirmed.**

- **`Backend CI` run #2 on `9389b73` — success, 42s.** This is the first time the backend job has
  ever actually executed: run #1 died at "Set up job" on the bad `setup-uv` pin. The job now
  genuinely runs `ruff format --check`, `ruff check`, `basedpyright`, and `pytest` against a
  PostgreSQL 17 service.
- **`Frontend CI` — success on `7b06e88`.** It did not re-run for `9389b73`, because the workflow
  is path-filtered to `frontend/**` and nothing under `frontend/` changed between the two
  commits, so that green still describes the current tree.
- **`docker compose up` runs API + web** — verified during `M0.7`.

Both exit criteria now hold, so `M0` is marked `[x]` in `ROADMAP.md`.

**Impact.** All ten `M0` increments are complete and the delivery pipeline is green for the first
time. The lesson from `v0.1.11` is why this entry exists: a workflow that has never run is not
evidence of anything, and only a push can establish that it has. `RUNBOOK.md` §6 now carries that
caveat, including the path-filter subtlety above.

### 2026-10-10 — v0.1.12 — M1.1 catalog models landed

**Context.** M1 begins: the catalog gets its physical schema, so `M1.2` can seed it and `M1.3`
can serve it.

**What was added.**

- A `catalog` app with `Category`, `Product`, `ProductVariant`, `ProductImage`, and
  `ImageCredit`, following `DATA-MODEL.md` §2. Money is integer cents throughout;
  `Product.attributes` is JSONB for specs that do not warrant a column.
- `core/models.py` — `TimeStampedModel`, the abstract base giving every table
  `created_at` / `updated_at` as `DATA-MODEL.md` §2 requires.
- `catalog/migrations/0001_initial.py` — generated, reviewed, unmodified.
- `tests/test_catalog_models.py` — 13 tests: `__str__` labels, unique slugs and SKUs, category
  nesting, `PROTECT` on `Product.category`, cascades to variants and images, `SET_NULL` on an
  image's credit, orderings, and rejection of negative money and stock.

**Decisions taken.**

- **`Product.category` is `PROTECT`; `ProductImage.credit` is `SET_NULL`.** `DATA-MODEL.md`
  lists both as foreign keys without an `on_delete`. Deleting a category must not silently take
  its products with it, and deleting a credit must not delete the image that uses it.
- **Each concrete `Meta` subclasses `TimeStampedModel.Meta`.** Two reasons: Django sets
  `abstract=False` on a base `Meta` before installing it, so a subclassing child stays concrete
  (verified — all five report `_meta.abstract is False`), and basedpyright would otherwise
  raise `reportIncompatibleVariableOverride` on every `Meta`.
- **All five models declare `Meta.ordering`.** Deterministic defaults keep pagination stable
  once `M1.5` and `M1.7` add paging and sorting over these tables.
- **`basedpyright` now covers `catalog`.** Its `include` list named only `config`, `core`, and
  `tests`, so the new app would otherwise have escaped type checking entirely.
- **`ImageCredit` maps the manifest by column:** `source_title → title`, `creator → creator`,
  `license → license`, `source → source`, `source_page → source_page_url`. The names differ
  between the manifest and `DATA-MODEL.md`; `M1.2` owns the import.

**Impact.** The catalog schema exists, migrates cleanly, and matches the models exactly. Backend
gates green: `ruff format --check` (31 files), `ruff check`, `basedpyright` (0 errors),
`makemigrations --check` (no drift), and `pytest` — 30 passed on SQLite and 30 passed against
PostgreSQL 17.

One limitation is now recorded in `RUNBOOK.md` §8 rather than hidden: **basedpyright cannot see
reverse foreign-key accessors**, so `category.children` and `product.images` are untyped. The
tests query explicitly instead. This needs a decision — and an ADR — before `M1.3`.

### 2026-10-10 — v0.1.11 — Backend CI unblocked (setup-uv pin corrected)

**Context.** The first push of the `M0.9` workflows revealed that `Backend CI` had been failing
since the moment it was created. Only a push could surface this: the assistant commits locally
and cannot run GitHub Actions.

**What happened.** The run died at "Set up job" with
`Unable to resolve action 'astral-sh/setup-uv@v8', unable to find version 'v8'`, before a single
gate executed. The pin came from a web search that reported `v8.3.2`. Setup-uv does publish full
versions from `v8.3.2` through `v10.3.0`, but it **stopped publishing floating major tags after
`v7`**, so `v8`, `v9`, and `v10` do not exist.

**What changed.**

- `backend.yml` pins `astral-sh/setup-uv@v10.3.0`, confirmed against the repository's tag list
  *and* its `action.yml` rather than a search result.
- CI pins uv to `0.12.5`, matching `backend/Dockerfile`. It would otherwise have installed the
  latest uv while the container ran `0.12.5` — silent drift between the two paths.
- The failure mode is recorded in `RUNBOOK.md` §8 so the next person checks the tag list first.

**Impact.** `Frontend CI` passed on the same push, which retroactively confirms `checkout@v6`,
`pnpm/action-setup@v4`, and `setup-node@v7` all resolve. **The corrected pin is still unverified
until the next push** — this entry records a fix, not a green run. `M0` therefore stays `[~]`;
it closes when a push shows `Backend CI` green.

### 2026-10-10 — v0.1.10 — Tailwind CSS adopted (revises M0.2)

**Context.** The founder reversed the `M0.2` "no styling framework" decision before the catalog
UI is built, so the storefront is written in one styling system instead of two. Recorded as
`ADR-0013` — the ADR the `v0.1.6` entry asked for.

**What changed.**

- `ADR-0013-tailwind-css.md` — the decision, the options considered, and the consequences; added
  to the decision index in `ARCHITECTURE.md` §11.
- `tailwindcss` and `@tailwindcss/postcss` 4.3.3, plus `postcss` 8.5.29, as frontend
  devDependencies, wired through a new `postcss.config.mjs`.
- `src/app/globals.css` — rewritten around `@import "tailwindcss"` and a `@theme` block that
  declares the `UX.md` §2 tokens, so Tailwind generates utilities from them. A small
  `@layer base` keeps the rules that must hold on every route: the `:focus-visible` ring
  (`UX.md` §7), heading line-height and `text-wrap: balance`, the anchor colour, and the body
  background and text colours.
- `src/app/page.tsx` — the placeholder composes utilities now, and `src/app/page.module.css` is
  deleted, retiring CSS Modules.
- `frontend/README.md` — the styling convention points at Tailwind and the `@theme` block.

**Decisions taken.**

- **Token *declaration* moves; token *values* do not.** `UX.md` §2 stays the source of truth —
  the values are declared in `@theme` instead of as standalone custom properties. No colour,
  size, or measure changed.
- **Custom theme entries only where Tailwind's defaults differ.** The project's 4px spacing scale
  and its 8px/16px radii are exactly Tailwind's defaults, so no `--spacing-*` or `--radius-*`
  entries were added: `p-4` and `rounded-lg` already mean the token values. Only the palette, the
  type scale, the 70ch measure, and the font stack needed declaring.
- **A `@layer base` for cross-cutting rules.** The focus ring is an accessibility requirement on
  every route (`UX.md` §7), so it stays global rather than being repeated per component and
  eventually forgotten.
- **The `v0.1.6` entry is not rewritten.** It was accurate when written; this entry and
  `ADR-0013` record the reversal, per the append-only rule.

**Impact.** The frontend styles through one system, and `M1.5`–`M1.9` are written in it from
their first commit. Frontend gates green: `typecheck`, `lint`, `format:check`, `vitest`
(2 passed), and `build`. The build is the meaningful check — Tailwind only fails loudly when
PostCSS compiles the CSS — and the emitted stylesheet was inspected directly: 7.6 KB containing
the palette (`#faf7f2`), the `70ch` measure, and the generated `max-w-measure`, `text-muted`,
and `tracking-tight` utilities, with the `focus-visible` and `text-wrap` base rules intact.

### 2026-10-10 — v0.1.9 — M0.8 seed command skeleton landed

**Context.** The last M0 increment: a seeding entry point that later milestones fill in, so the
command's contract is fixed before there is any data to seed.

**What was added.**

- `core/seeding.py` — a registry of `SeedStep` entries. A step carries a `name`, an idempotent
  `run` callable, and an optional `clear` hook used by `--reset`.
- `core/management/commands/seed.py` — `manage.py seed`. Runs every registered step in
  registration order inside a single transaction; `--reset` calls each `clear` hook first, in
  reverse registration order.
- `tests/test_seed.py` — nine tests covering ordering, the `--reset` hook, steps with no
  `clear`, the empty-registry path, fail-fast, and the registry's snapshot semantics.

**Decisions taken.**

- **A registry, not hard-coded seeding.** With no models until `M1.1`, the only way to make the
  two properties the roadmap asks for — *idempotent* and `--reset` — real and testable is for
  the command to execute something. The registry is that seam: `M1.2` registers the catalog
  seeders without touching the command.
- **One transaction for the whole run.** A failure part-way through leaves neither a
  half-seeded database nor, under `--reset`, a wiped-but-unfilled one. The run aborts instead of
  reporting success, which `test_a_failing_step_aborts_the_run` pins.
- **`clear` hooks run in reverse registration order**, so rows are deleted before the rows they
  depend on.
- **Idempotency is a contract on each step, not something the command can enforce.** The
  skeleton proves the command's mechanics; every real seeder is responsible for its own
  re-runnability, and `M1.2` must cover that with its own tests.

**Impact.** Every M0 increment has landed, and `uv run python manage.py seed` runs with and
without `--reset`. Backend gates green — `ruff format --check` (26 files), `ruff check`,
`basedpyright` (0 errors), `pytest` (17 passed, up from 8).

The M0 milestone row stays `[~]` rather than `[x]`: its exit criteria include "CI passes", and
the `M0.9` workflows have not yet run on GitHub, because pushing is the founder's call
(`WORKING-AGREEMENT.md` §1.4). M0 closes once the first push goes green.

### 2026-10-10 — v0.1.8 — M0.9 continuous integration landed

**Context.** With the compose stack proven, M0.9 wired the quality gates into GitHub Actions so
a push or a pull request is checked without anyone running the commands by hand.

**What was added.**

- `.github/workflows/backend.yml` — `ruff format --check`, `ruff check`, `basedpyright`, and
  `pytest`, on Python provisioned by `uv` from the lockfile.
- `.github/workflows/frontend.yml` — `pnpm typecheck`, `lint`, `format:check`, `test`, and
  `build`, on Node 24 with the pnpm store cached.
- Both are path-filtered (`backend/**` and `frontend/**`), so a change to one app does not run
  the other's gates; each also re-runs when its own workflow file changes.

**Decisions taken.**

- **Native path filters across two workflows.** The roadmap asks for "path-filtered jobs".
  Job-level filtering inside a single workflow needs a third-party action such as
  `dorny/paths-filter`; two workflows using `on.push.paths` / `on.pull_request.paths` reach the
  same result with no extra dependency. The trade-off is that a docs-only change reports no
  checks at all instead of a green skip. Acceptable while `main` is unprotected.
- **The backend job runs a real PostgreSQL service.** Settings fall back to SQLite only when
  `DATABASE_URL` is empty, so leaving it unset would have tested an engine the project never
  deploys on. The job provisions PostgreSQL 17 — the same version as `compose.yml`.
- **Actions are pinned to major tags** (`checkout@v6`, `setup-uv@v8`, `pnpm/action-setup@v4`,
  `setup-node@v7`) rather than commit SHAs. Major tags are the ecosystem norm and stay readable;
  SHA pinning is the stronger supply-chain posture and is worth revisiting before the project
  faces real customers.
- `pnpm` is pinned to `12.3.4` in the workflow to match `packageManager` in
  `frontend/package.json`; the two must move together.
- Concurrency groups cancel a superseded run on the same ref, so a quick second push does not
  queue behind the first.

**Impact.** The CI configuration is complete and was validated locally with `actionlint`, and
the backend suite was re-run against PostgreSQL 17 before the commit. The workflows have
**not** executed on GitHub — the working agreement has the assistant commit locally and the
founder decide when code reaches GitHub — so the M0 exit criterion "CI passes" stays unverified
until the first push. M0 is down to `M0.8` (seed command).

### 2026-10-10 — v0.1.7 — M0.7 compose stack landed

**Context.** Both apps booted on the host; M0.7 made the whole system start with one command so
a reviewer can run the demo without installing Python, Node, or Postgres.

**What was added.**

- `compose.yml` — Postgres 17, the API, and the web app, with health-gated start ordering and a
  named `db-data` volume. Every connection value comes from the environment with a local
  default, so `docker compose up --build` needs no `.env` file.
- `backend/Dockerfile` — `python:3.13-slim` with `uv`; dependencies install from the lockfile
  into `/opt/venv` in a cached layer, then the source is copied. Runs Uvicorn on the ASGI app.
- `frontend/Dockerfile` — multi-stage Node 24 with `pnpm`; dependencies install from the
  lockfile, `pnpm build` runs in the builder, and the runner starts the built app.
- `backend/.dockerignore`, `frontend/.dockerignore` — keep host artefacts (`.venv`,
  `node_modules`, `.next`, `db.sqlite3`) and the local `.env` out of the build context.

**Decisions taken.**

- The API container runs `manage.py migrate --noinput` before Uvicorn. Migrations are
  idempotent, so a fresh volume needs no manual step and a restart is harmless.
- The Postgres port is **not** published to the host by default. Only database clients need it,
  and leaving it closed avoids a collision on a machine that already runs Postgres; the entry
  ships commented in `compose.yml`.
- The web image runs the **production** build (`pnpm build` → `pnpm start`) rather than
  `pnpm dev`, so the container exercises the artefact that actually ships. A Next.js
  `standalone` output would shrink the image further, but it interacts badly with `pnpm`'s
  symlinked `node_modules`; that optimisation is deferred until image size matters.
- No source bind-mounts. Compose is the "does the whole system work together" path; the fast
  edit loop stays on the host (`uv run uvicorn --reload`, `pnpm dev`), as the runbook documents.

**Impact.** `docker compose up --build` brings up all three services from a clean checkout.
Remaining M0 items: `M0.9` CI, then `M0.8` seed command.

### 2026-10-09 — v0.1.6 — M0 frontend skeleton landed

**Context.** With the backend skeleton committed, M0 continued with the Next.js application so
both apps boot and the quality gates cover both sides.

**What was added.**

- `frontend/` — Next.js 16.4 (App Router, RSC, Turbopack) with TypeScript `strict`, managed by
  `pnpm`.
- The design tokens from `UX.md` §2 are now the single source of truth in
  `src/app/globals.css` (the `--lys-*` custom properties), with a minimal base layer: warm
  canvas, ink text, a visible `:focus-visible` ring, and image defaults.
- `src/app/layout.tsx` — `lang="en"`, Inter through `next/font`, LYSHEIM metadata.
- `src/app/page.tsx` — a minimal branded placeholder (one `<h1>`, one `<main>` landmark).
- Tooling: ESLint 9 flat config (`core-web-vitals` + `typescript` + `eslint-config-prettier`),
  Prettier, `vitest`, and a root `.editorconfig`.
- Gate scripts: `typecheck`, `lint`, `format:check`, `test`, `build`.
- `src/lib/config.ts` — `getApiBaseUrl()` reads `NEXT_PUBLIC_API_BASE_URL` with a localhost
  fallback, covered by two tests.
- `frontend/.env.example` documenting `NEXT_PUBLIC_API_BASE_URL`.

**Decisions taken.**

- **No styling framework.** The docs specify design tokens in `globals.css` and never mention
  Tailwind, so the scaffold uses plain CSS with `--lys-*` tokens plus CSS Modules. Adopting a
  CSS framework is deferred to its own ADR before the catalog UI is built at `M1.5`.
- `typecheck` runs `next typegen && tsc --noEmit` — Next 16 generates `LayoutProps` and the
  route types, so a bare `tsc --noEmit` fails on a fresh checkout.
- The vitest config uses the `.mts` extension so Vite loads it as ESM.
- `@types/node` raised to `^24` to match the Node runtime and satisfy `vitest@5`'s peer range.

**Impact.** Both applications boot. Backend gates unchanged and green. Frontend gates green:
`lint`, `format:check`, `vitest` (2 passed), `typecheck`, `build` (4 static pages). Boot smoke
test: `GET /` returns 200 and renders `LYSHEIM`. Remaining M0 items: `M0.7` compose, `M0.8`
seed command, `M0.9` CI.

### 2026-10-09 — v0.1.5 — M0 backend skeleton landed

**Context.** Planning closed at v0.1.4. M0 (foundations) began with the backend skeleton —
the Django 6 + Django Ninja service every later increment builds on.

**What was added.**

- `backend/` — a `uv`-managed project: `config/` (settings split `base`/`dev`/`prod`, URL
  config, Ninja API instance, ASGI and WSGI entrypoints), `core/` (request-ID middleware,
  health view, JSON log formatter), `manage.py`, `pyproject.toml`, `uv.lock`, `.env.example`,
  `README.md`.
- `GET /healthz` returns `{"status": "ok", "request_id": ...}` and always sets an
  `X-Request-ID` response header, echoing a caller-supplied value when present.
- API surface under `/api/v1`: `GET /api/v1/openapi.json` and `GET /api/v1/docs`.
- `tests/` — four pytest tests covering the health contract and the OpenAPI schema.
- Configuration is environment-only (`django-environ`), with a SQLite fallback so a bare
  checkout and the test suite run without infrastructure; PostgreSQL is used via
  `DATABASE_URL`.

**Decisions taken.**

- `uvicorn[standard]` added as a runtime dependency — it serves both local runs and the
  Render deploy, and `uv run uvicorn config.asgi:application` is the documented run command.

**Impact.** First application code in the fresh-start repository. All gates green:
`ruff format --check` (19 files), `ruff check`, `basedpyright` (0 errors), `pytest` (4
passed). ASGI smoke test: `/healthz` → `200`, `/api/v1/openapi.json` → `200`. `PLAN.md` is
unchanged at v0.1.4.

### 2026-10-09 — v0.1.4 — Quality standards baselined (planning phase complete)

**Context.** Stage 5 (cross-cutting) produced the security, review, and collaboration
standards, closing the planning phase.

**What was added.**

- `06-quality/SECURITY-BASELINE.md` — scope and data classification, trust boundaries, a
  STRIDE threat model, twelve findings (`SEC-FIND-1.1..12`) with risk and remediation, a
  secure-configuration baseline, detection/incident-response, and privacy handling.
- `06-quality/CODE-REVIEW-STANDARD.md` — the review ritual, severity levels, and the checklist
  that must pass before any commit.
- `06-quality/AGENT-TOPOLOGY.md` — the founder/assistant/tester-agent topology, handoff
  contracts, communication protocol, memory model, failure recovery, and evaluation signals.
- `_working/TODO_cybersecurity.md`, `TODO_code-reviewer.md`, `TODO_multi-agent-orchestrator.md`.

**Impact.** `PLAN.md` re-baselined to v0.1.4. **The planning phase (Stages 0–5) is complete.**
No application code written yet; the next step is M0 (foundations).

### 2026-10-09 — v0.1.3 — Delivery plan baselined

**Context.** Stage 4 (delivery) turned the workstreams into a sequenced, incremented roadmap
and formalised delivery governance.

**What was added.**

- `04-delivery/ROADMAP.md` — milestones `M0`–`M8` with concrete increments, sequencing and
  dependencies, RACI, Definition of Done, and change control.
- `04-delivery/RISK-REGISTER.md` — the full register `RISK-1..9`, reviewed at every milestone
  gate.
- `04-delivery/RUNBOOK.md` — the runbook skeleton, filled in one entry per increment.
- `_working/TODO_technical-lead.md` — raw technical-lead file; `_working/TODO_technical-project-manager.md`
  extended with the Stage 4 items.

**Impact.** `PLAN.md` re-baselined to v0.1.3. No application code written yet.

### 2026-10-09 — v0.1.2 — Architecture baselined

**Context.** Stage 3 (architecture) produced the system, domain, and API designs and closed
the three product decisions deferred from Stage 2.

**What was added.**

- `03-architecture/ARCHITECTURE.md` — C4 context, container, and component views; bounded
  contexts; integration flow; NFR architecture; deployment topology; a Phase 2 data-platform
  outline.
- `03-architecture/DATA-MODEL.md` — ERD, tables, enumerations, indexes, money handling,
  migration and seeding strategy.
- `03-architecture/API.md` — REST contract, conventions, error envelope, and endpoints.
- `decisions/ADR-0005..0012` — API style, async & tasks, operator console, cart & guest
  merge, auth & tokens, mock-first payments, deployment stack, and image licensing.
- `_working/TODO_*` — raw system-architect, backend, frontend, data-engineer, and
  cloud-engineer files.

**Decisions closed.** `D1` → Django admin as the v1 operator console (`ADR-0007`). `D2` →
server-side cart with a guest cookie merged on login (`ADR-0008`). `D3` → in-memory access
token plus an httpOnly refresh cookie (`ADR-0009`).

**Impact.** `PLAN.md` re-baselined to v0.1.2. No application code written yet.

### 2026-10-09 — v0.1.1 — Product scope baselined

**Context.** Stage 2 (product) produced the curated scope and UX documents.

**What was added.**

- `02-product/SCOPE.md` — personas, epics `EPIC-1..7`, user stories with acceptance
  criteria, in/out of scope, NFRs `NFR-1..9`, and the v1 Definition of Done. Three open
  decisions (`D1` operator-console form, `D2` guest cart, `D3` token storage) are deferred to
  Stage 3.
- `02-product/UX.md` — visual language and design tokens, information architecture, key
  flows, states matrix, component inventory, accessibility and responsive requirements, and
  the validation plan.
- `_working/TODO_technical-project-manager.md`, `_working/TODO_ui-ux.md` — raw agent files.

**Impact.** No change to the plan itself; product detail elaborated. `PLAN.md` re-baselined
to v0.1.1. No application code written yet.

### 2026-10-09 — v0.1.0 — Project reset and re-baseline

**Context.** The repository previously contained a complete earlier iteration of this
project (brand `NORDVIK`) that was erased in commits `1bb7969` ("erase content") and
`64550f3` ("erase all"). The founder chose a **fresh start**: re-plan the project from zero
rather than resume the prior code, reusing the prior *documentation conventions* because
they were sound.

**Decisions taken in this baseline.**

- Fresh start; prior work treated as discarded (recoverable at `d23c8de` if ever needed).
- Brand **LYSHEIM** adopted (`ADR-0003`).
- Monorepo structure with `backend/`, `frontend/`, `docs/` (`ADR-0001`).
- Documentation and change-control convention reused (`ADR-0002`).
- Working agreement adopted: small increments, quality gates, unit tests, local commit
  without push, scenario-based QA, seeding, environment segregation (`ADR-0004`, see
  `WORKING-AGREEMENT.md`).
- Market changed to **international, USD** (the prior iteration targeted Indonesia/IDR).
- Stack updated to **Django 6** with an explicit async + built-in Tasks policy (see
  `PLAN.md` §5).
- Free-tier deploy targets fixed: Render (backend), Vercel (frontend), Supabase (Postgres),
  Upstash (Phase 2).

**Impact.** `PLAN.md` baselined at v0.1.0. Stage 0 (foundation) and Stage 1 (business
strategy) documentation produced. No application code written yet.
