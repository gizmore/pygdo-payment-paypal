from gdo.base.Method import Method
from gdo.core.GDT_String import GDT_String
from gdo.payment.GDO_Order import GDO_Order


class cancel(Method):

    def gdo_needs_authentication(self):
        return True

    def gdo_parameters(self):
        return [GDT_String('order').maxlen(64).not_null()]

    def gdo_execute(self):
        try:
            GDO_Order.for_user(self.param_val('order'), self._env_user)
            return self.msg('msg_payment_cancelled')
        except ValueError:
            return self.err('err_payment_order')
