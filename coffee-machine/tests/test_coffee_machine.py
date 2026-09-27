import threading

import pytest

from decorators.beverage_decorator import BeverageDecorator
from decorators.caramel_syrup_decorator import CaramelSyrupDecorator
from decorators.milk_decorator import MilkDecorator
from decorators.sugar_decorator import SugarDecorator
from machine.coffee_machine import CoffeeMachine
from models.americano import Americano
from models.beverage import Beverage
from models.espresso import Espresso
from services.inventory import Inventory
from states.brewing_state import BrewingState
from states.coffee_machine_state import CoffeeMachineState
from states.idle_state import IdleState
from states.payment_pending_state import PaymentPendingState


@pytest.fixture
def machine():
    return CoffeeMachine()


@pytest.fixture
def stocked_machine():
    return CoffeeMachine(
        Inventory(
            {
                "coffee_beans": 10,
                "water": 20,
                "milk": 5,
                "sugar": 5,
                "caramel_syrup": 3,
            }
        )
    )


def pay_and_brew(machine, beverage, amount):
    machine.select_beverage(beverage)
    machine.insert_coin(amount)
    machine.brew()


class TestBeverageContract:
    def test_beverage_is_abstract(self):
        with pytest.raises(TypeError):
            Beverage()

    def test_decorator_base_is_abstract(self):
        with pytest.raises(TypeError):
            BeverageDecorator(Espresso())

    def test_every_beverage_implements_the_interface(self):
        for beverage in (
            Espresso(),
            Americano(),
            MilkDecorator(Espresso()),
            SugarDecorator(Americano()),
            CaramelSyrupDecorator(Espresso()),
        ):
            assert isinstance(beverage, Beverage)
            assert isinstance(beverage.get_recipe(), dict)

    def test_str_renders_description_and_price(self):
        assert str(Espresso()) == "Espresso ($2.00)"

    def test_custom_beverage_can_be_added_without_touching_machine(self):
        class Matcha(Beverage):
            def get_cost(self) -> float:
                return 3.25

            def get_description(self) -> str:
                return "Matcha Latte"

            def get_recipe(self) -> dict[str, int]:
                return {"matcha": 1, "water": 1, "milk": 1}

        assert str(Matcha()) == "Matcha Latte ($3.25)"


class TestBaseBeverages:
    def test_espresso(self):
        e = Espresso()
        assert e.get_cost() == 2.00
        assert e.get_description() == "Espresso"
        assert e.get_recipe() == {"coffee_beans": 1, "water": 1}

    def test_americano(self):
        a = Americano()
        assert a.get_cost() == 2.50
        assert a.get_description() == "Americano"
        assert a.get_recipe() == {"coffee_beans": 1, "water": 2}

    def test_base_recipes_are_fresh_dicts(self):
        e = Espresso()
        first = e.get_recipe()
        first["coffee_beans"] = 99
        assert e.get_recipe()["coffee_beans"] == 1


class TestDecorators:
    def test_milk_adds_cost_and_ingredient(self):
        m = MilkDecorator(Espresso())
        assert m.get_cost() == 2.50
        assert m.get_description() == "Espresso, Milk"
        assert m.get_recipe() == {"coffee_beans": 1, "water": 1, "milk": 1}

    def test_sugar_adds_cost_and_ingredient(self):
        s = SugarDecorator(Espresso())
        assert s.get_cost() == 2.20
        assert s.get_description() == "Espresso, Sugar"
        assert s.get_recipe() == {"coffee_beans": 1, "water": 1, "sugar": 1}

    def test_caramel_adds_cost_and_ingredient(self):
        c = CaramelSyrupDecorator(Espresso())
        assert c.get_cost() == 2.60
        assert c.get_description() == "Espresso, Caramel Syrup"
        assert c.get_recipe() == {"coffee_beans": 1, "water": 1, "caramel_syrup": 1}

    def test_decorators_stack(self):
        drink = SugarDecorator(MilkDecorator(Espresso()))
        assert drink.get_cost() == pytest.approx(2.70)
        assert drink.get_description() == "Espresso, Milk, Sugar"
        assert drink.get_recipe() == {
            "coffee_beans": 1,
            "water": 1,
            "milk": 1,
            "sugar": 1,
        }

    def test_stacking_is_order_independent_for_cost(self):
        a = SugarDecorator(MilkDecorator(Espresso()))
        b = MilkDecorator(SugarDecorator(Espresso()))
        assert a.get_cost() == b.get_cost()
        assert a.get_recipe() == b.get_recipe()

    def test_stacking_order_changes_description(self):
        a = SugarDecorator(MilkDecorator(Espresso()))
        b = MilkDecorator(SugarDecorator(Espresso()))
        assert a.get_description() != b.get_description()

    def test_same_decorator_twice_accumulates(self):
        drink = MilkDecorator(MilkDecorator(Espresso()))
        assert drink.get_cost() == pytest.approx(3.00)
        assert drink.get_recipe()["milk"] == 2

    def test_recipe_is_not_shared_between_calls(self):
        drink = MilkDecorator(Espresso())
        first = drink.get_recipe()
        first["milk"] = 99
        assert drink.get_recipe()["milk"] == 1

    def test_three_deep_stack(self):
        drink = CaramelSyrupDecorator(
            SugarDecorator(MilkDecorator(Americano()))
        )
        assert drink.get_cost() == pytest.approx(3.80)
        assert drink.get_description() == "Americano, Milk, Sugar, Caramel Syrup"


