# pygdo-payment-paypal

Paypal Payment Processor for PyGDO8.

Implements PHPGDO's processor role using PayPal REST Orders v2: create an
order, redirect to PayPal approval, capture server-side, then fulfil the local
order. This does not use the legacy NVP credentials from PHPGDO.

Configuration:

- `paypal_enabled`: off by default.
- `paypal_sandbox`: on by default; keep enabled for testing.
- `paypal_client_id` and `paypal_client_secret`: REST app credentials for the
  selected environment. The secret uses `GDT_Secret`.

Enable the processor after entering matching sandbox credentials. Start at
`payment_credits.order_credits.html`, choose PayPal, and approve using a sandbox
buyer account. The public application URL must be configured correctly for the
return and cancel links. Switch credentials as well as `paypal_sandbox` for live
payments; do not use a real payment to test configuration.

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
