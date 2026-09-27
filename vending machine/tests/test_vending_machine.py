import threading

import pytest

from models.coin import Coin
from models.product import Product
from services.vending_machine import VendingMachine
from states.dispensing_state import DispensingState
from states.has_money_state import HasMoneyState
from states.idle_state import IdleState
from states.out_of_stock_state import OutOfStockState
from states.state import State


@pytest.fixture
def machine():
    vm = VendingMachine()
    vm.add_product(Product("Coke", 1.25, 2))
    vm.add_product(Product("Chips", 0.75, 1))
    return vm


class TestCoin:
    def test_denominations(self):
        assert Coin.NICKEL.value == 0.05
        assert Coin.DIME.value == 0.10
        assert Coin.QUARTER.value == 0.25
        assert Coin.DOLLAR.value == 1.00

    def test_coin_is_value_object(self):
        assert Coin.QUARTER is Coin.QUARTER
        assert Coin.QUARTER != Coin.DIME


class TestProduct:
    def test_initial_quantity(self):
        assert Product("Coke", 1.25, 3).get_quantity() == 3

    def test_decrement_reduces_quantity(self):
        p = Product("Coke", 1.25, 2)
        p.decrement()
        assert p.get_quantity() == 1

    def test_decrement_can_go_negative(self):
        p = Product("Coke", 1.25, 0)
        p.decrement()
        assert p.get_quantity() == -1

    def test_restock_adds_quantity(self):
        p = Product("Coke", 1.25, 1)
        p.restock(5)
        assert p.get_quantity() == 6

    def test_quantity_is_thread_safe(self):
        p = Product("Coke", 1.25, 0)
        threads = [
            threading.Thread(target=lambda: [p.decrement() for _ in range(500)])
            for _ in range(8)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert p.get_quantity() == -4000


class TestStateContract:
    def test_all_states_implement_abstract_interface(self):
        for state in (
            IdleState(),
            HasMoneyState(),
            DispensingState(),
            OutOfStockState(),
        ):
            assert isinstance(state, State)

    def test_state_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            State()

    def test_states_are_reused_across_transitions(self, machine):
        idle = machine.get_idle_state()
        machine.insert_coin(Coin.QUARTER)
        machine.cancel()
        assert machine.get_idle_state() is idle


class TestMachineBasics:
    def test_starts_idle_with_zero_balance(self, machine):
        assert machine.get_balance() == 0.0
        assert machine.get_selected_product() is None
        assert machine.get_idle_state() is not None

    def test_add_and_get_product(self, machine):
        assert machine.get_product("Coke").price == 1.25
        assert machine.get_product("Missing") is None

    def test_get_all_products(self, machine):
        assert len(machine.get_all_products()) == 2

    def test_add_balance_and_clear(self, machine):
        machine.add_balance(0.25)
        machine.add_balance(0.10)
        assert machine.get_balance() == pytest.approx(0.35)
        machine.clear_balance()
        assert machine.get_balance() == 0.0

    def test_round2_absorbs_float_error(self, machine):
        assert machine.round2(0.1 + 0.2) == 0.3

    def test_balance_survives_repeated_penny_math(self, machine):
        for _ in range(10):
            machine.add_balance(0.10)
        assert machine.get_balance() == pytest.approx(1.00)


class TestIdleState:
    def test_insert_coin_moves_to_has_money(self, machine, capsys):
        machine.insert_coin(Coin.QUARTER)
        capsys.readouterr()
        machine.set_state(machine.get_idle_state())
        machine.insert_coin(Coin.DIME)
        assert machine.get_balance() == pytest.approx(0.35)
        assert "Inserted coin" in capsys.readouterr().out

    def test_select_product_is_rejected(self, machine, capsys):
        machine.select_product("Coke")
        assert machine.get_selected_product() is None
        assert "Insert coins first" in capsys.readouterr().out

    def test_dispense_is_rejected(self, machine, capsys):
        machine.dispense()
        assert "No coins loaded" in capsys.readouterr().out

    def test_cancel_is_rejected(self, machine, capsys):
        machine.cancel()
        assert machine.get_balance() == 0.0
        assert "No transactional balance" in capsys.readouterr().out


class TestHasMoneyState:
    def test_insert_coin_accumulates(self, machine, capsys):
        machine.insert_coin(Coin.QUARTER)
        machine.insert_coin(Coin.QUARTER)
        assert machine.get_balance() == pytest.approx(0.50)
        assert "Inserted another coin" in capsys.readouterr().out

    def test_unknown_product_is_reported(self, machine, capsys):
        machine.insert_coin(Coin.DOLLAR)
        capsys.readouterr()
        machine.select_product("Sushi")
        assert machine.get_selected_product() is None
        assert "out of stock" in capsys.readouterr().out

    def test_empty_product_is_reported(self, machine, capsys):
        machine.insert_coin(Coin.DOLLAR)
        machine.get_product("Chips").decrement()
        capsys.readouterr()
        machine.select_product("Chips")
        assert machine.get_selected_product() is None
        assert "out of stock" in capsys.readouterr().out

    def test_insufficient_funds_keeps_balance(self, machine, capsys):
        machine.insert_coin(Coin.QUARTER)
        capsys.readouterr()
        machine.select_product("Coke")
        assert machine.get_selected_product() is None
        assert machine.get_balance() == pytest.approx(0.25)
        assert "Insufficient funds" in capsys.readouterr().out

    def test_dispense_without_selection_is_rejected(self, machine, capsys):
        machine.insert_coin(Coin.QUARTER)
        machine.set_state(machine.get_has_money_state())
        machine.dispense()
        assert "Select a product" in capsys.readouterr().out


class TestSuccessfulPurchase:
    def test_exact_payment_dispenses_and_returns_to_idle(self, machine, capsys):
        machine.insert_coin(Coin.DOLLAR)
        machine.insert_coin(Coin.QUARTER)
        capsys.readouterr()
        machine.select_product("Coke")

        out = capsys.readouterr().out
        assert machine.get_product("Coke").get_quantity() == 1
        assert machine.get_balance() == 0.0
        assert machine.get_selected_product() is None
        assert "Dispensing product Coke" in out
        assert machine._current_state is machine.get_idle_state()

    def test_overpayment_returns_change(self, machine, capsys):
        machine.insert_coin(Coin.DOLLAR)
        machine.insert_coin(Coin.DOLLAR)
        capsys.readouterr()
        machine.select_product("Chips")

        out = capsys.readouterr().out
        assert machine.get_product("Chips").get_quantity() == 0
        assert "Change due: $1.25" in out
        assert "Returned change coin: DOLLAR x1" in out
        assert "Returned change coin: QUARTER x1" in out
        assert machine.get_balance() == 0.0

    def test_multi_coin_purchase(self, machine):
        machine.insert_coin(Coin.QUARTER)
        machine.insert_coin(Coin.QUARTER)
        machine.insert_coin(Coin.QUARTER)
        machine.select_product("Chips")
        assert machine.get_product("Chips").get_quantity() == 0

    def test_change_debits_coin_inventory(self, machine):
        machine.insert_coin(Coin.DOLLAR)
        machine.insert_coin(Coin.DOLLAR)
        machine.select_product("Chips")
        assert machine._coin_inventory[Coin.DOLLAR] == 4
        assert machine._coin_inventory[Coin.QUARTER] == 9


class TestCancel:
    def test_cancel_refunds_and_resets(self, machine, capsys):
        machine.insert_coin(Coin.DOLLAR)
        capsys.readouterr()
        machine.cancel()

        out = capsys.readouterr().out
        assert machine.get_balance() == 0.0
        assert machine._coin_inventory[Coin.DOLLAR] == 4
        assert "Transaction cancelled" in out
        assert machine._current_state is machine.get_idle_state()

    def test_cancel_keeps_inventory_untouched(self, machine):
        machine.insert_coin(Coin.DOLLAR)
        machine.insert_coin(Coin.QUARTER)
        machine.select_product("Coke")
        assert machine.get_product("Coke").get_quantity() == 1


class TestOutOfStockState:
    def test_machine_enters_out_of_stock_when_drained(self, machine):
        machine.insert_coin(Coin.DOLLAR)
        machine.insert_coin(Coin.QUARTER)
        machine.select_product("Coke")
        machine.insert_coin(Coin.DOLLAR)
        machine.insert_coin(Coin.QUARTER)
        machine.select_product("Coke")
        machine.insert_coin(Coin.QUARTER)
        machine.insert_coin(Coin.QUARTER)
        machine.insert_coin(Coin.QUARTER)
        machine.select_product("Chips")

        assert machine._current_state is machine.get_out_of_stock_state()

    def test_out_of_stock_rejects_every_action(self, machine, capsys):
        machine.set_state(machine.get_out_of_stock_state())
        machine.insert_coin(Coin.DOLLAR)
        machine.select_product("Coke")
        machine.dispense()
        machine.cancel()

        out = capsys.readouterr().out
        assert out.count("Machine is completely Out of Stock.") == 2
        assert "Nothing to dispense." in out
        assert "Nothing to cancel." in out
        assert machine.get_balance() == 0.0

    def test_dispensing_rejects_every_action(self, machine, capsys):
        machine.set_state(machine.get_dispensing_state())
        machine.insert_coin(Coin.DOLLAR)
        machine.select_product("Coke")
        machine.cancel()

        out = capsys.readouterr().out
        assert out.count("Currently dispensing, please wait.") == 2
        assert "Cannot cancel while dispensing" in out


class TestChangeAlgorithm:
    def test_zero_change_is_trivially_returned(self, machine):
        assert machine.return_change(0.0) is True

    def test_greedy_breakdown_prefers_larger_coins(self, machine, capsys):
        assert machine.return_change(1.05) is True
        out = capsys.readouterr().out
        assert "DOLLAR x1" in out
        assert "NICKEL x1" in out

    def test_change_is_never_over_returned(self, machine):
        assert machine.return_change(0.05) is True
        assert machine._coin_inventory[Coin.NICKEL] == 19
        assert machine._coin_inventory[Coin.DIME] == 10

    def test_limited_inventory_caps_taken_coins(self, machine, capsys):
        machine.add_coins(Coin.DOLLAR, -4)
        assert machine.return_change(2.00) is True
        assert "DOLLAR x1" in capsys.readouterr().out

    def test_unreachable_amount_fails_cleanly(self, machine, capsys):
        for coin in Coin:
            machine._coin_inventory[coin] = 0
        assert machine.return_change(0.05) is False
        assert "Insufficient physical coins" in capsys.readouterr().out

    def test_failed_change_does_not_debit_inventory(self, machine):
        for coin in Coin:
            machine._coin_inventory[coin] = 0
        before = dict(machine._coin_inventory)
        machine.return_change(0.05)
        assert machine._coin_inventory == before

    def test_add_coins_increases_stock(self, machine):
        machine.add_coins(Coin.NICKEL, 5)
        assert machine._coin_inventory[Coin.NICKEL] == 25


class TestRefundOnFailedChange:
    def test_product_is_restocked_when_change_cannot_be_made(self, machine, capsys):
        machine.add_product(Product("Water", 0.05, 1))
        for coin in Coin:
            machine._coin_inventory[coin] = 0
        machine.insert_coin(Coin.DOLLAR)
        capsys.readouterr()
        machine.select_product("Water")

        out = capsys.readouterr().out
        assert "Refunding complete amount" in out
        assert machine.get_product("Water").get_quantity() == 1
        assert machine.get_balance() == 0.0
        assert machine._current_state is machine.get_idle_state()


class TestThreadSafety:
    def test_concurrent_coin_insertion_keeps_exact_balance(self):
        vm = VendingMachine()
        coins_per_thread = 200
        threads_count = 8

        threads = [
            threading.Thread(
                target=lambda: [
                    vm.insert_coin(Coin.NICKEL) for _ in range(coins_per_thread)
                ]
            )
            for _ in range(threads_count)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        expected = round(coins_per_thread * threads_count * 0.05, 2)
        assert vm.get_balance() == pytest.approx(expected)

    def test_stock_never_goes_negative_under_racing_buyers(self):
        vm = VendingMachine()
        vm.add_product(Product("Coke", 0.25, 20))
        stock = 20

        def buy():
            vm.insert_coin(Coin.QUARTER)
            vm.select_product("Coke")

        threads = [threading.Thread(target=buy) for _ in range(30)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert 0 <= vm.get_product("Coke").get_quantity() <= stock

    def test_stock_drains_exactly_under_sequential_buyers(self):
        vm = VendingMachine()
        vm.add_product(Product("Coke", 0.25, 20))

        for _ in range(20):
            vm.insert_coin(Coin.QUARTER)
            vm.select_product("Coke")

        assert vm.get_product("Coke").get_quantity() == 0
        assert vm._current_state is vm.get_out_of_stock_state()