class TestInventory:
    def test_empty_inventory(self):
        assert Inventory().get_stock() == {}

    def test_has_ingredients_true_when_stock_suffices(self):
        inv = Inventory({"coffee_beans": 2, "water": 2})
        assert inv.has_ingredients({"coffee_beans": 2}) is True

    def test_has_ingredients_false_when_short(self):
        inv = Inventory({"coffee_beans": 1})
        assert inv.has_ingredients({"coffee_beans": 2}) is False

    def test_has_ingredients_false_for_unknown_item(self):
        assert Inventory({"water": 10}).has_ingredients({"matcha": 1}) is False

    def test_consume_decrements(self):
        inv = Inventory({"coffee_beans": 5})
        inv.consume({"coffee_beans": 2})
        assert inv.get_stock()["coffee_beans"] == 3

    def test_consume_is_all_or_nothing_on_failure(self):
        inv = Inventory({"coffee_beans": 1, "water": 10})
        with pytest.raises(ValueError, match="Insufficient coffee_beans"):
            inv.consume({"coffee_beans": 2, "water": 1})
        assert inv.get_stock() == {"coffee_beans": 1, "water": 10}

    def test_restock_adds_new_and_existing(self):
        inv = Inventory({"water": 5})
        inv.restock({"water": 5, "sugar": 2})
        assert inv.get_stock() == {"water": 10, "sugar": 2}

    def test_get_stock_returns_a_copy(self):
        inv = Inventory({"water": 5})
        snapshot = inv.get_stock()
        snapshot["water"] = 999
        assert inv.get_stock()["water"] == 5

    def test_concurrent_consume_never_goes_negative(self):
        inv = Inventory({"coffee_beans": 100})

        def worker():
            for _ in range(50):
                if inv.has_ingredients({"coffee_beans": 1}):
                    inv.consume({"coffee_beans": 1})

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert inv.get_stock()["coffee_beans"] == 0


class TestStateContract:
    def test_state_base_is_abstract(self):
        with pytest.raises(TypeError):
            CoffeeMachineState()

    def test_all_states_implement_interface(self):
        for state in (IdleState(), PaymentPendingState(), BrewingState()):
            assert isinstance(state, CoffeeMachineState)


class TestIdleState:
    def test_starts_idle(self, machine):
        assert isinstance(machine.get_state(), IdleState)
        assert machine.get_inserted_cash() == 0.0
        assert machine.get_selected_beverage() is None

    def test_select_moves_to_payment_pending(self, machine, capsys):
        machine.select_beverage(Espresso())
        assert isinstance(machine.get_state(), PaymentPendingState)
        assert machine.get_selected_beverage() is not None
        assert "Please pay" in capsys.readouterr().out

    def test_coin_before_selection_is_rejected(self, machine, capsys):
        machine.insert_coin(1.00)
        assert machine.get_inserted_cash() == 0.0
        assert "Select a beverage first" in capsys.readouterr().out

    def test_brew_before_selection_is_rejected(self, machine, capsys):
        machine.brew()
        assert "Select a beverage and insert coins first" in capsys.readouterr().out


class TestPaymentPendingState:
    def test_partial_payment_accumulates(self, machine, capsys):
        machine.select_beverage(Espresso())
        capsys.readouterr()
        machine.insert_coin(1.00)
        assert machine.get_inserted_cash() == 1.00
        assert isinstance(machine.get_state(), PaymentPendingState)
        assert "Payment complete" not in capsys.readouterr().out

    def test_full_payment_moves_to_brewing(self, machine, capsys):
        machine.select_beverage(Espresso())
        machine.insert_coin(2.00)
        assert isinstance(machine.get_state(), BrewingState)
        assert "Payment complete" in capsys.readouterr().out

    def test_overpayment_still_moves_to_brewing(self, machine):
        machine.select_beverage(Espresso())
        machine.insert_coin(5.00)
        assert isinstance(machine.get_state(), BrewingState)

    def test_change_selection_is_rejected(self, machine, capsys):
        machine.select_beverage(Espresso())
        capsys.readouterr()
        machine.select_beverage(Americano())
        assert isinstance(machine.get_selected_beverage(), Espresso)
        assert "Payment already pending" in capsys.readouterr().out

    def test_brew_before_full_payment_is_rejected(self, machine, capsys):
        machine.select_beverage(Espresso())
        machine.insert_coin(1.00)
        capsys.readouterr()
        machine.brew()
        assert "Payment incomplete" in capsys.readouterr().out
        assert machine.inventory.get_stock()["coffee_beans"] == 10


