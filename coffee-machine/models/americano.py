from .beverage import Beverage


class Americano(Beverage):
    def get_cost(self) -> float:
        return 2.50

    def get_description(self) -> str:
        return "Americano"

    def get_recipe(self) -> dict[str, int]:
        return {"coffee_beans": 1, "water": 2}
