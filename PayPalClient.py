import base64
import json
import re
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class PayPalError(ValueError):
    """Safe payment failure; excludes credentials and raw API bodies."""


class PayPalClient:

    def __init__(self, client_id, secret, sandbox=True):
        self._client_id = client_id
        self._secret = secret
        self._sandbox = sandbox
        self._base = 'https://api-m.sandbox.paypal.com' if sandbox else 'https://api-m.paypal.com'
        self._access_token = None

    def _request(self, path, method='GET', data=None, headers=None):
        request = Request(self._base + path, data=data, method=method, headers=headers or {})
        try:
            with urlopen(request, timeout=20) as response:
                return json.loads(response.read(1048576))
        except (HTTPError, URLError, TimeoutError, ValueError):
            raise PayPalError('PayPal request failed; retry the existing order') from None

    def api(self, path, method='GET', payload=None, request_id=None):
        if self._access_token is None:
            basic = base64.b64encode(f'{self._client_id}:{self._secret}'.encode()).decode()
            auth = self._request('/v1/oauth2/token', 'POST', b'grant_type=client_credentials',
                                 {'Authorization': 'Basic ' + basic, 'Content-Type': 'application/x-www-form-urlencoded'})
            self._access_token = auth.get('access_token')
            if not self._access_token:
                raise PayPalError('PayPal authentication failed')
        headers = {'Authorization': 'Bearer ' + self._access_token, 'Content-Type': 'application/json',
                   'Prefer': 'return=representation'}
        if request_id:
            headers['PayPal-Request-Id'] = request_id
        return self._request(path, method, json.dumps(payload).encode() if payload is not None else None, headers)

    @staticmethod
    def order_path(remote_id):
        if not re.fullmatch(r'[A-Z0-9]{1,64}', remote_id or ''):
            raise PayPalError('Invalid PayPal order ID')
        return '/v2/checkout/orders/' + remote_id

    def create_order(self, token, price, return_url, cancel_url):
        return self.api('/v2/checkout/orders', 'POST', {
            'intent': 'CAPTURE',
            'purchase_units': [{'custom_id': token, 'amount': {'currency_code': 'EUR', 'value': format(Decimal(price), '.2f')}}],
            'payment_source': {'paypal': {'experience_context': {
                'return_url': return_url, 'cancel_url': cancel_url,
                'user_action': 'PAY_NOW', 'shipping_preference': 'NO_SHIPPING',
            }}},
        }, token[:30] + '-create')

    def get_order(self, remote_id):
        return self.api(self.order_path(remote_id))

    def capture_order(self, remote_id, token):
        return self.api(self.order_path(remote_id) + '/capture', 'POST', {}, token[:30] + '-capture')

    @staticmethod
    def verify_order(data, remote_id, token, price, completed=False):
        try:
            units = data['purchase_units']
            unit = units[0]
            expected = Decimal(price)
            if (data['id'] != remote_id or data.get('intent') != 'CAPTURE' or len(units) != 1
                    or unit['custom_id'] != token or unit['amount']['currency_code'] != 'EUR'
                    or not expected.is_finite() or expected <= 0
                    or Decimal(unit['amount']['value']) != expected):
                raise PayPalError('Payment does not match the order')
            if completed:
                captures = unit['payments']['captures']
                capture = captures[0]
                if (data['status'] != 'COMPLETED' or len(captures) != 1
                        or capture['status'] != 'COMPLETED' or not capture.get('id')
                        or capture['amount']['currency_code'] != 'EUR'
                        or Decimal(capture['amount']['value']) != expected):
                    raise PayPalError('Payment is not completed')
                return capture['id']
        except (KeyError, IndexError, TypeError, InvalidOperation):
            raise PayPalError('Invalid PayPal confirmation') from None
