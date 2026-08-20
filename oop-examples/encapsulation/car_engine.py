from enum import Enum


class EngineState(Enum):
    OFF = 0
    IDLE = 2
    RUNNING = 3
    OVERHEATED = 4


class Engine:
    def __init__(self):
        self.__state = EngineState.OFF

    def start(self):
        if self.__state == EngineState.OFF:
            self.__state = EngineState.IDLE
        elif self.__state == EngineState.OVERHEATED:
            print("Cannot start the engine. It is overheated.")
        elif self.__state == EngineState.IDLE:
            print("Engine is already on.")
        else:
            print("Engine is already running.")

    def stop(self):
        if self.__state in (EngineState.RUNNING, EngineState.IDLE):
            self.__state = EngineState.OFF
        elif self.__state == EngineState.OVERHEATED:
            print("Cannot stop the engine. It is overheated.")
        else:
            print("Engine is already off.")

    def accelerate(self, speed):
        if self.__state == EngineState.IDLE:
            self.__state = EngineState.RUNNING
        elif self.__state == EngineState.RUNNING:
            print("Engine is already running at speed:", speed)
        elif self.__state == EngineState.OVERHEATED:
            print("Cannot accelerate. The engine is overheated.")
        else:
            print("Cannot accelerate. The engine is off.")

    def get_state(self):
        return self.__state


class Wheel:
    def __init__(self, pressure):
        self.__pressure = pressure

    def get_pressure(self):
        return self.__pressure

    def set_pressure(self, pressure):
        if pressure < 0:
            print("Pressure cannot be negative.")
        else:
            self.__pressure = pressure


class Car:
    def __init__(self, engine):
        self.__engine = engine
        self.__wheels = [Wheel(32) for _ in range(4)]

    def start_engine(self):
        self.__engine.start()

    def accelerate(self, speed):
        self.__engine.accelerate(speed)

    def stop_engine(self):
        self.__engine.stop()

    def get_engine_state(self):
        return self.__engine.get_state()

    def check_wheel_pressure(self):
        return [wheel.get_pressure() for wheel in self.__wheels]


def main():
    engine = Engine()
    car = Car(engine)

    car.start_engine()
    print("Engine state after starting:", car.get_engine_state())

    car.accelerate(60)
    print("Engine state after accelerating:", car.get_engine_state())

    car.stop_engine()
    print("Engine state after stopping:", car.get_engine_state())

    pressures = car.check_wheel_pressure()
    print("Wheel pressures:", pressures)


if __name__ == "__main__":
    main()
