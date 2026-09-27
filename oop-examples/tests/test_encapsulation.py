import pytest

from encapsulation.car_engine import Car, Engine, EngineState, Wheel


@pytest.fixture
def engine():
    return Engine()


class TestNameMangling:
    def test_engine_state_is_mangled(self, engine):
        assert not hasattr(engine, "__state")
        assert hasattr(engine, "_Engine__state")

    def test_wheel_pressure_is_mangled(self):
        wheel = Wheel(32)
        assert not hasattr(wheel, "__pressure")
        assert hasattr(wheel, "_Wheel__pressure")

    def test_car_engine_is_mangled(self):
        car = Car(Engine())
        assert not hasattr(car, "__engine")
        assert hasattr(car, "_Car__engine")

    def test_car_wheels_are_mangled(self):
        car = Car(Engine())
        assert not hasattr(car, "__wheels")
        assert len(car._Car__wheels) == 4

    def test_mangled_attribute_is_still_reachable_by_convention(self, engine):
        engine.start()
        assert engine._Engine__state is EngineState.IDLE

    def test_overheated_state_is_unreachable_through_the_public_api(self, engine):
        """Encapsulation pays off: no public method can force an illegal state."""
        for _ in range(10):
            engine.start()
            engine.accelerate(60)
            engine.stop()
        assert engine.get_state() is EngineState.OFF
        assert engine._Engine__state is not EngineState.OVERHEATED


class TestEngineStart:
    def test_off_to_idle(self, engine):
        engine.start()
        assert engine.get_state() is EngineState.IDLE

    def test_starting_twice_is_reported(self, engine, capsys):
        engine.start()
        engine.start()
        assert engine.get_state() is EngineState.IDLE
        assert "Engine is already on." in capsys.readouterr().out

    def test_starting_while_running_is_reported(self, engine, capsys):
        engine.start()
        engine.accelerate(60)
        capsys.readouterr()
        engine.start()
        assert "Engine is already running." in capsys.readouterr().out


class TestEngineAccelerate:
    def test_idle_to_running(self, engine):
        engine.start()
        engine.accelerate(60)
        assert engine.get_state() is EngineState.RUNNING

    def test_accelerating_twice_is_reported(self, engine, capsys):
        engine.start()
        engine.accelerate(60)
        capsys.readouterr()
        engine.accelerate(80)
        assert "Engine is already running at speed: 80" in capsys.readouterr().out

    def test_accelerating_when_off_is_refused(self, engine, capsys):
        engine.accelerate(60)
        assert engine.get_state() is EngineState.OFF
        assert "Cannot accelerate. The engine is off." in capsys.readouterr().out

    def test_accelerating_does_not_change_off_state(self, engine):
        engine.accelerate(60)
        engine.accelerate(120)
        assert engine.get_state() is EngineState.OFF


class TestEngineStop:
    def test_running_to_off(self, engine):
        engine.start()
        engine.accelerate(60)
        engine.stop()
        assert engine.get_state() is EngineState.OFF

    def test_idle_to_off(self, engine):
        engine.start()
        engine.stop()
        assert engine.get_state() is EngineState.OFF

    def test_stopping_twice_is_reported(self, engine, capsys):
        engine.stop()
        assert "Engine is already off." in capsys.readouterr().out

    def test_stop_then_accelerate_is_still_refused(self, engine, capsys):
        engine.start()
        engine.stop()
        capsys.readouterr()
        engine.accelerate(60)
        assert "Cannot accelerate. The engine is off." in capsys.readouterr().out


class TestEngineStateEnum:
    def test_states_are_distinct(self):
        values = [s.value for s in EngineState]
        assert len(set(values)) == len(values) == 4

    def test_initial_state_is_off(self, engine):
        assert engine.get_state() is EngineState.OFF


class TestWheel:
    def test_initial_pressure(self):
        assert Wheel(32).get_pressure() == 32

    def test_pressure_can_be_changed(self):
        wheel = Wheel(32)
        wheel.set_pressure(30)
        assert wheel.get_pressure() == 30

    def test_zero_pressure_is_allowed(self):
        wheel = Wheel(32)
        wheel.set_pressure(0)
        assert wheel.get_pressure() == 0

    def test_negative_pressure_is_refused(self, capsys):
        wheel = Wheel(32)
        wheel.set_pressure(-1)
        assert wheel.get_pressure() == 32
        assert "Pressure cannot be negative." in capsys.readouterr().out

    def test_refused_pressure_does_not_corrupt_state(self, capsys):
        wheel = Wheel(32)
        wheel.set_pressure(28)
        wheel.set_pressure(-5)
        assert wheel.get_pressure() == 28
        capsys.readouterr()


class TestCar:
    def test_has_four_wheels_at_32_psi(self):
        car = Car(Engine())
        assert car.check_wheel_pressure() == [32, 32, 32, 32]

    def test_wheels_are_independent_objects(self):
        car = Car(Engine())
        car._Car__wheels[0].set_pressure(20)
        assert car.check_wheel_pressure() == [20, 32, 32, 32]

    def test_start_delegates_to_engine(self):
        engine = Engine()
        car = Car(engine)
        car.start_engine()
        assert car.get_engine_state() is EngineState.IDLE
        assert engine.get_state() is EngineState.IDLE

    def test_accelerate_delegates_to_engine(self):
        engine = Engine()
        car = Car(engine)
        car.start_engine()
        car.accelerate(60)
        assert car.get_engine_state() is EngineState.RUNNING

    def test_stop_delegates_to_engine(self):
        engine = Engine()
        car = Car(engine)
        car.start_engine()
        car.stop_engine()
        assert car.get_engine_state() is EngineState.OFF

    def test_car_does_not_expose_engine_internals(self):
        car = Car(Engine())
        assert not hasattr(car, "engine")
        assert not hasattr(car, "wheels")

    def test_full_drive_cycle(self):
        car = Car(Engine())
        car.start_engine()
        car.accelerate(60)
        car.stop_engine()
        assert car.get_engine_state() is EngineState.OFF
        assert car.check_wheel_pressure() == [32, 32, 32, 32]
