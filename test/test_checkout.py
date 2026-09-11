import unittest
from unittest.mock import patch

from gdo.payment_paypal.PayPalClient import PayPalClient, PayPalError


class PayPalCheckoutTest(unittest.TestCase):

    def payment(self):
        return {'id': 'ORDER123', 'intent': 'CAPTURE', 'status': 'COMPLETED', 'purchase_units': [{
            'custom_id': 'local-token', 'amount': {'currency_code': 'EUR', 'value': '5.00'},
            'payments': {'captures': [{'id': 'CAPTURE123', 'status': 'COMPLETED',
                                     'amount': {'currency_code': 'EUR', 'value': '5.00'}}]},
        }]}

    def test_completed_payment(self):
        self.assertEqual('CAPTURE123', PayPalClient.verify_order(self.payment(), 'ORDER123', 'local-token', '5.0000', True))

    def test_untrusted_confirmation(self):
        for path, value in [
            (['id'], 'OTHER'), (['status'], 'APPROVED'),
            (['purchase_units', 0, 'custom_id'], 'other-token'),
            (['purchase_units', 0, 'amount', 'value'], '0.01'),
            (['purchase_units', 0, 'amount', 'currency_code'], 'USD'),
            (['purchase_units', 0, 'payments', 'captures', 0, 'status'], 'PENDING'),
            (['purchase_units', 0, 'payments', 'captures', 0, 'amount', 'value'], '4.99'),
        ]:
            with self.subTest(path=path):
                data = self.payment()
                node = data
                for key in path[:-1]:
                    node = node[key]
                node[path[-1]] = value
                with self.assertRaises(PayPalError):
                    PayPalClient.verify_order(data, 'ORDER123', 'local-token', '5.00', True)

    def test_multiple_captures_rejected(self):
        data = self.payment()
        data['purchase_units'][0]['payments']['captures'] *= 2
        with self.assertRaises(PayPalError):
            PayPalClient.verify_order(data, 'ORDER123', 'local-token', '5.00', True)

    def test_retry_uses_same_idempotency_key_and_exact_cents(self):
        client = PayPalClient('test', 'test')
        token = 'a' * 48
        with patch.object(client, 'api', return_value={}) as api:
            for _ in range(2):
                client.create_order(token, '5.0000', 'https://example.com/return', 'https://example.com/cancel')
            self.assertEqual(api.call_args_list[0], api.call_args_list[1])
            self.assertEqual('5.00', api.call_args.args[2]['purchase_units'][0]['amount']['value'])
            self.assertLessEqual(len(api.call_args.args[3]), 38)
            client.capture_order('ORDER123', token)
            self.assertLessEqual(len(api.call_args.args[3]), 38)

    def test_remote_id_cannot_change_api_path(self):
        with self.assertRaises(PayPalError):
            PayPalClient.order_path('../other')


if __name__ == '__main__':
    unittest.main()
