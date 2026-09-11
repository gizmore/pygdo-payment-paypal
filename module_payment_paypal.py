import asyncio
from urllib.parse import urlparse

from gdo.base.util.href import url
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_Secret import GDT_Secret
from gdo.core.GDT_String import GDT_String
from gdo.net.GDT_Redirect import GDT_Redirect
from gdo.payment.PaymentModule import PaymentModule
from gdo.payment_paypal.PayPalClient import PayPalClient, PayPalError


class module_payment_paypal(PaymentModule):

    def gdo_dependencies(self):
        return ['payment']

    def gdo_module_config(self):
        return [
            GDT_Bool('paypal_enabled').not_null().initial('0'),
            GDT_Bool('paypal_sandbox').not_null().initial('1'),
            GDT_String('paypal_client_id').ascii().maxlen(255).initial(''),
            GDT_Secret('paypal_client_secret').ascii().maxlen(255).initial(''),
        ]

    def is_configured(self):
        return bool(self.get_config_value('paypal_enabled') and self.get_config_val('paypal_client_id')
                    and self.get_config_val('paypal_client_secret'))

    def client(self):
        if not self.is_configured():
            raise PayPalError('PayPal is not configured')
        return PayPalClient(self.get_config_val('paypal_client_id'), self.get_config_val('paypal_client_secret'),
                            self.get_config_value('paypal_sandbox'))

    async def start_payment(self, order):
        token = order.gdo_val('order_token')
        client = self.client()
        remote_id = order.gdo_val('order_remote_id')
        if remote_id:
            data = await asyncio.to_thread(client.get_order, remote_id)
        else:
            data = await asyncio.to_thread(client.create_order, token, order.gdo_val('order_price'),
                                           url('payment_paypal', 'capture', '&order=' + token),
                                           url('payment_paypal', 'cancel', '&order=' + token))
            remote_id = data['id']
            order.save_vals({'order_processor': self.get_name, 'order_remote_id': remote_id})
        if data.get('status') in ('COMPLETED', 'APPROVED'):
            return GDT_Redirect().href(url('payment_paypal', 'capture', '&order=' + token))
        for link in data.get('links', []):
            if link.get('rel') in ('approve', 'payer-action'):
                target = urlparse(link['href'])
                host = 'www.sandbox.paypal.com' if client._sandbox else 'www.paypal.com'
                if target.scheme == 'https' and target.hostname == host and not target.username:
                    return GDT_Redirect().href(link['href'])
        raise PayPalError('PayPal did not provide an approval link')
