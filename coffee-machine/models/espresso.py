from .beverage import Beverage


class Espresso(Beverage):
    def get_cost(self) -> float:
        return 2.00

    def get_description(self) -> str:
        return "Espresso"

    def get_recipe(self) -> dict[str, int]:
        return {"coffee_beans": 1, "water": 1}
