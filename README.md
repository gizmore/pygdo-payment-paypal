# pygdo-payment-paypal

Paypal Payment Processor for PyGDO8.

Implements PHPGDO's processor role using PayPal REST Orders v2: create an
order, redirect to PayPal approval, capture server-side, then fulfil the local
order. This does not use the legacy NVP credentials from PHPGDO.

Configuration:

- `paypal_enabled`: off by default.
- `paypal_environment`: `sandbox` (default) or `live`.
- Both REST credential pairs live only in the ignored `secret.toml`; they are
  never stored in the module configuration or database.

```sh
cd gdo/payment_paypal
cp secret.example.toml secret.toml
chmod 600 secret.toml
```

Enter the sandbox client ID/secret under `[paypal.sandbox]` and the real pair
under `[paypal.live]`. Only the pair selected by `paypal_environment` is used.

Enable the processor after entering matching sandbox credentials. Start at
`payment_credits.order_credits.html`, choose PayPal, and approve using a sandbox
buyer account. The public application URL must be configured correctly for the
return and cancel links. Switch credentials as well as `paypal_sandbox` for live
payments; do not use a real payment to test configuration. Switching to `live`
requires an explicit config change as well as a complete `[paypal.live]` pair.

Remote order ID, custom local token, EUR currency, exact amount, completed order
and capture are verified through the authenticated API. Stable PayPal request IDs
make retries idempotent; the local transaction prevents duplicate credits. A
network failure can be retried from the same checkout URL. The return route is
`payment_paypal.capture`, cancellation is `payment_paypal.cancel`.

There is no webhook/reconciliation worker yet: if the browser never returns,
resume the existing checkout to capture/reconcile it. Refunds and chargebacks
are not handled automatically. No live payment has been made during development.

API references: https://developer.paypal.com/api/rest/integration/orders-api
and https://developer.paypal.com/api/rest/reference/idempotency/

```sh
.venv/bin/python -m unittest gdo.payment_paypal.test.test_checkout -v
```
