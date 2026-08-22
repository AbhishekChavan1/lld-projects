from .beverage_decorator import BeverageDecorator


class CaramelSyrupDecorator(BeverageDecorator):
    def get_cost(self) -> float:
        return self._wrapped.get_cost() + 0.60

    def get_description(self) -> str:
        return f"{self._wrapped.get_description()}, Caramel Syrup"

    def get_recipe(self) -> dict[str, int]:
        recipe = self._wrapped.get_recipe()
        recipe["caramel_syrup"] = recipe.get("caramel_syrup", 0) + 1
        return recipe
