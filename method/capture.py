import asyncio

from gdo.base.Method import Method
from gdo.core.GDT_String import GDT_String
from gdo.core.GDO_UserSetting import GDO_UserSetting
from gdo.base.Cache import Cache
from gdo.base.IPC import IPC
from gdo.payment.GDO_Order import GDO_Order
from gdo.payment_paypal.module_payment_paypal import module_payment_paypal


class capture(Method):

    def gdo_transactional(self):
        return False

    def gdo_needs_authentication(self):
        return True

    def gdo_parameters(self):
        return [GDT_String('order').maxlen(64).not_null(), GDT_String('token').maxlen(64),
                GDT_String('PayerID').maxlen(64)]

    async def gdo_execute(self):
        try:
            order = GDO_Order.for_user(self.param_val('order'), self._env_user)
            if order.gdo_val('order_status') == 'paid':
                return self.msg('msg_payment_complete')
            if order.gdo_val('order_processor') != 'payment_paypal':
                return self.err('err_payment_order')
            remote_id = order.gdo_val('order_remote_id')
            if self.param_val('token') and self.param_val('token') != remote_id:
                return self.err('err_payment_order')
            client = module_payment_paypal.instance().client()
            token, price = order.gdo_val('order_token'), order.gdo_val('order_price')
            data = await asyncio.to_thread(client.get_order, remote_id)
            client.verify_order(data, remote_id, token, price)
            if data.get('status') == 'APPROVED':
                await asyncio.to_thread(client.capture_order, remote_id, token)
                data = await asyncio.to_thread(client.get_order, remote_id)
            capture_id = client.verify_order(data, remote_id, token, price, completed=True)
            await order.complete(capture_id)
            settings = GDO_UserSetting.load_for_user(self._env_user)
            Cache.update_for(self._env_user)
            if 'credits' in settings:
                IPC.send('base.ipc_uset', (self._env_user.get_id(), 'credits', settings['credits']))
            return self.msg('msg_payment_complete')
        except ValueError:
            return self.err('err_paypal_confirmation')