class TestBrewingState:
    def test_brew_consumes_ingredients(self, machine, capsys):
        pay_and_brew(machine, Espresso(), 2.00)
        stock = machine.inventory.get_stock()
        assert stock["coffee_beans"] == 9
        assert stock["water"] == 19
        assert "Brewing Espresso" in capsys.readouterr().out

    def test_brew_returns_to_idle_and_clears_context(self, machine):
        pay_and_brew(machine, Espresso(), 2.00)
        assert isinstance(machine.get_state(), IdleState)
        assert machine.get_inserted_cash() == 0.0
        assert machine.get_selected_beverage() is None

    def test_exact_payment_dispenses_no_change(self, machine, capsys):
        pay_and_brew(machine, Espresso(), 2.00)
        assert "Dispensing change" not in capsys.readouterr().out

    def test_overpayment_dispenses_change(self, machine, capsys):
        pay_and_brew(machine, Espresso(), 3.00)
        assert "Dispensing change: $1.00" in capsys.readouterr().out

    def test_decorated_drink_consumes_condiments(self, machine):
        pay_and_brew(machine, SugarDecorator(MilkDecorator(Espresso())), 2.70)
        stock = machine.inventory.get_stock()
        assert stock["coffee_beans"] == 9
        assert stock["milk"] == 4
        assert stock["sugar"] == 4

    def test_coin_during_brewing_is_rejected(self, machine, capsys):
        machine.select_beverage(Espresso())
        machine.insert_coin(2.00)
        capsys.readouterr()
        machine.insert_coin(1.00)
        assert machine.get_inserted_cash() == 2.00
        assert "Cannot insert coins while brewing" in capsys.readouterr().out

    def test_selection_during_brewing_is_rejected(self, machine, capsys):
        machine.select_beverage(Espresso())
        machine.insert_coin(2.00)
        capsys.readouterr()
        machine.select_beverage(Americano())
        assert isinstance(machine.get_selected_beverage(), Espresso)
        assert "Cannot change beverage while brewing" in capsys.readouterr().out


class TestInsufficientIngredients:
    def test_refund_and_reset_when_beans_run_out(self, machine, capsys):
        machine.inventory.restock({"coffee_beans": -10})
        pay_and_brew(machine, Espresso(), 2.50)

        out = capsys.readouterr().out
        assert "Insufficient ingredients" in out
        assert "Refunded: $2.50" in out
        assert machine.get_inserted_cash() == 0.0
        assert machine.get_selected_beverage() is None
        assert isinstance(machine.get_state(), IdleState)

    def test_failed_brew_consumes_nothing(self, machine):
        machine.inventory.restock({"milk": -5})
        before = machine.inventory.get_stock()
        pay_and_brew(machine, MilkDecorator(Espresso()), 2.50)
        assert machine.inventory.get_stock() == before

    def test_missing_condiment_triggers_refund(self, machine, capsys):
        machine.inventory.restock({"caramel_syrup": -3})
        pay_and_brew(machine, CaramelSyrupDecorator(Americano()), 3.10)
        assert "Refunded: $3.10" in capsys.readouterr().out

    def test_restock_allows_recovery(self, machine):
        machine.inventory.restock({"coffee_beans": -10})
        pay_and_brew(machine, Espresso(), 2.00)
        machine.inventory.restock({"coffee_beans": 5})
        pay_and_brew(machine, Espresso(), 2.00)
        assert machine.inventory.get_stock()["coffee_beans"] == 4


class TestThreadSafety:
    def test_concurrent_brews_consume_exactly_one_recipe(self):
        cm = CoffeeMachine(Inventory({"coffee_beans": 10, "water": 100}))
        cm.select_beverage(Espresso())
        cm.insert_coin(2.00)

        threads = [threading.Thread(target=cm.brew) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stock = cm.inventory.get_stock()
        assert stock["coffee_beans"] == 9
        assert stock["water"] == 99
        assert isinstance(cm.get_state(), IdleState)

    def test_concurrent_failed_brews_refund_only_once(self):
        cm = CoffeeMachine(Inventory({"coffee_beans": 0, "water": 100}))
        cm.select_beverage(Espresso())
        cm.insert_coin(2.00)

        threads = [threading.Thread(target=cm.brew) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert cm.get_inserted_cash() == 0.0
        assert cm.inventory.get_stock()["coffee_beans"] == 0

    def test_concurrent_payments_do_not_lose_cash(self):
        class Wholesale(Beverage):
            def get_cost(self) -> float:
                return 100.00

            def get_description(self) -> str:
                return "Wholesale Pail"

            def get_recipe(self) -> dict[str, int]:
                return {"coffee_beans": 99}

        cm = CoffeeMachine(Inventory({"coffee_beans": 1000, "water": 1000}))
        cm.select_beverage(Wholesale())

        def worker():
            cm.insert_coin(0.50)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert cm.get_inserted_cash() == pytest.approx(10.00)
        assert isinstance(cm.get_state(), PaymentPendingState)

