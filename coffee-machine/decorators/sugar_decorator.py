from .beverage_decorator import BeverageDecorator


class SugarDecorator(BeverageDecorator):
    def get_cost(self) -> float:
        return self._wrapped.get_cost() + 0.20

    def get_description(self) -> str:
        return f"{self._wrapped.get_description()}, Sugar"

    def get_recipe(self) -> dict[str, int]:
        recipe = self._wrapped.get_recipe()
        recipe["sugar"] = recipe.get("sugar", 0) + 1
        return recipe
