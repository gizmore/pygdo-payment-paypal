import unittest

from gdo.payment_paypal.method.cancel import cancel
from gdo.payment_paypal.method.capture import capture
from gdo.payment_paypal.method.overview import overview


class PayPalHelpVisibilityTest(unittest.TestCase):
    def test_methods_hidden(self):
        for method in (cancel, capture, overview):
            with self.subTest(method=method):
                self.assertTrue(method.gdo_method_hidden(object.__new__(method)))
