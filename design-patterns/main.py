"""
Design Patterns Demo - Singleton, Prototype, Object Pool & Factory

Run: python main.py
"""
import time

from singleton.metaclass_singleton import DatabaseConnection, SingletonMeta
from singleton.logger_singleton import Logger, LogLevel
from singleton.config_singleton import AppConfig
from prototype.document_prototype import ReportDocument
from prototype.user_prototype import (
    AdminUser,
    RegularUser,
    UserPrototypeRegistry,
    Permission,
)
from object_pool.connection_pool import ConnectionPool
from object_pool.worker_pool import WorkerPool
from factory.parking_spot_factory import ParkingSpotFactory, SpotType
from factory.notification_factory import (
    NotificationChannelFactory,
    ChannelType,
    EmailCreator,
)


def separator(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def demo_singleton_database() -> None:
    separator("SINGLETON: Database Connection (Metaclass)")

    db1 = DatabaseConnection("localhost", 5432, "parking_db")
    db2 = DatabaseConnection("remote-server", 9999, "other_db")

    print(f"db1: {db1}")
    print(f"db2: {db2}")
    print(f"Same instance? {db1 is db2}")

    db1.execute("SELECT * FROM parking_spots")
    db2.execute("INSERT INTO tickets VALUES (1)")

    print(f"Query count (via db1): {db1.query_count}")
    print(f"Query count (via db2): {db2.query_count}")
    print("Both share the same query count - proves single instance!")


def demo_singleton_logger() -> None:
    separator("SINGLETON: Logger")

    logger1 = Logger(LogLevel.DEBUG)
    logger2 = Logger(LogLevel.WARNING)

    print(f"logger1 is logger2: {logger1 is logger2}")
    print(f"logger2 min_level: {logger2.min_level.value} (logger1 set it to DEBUG)")

    logger1.info("User logged in")
    logger2.warning("Cache miss for key 'user_42'")
    logger1.error("Connection timeout")

    print(f"Total logs: {logger1.log_count}")
    print(f"Stored logs: {logger1.get_logs()}")


def demo_singleton_config() -> None:
    separator("SINGLETON: App Config")

    config1 = AppConfig()
    config1.set("max_retries", 5)

    config2 = AppConfig()
    print(f"config1 is config2: {config1 is config2}")
    print(f"config2 sees max_retries=5: {config2.get('max_retries')}")
    print(f"Full config: {config2.get_all()}")


def demo_prototype_document() -> None:
    separator("PROTOTYPE: Document Cloning")

    template = ReportDocument("Annual Report 2025", "Default Author")
    print(f"Template: {template}")

    clone1 = template.clone()
    clone1.set_title("Q1 Report 2025")
    clone1.set_metadata("quarter", "Q1")

    clone2 = template.clone()
    clone2.set_title("Q2 Report 2025")
    clone2.add_section("Appendix A")

    print(f"\nOriginal: {template}")
    print(f"Clone 1:  {clone1}")
    print(f"Clone 2:  {clone2}")

    print("\nIndependence check:")
    print(f"  Template sections: {template.sections}")
    print(f"  Clone 2 sections:  {clone2.sections}  (has extra Appendix)")
    print("  Modifying clone didn't affect original!")


def demo_prototype_user_registry() -> None:
    separator("PROTOTYPE: User Permission Registry")

    registry = UserPrototypeRegistry()
    registry.register("admin", AdminUser())
    registry.register("regular", RegularUser())

    print(f"Registered prototypes: {registry.list_prototypes()}")

    new_admin = registry.create("admin")
    new_admin.update_setting("session_timeout", 7200)
    new_admin.remove_permission(Permission.DELETE)

    new_user = registry.create("regular")
    new_user.add_permission(Permission.WRITE)

    print(f"\nNew admin:  {new_admin}")
    print(f"New user:   {new_user}")

    original_admin = registry.create("admin")
    print(f"\nOriginal admin (still full perms): {original_admin}")
    print("Cloned admin had DELETE removed, but original is unchanged!")


def demo_object_pool_connection() -> None:
    separator("OBJECT POOL: Connection Pool")

    pool = ConnectionPool(max_size=5, min_size=2)
    print(f"Pool after init: {pool}")

    c1 = pool.borrow()
    c2 = pool.borrow()
    print(f"After borrowing 2: {pool}")

    c1.execute("SELECT * FROM parking_spots")
    c2.execute("INSERT INTO tickets VALUES (1)")

    pool.release(c1)
    pool.release(c2)
    print(f"After releasing 2: {pool}")
    print("Connections were reused, not recreated!")


def demo_object_pool_worker() -> None:
    separator("OBJECT POOL: Worker Pool")

    pool = WorkerPool(pool_size=3)
    pool.start()
    print(f"Pool started: {pool}")

    for i in range(6):
        pool.submit(f"job-{i}", lambda idx=i: time.sleep(0.01))

    pool.shutdown(wait=True)
    print(f"Pool after shutdown: {pool}")

    for w in pool.get_workers():
        print(f"  {w}")


def demo_factory_parking_spot() -> None:
    separator("FACTORY: Parking Spot (Simple Factory)")

    for spot_type in SpotType:
        spot = ParkingSpotFactory.create_spot(spot_type, f"{spot_type.value[0].upper()}1")
        print(f"Created: {spot} | Rate: ${spot.get_hourly_rate()}/hr | Size: {spot.get_size()}")

    spot = ParkingSpotFactory.create_spot(SpotType.CAR, "A1")
    spot.park("vehicle_XYZ")
    print(f"\nParked vehicle in: {spot}")


def demo_factory_notification() -> None:
    separator("FACTORY: Notification Channel (Factory Method)")

    for channel_type in ChannelType:
        channel = NotificationChannelFactory.create(channel_type)
        result = channel.send("user@example.com", "Your order shipped!")
        print(f"  {result}")

    print("\nFactory Method subclass:")
    creator = EmailCreator(smtp_host="mail.company.com")
    result = creator.send_notification("admin@company.com", "Server alert!")
    print(f"  {result}")


if __name__ == "__main__":
    print("=" * 60)
    print("  DESIGN PATTERNS: Singleton, Prototype, Object Pool & Factory")
    print("  LLD Implementation Demo")
    print("=" * 60)

    demo_singleton_database()
    demo_singleton_logger()
    demo_singleton_config()
    demo_prototype_document()
    demo_prototype_user_registry()
    demo_object_pool_connection()
    demo_object_pool_worker()
    demo_factory_parking_spot()
    demo_factory_notification()

    print(f"\n{'=' * 60}")
    print("  All demos completed!")
    print(f"{'=' * 60}")
