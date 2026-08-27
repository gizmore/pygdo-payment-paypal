import os
import unittest

from gdo.base.Application import Application
from gdo.base.ModuleLoader import ModuleLoader
from gdo.payment_paypal.module_payment_paypal import module_payment_paypal
from gdotest.TestUtil import cli_plug, reinstall_module, cli_gizmore, GDOTestCase, WebPlug, install_module, web_plug


class module_payment_paypal_Test(GDOTestCase):

    async def asyncSetUp(self):
        await super().asyncSetUp()
        Application.init(os.path.dirname(__file__ + "/../../../../"))
        loader = ModuleLoader.instance()
        install_module('payment_paypal')
        loader.load_modules_db(True)
        WebPlug.COOKIES = {}
        Application.init_cli()
        loader.init_modules(True, True)
        loader.init_cli()

    def test_00_reinstall(self):
        reinstall_module('payment_paypal')
        self.assertIs(type(module_payment_paypal.instance()), module_payment_paypal, "Cannot re-install module payment_paypal.")

    def test_03_overview_cli(self):
        giz =  cli_gizmore()
        out = cli_plug(giz, "$payment_paypal.overview")
        self.assertIsNotNone(out, '$payment_paypal.overview does not work.')

    def test_02_overview_web(self):
        giz =  cli_gizmore()
        out = web_plug("payment_paypal.overview.html")
        self.assertIsNotNone(out, 'payment_paypal.overview.html does not work.')


if __name__ == '__main__':
    unittest.main()
