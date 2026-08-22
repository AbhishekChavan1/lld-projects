from .beverage_decorator import BeverageDecorator


class MilkDecorator(BeverageDecorator):
    def get_cost(self) -> float:
        return self._wrapped.get_cost() + 0.50

    def get_description(self) -> str:
        return f"{self._wrapped.get_description()}, Milk"

    def get_recipe(self) -> dict[str, int]:
        recipe = self._wrapped.get_recipe()
        recipe["milk"] = recipe.get("milk", 0) + 1
        return recipe
