from abc import ABC, abstractmethod


class Payable(ABC):
    @abstractmethod
    def calculate_pay(self):
        pass


class Manageable(ABC):
    @abstractmethod
    def add_report(self, employee):
        pass

    @abstractmethod
    def get_reports(self):
        pass


class Reportable(ABC):
    @abstractmethod
    def generate_report(self):
        pass


class TaxService:
    def calculate_tax(self, income):
        return income * 0.20


class PayrollService:
    def __init__(self, tax_service):
        self.__tax_service = tax_service

    def calculate_net_pay(self, gross_pay):
        tax = self.__tax_service.calculate_tax(gross_pay)
        return gross_pay - tax


class ReportingService:
    def generate(self, name, role):
        return f"Report for {name} ({role})"


class Employee(Payable, Reportable):
    def __init__(self, name, salary, payroll_service, reporting_service):
        self.__name = name
        self.__salary = salary
        self.__payroll_service = payroll_service
        self.__reporting_service = reporting_service

    def calculate_pay(self):
        return self.__payroll_service.calculate_net_pay(self.__salary)

    def generate_report(self):
        return self.__reporting_service.generate(self.__name, "Employee")


class Manager(Payable, Manageable, Reportable):
    def __init__(self, name, salary, payroll_service, reporting_service):
        self.__name = name
        self.__salary = salary
        self.__payroll_service = payroll_service
        self.__reporting_service = reporting_service
        self.__reports = []

    def calculate_pay(self):
        return self.__payroll_service.calculate_net_pay(self.__salary)

    def add_report(self, employee):
        self.__reports.append(employee)

    def get_reports(self):
        return list(self.__reports)

    def generate_report(self):
        return self.__reporting_service.generate(self.__name, "Manager")


class Contractor(Payable):
    def __init__(self, name, contract_amount, payroll_service):
        self.__name = name
        self.__contract_amount = contract_amount
        self.__payroll_service = payroll_service

    def calculate_pay(self):
        return self.__payroll_service.calculate_net_pay(self.__contract_amount)


def main():
    tax_service = TaxService()
    payroll_service = PayrollService(tax_service)
    reporting_service = ReportingService()

    employee = Employee("Alice", 60000, payroll_service, reporting_service)
    manager = Manager("Bob", 100000, payroll_service, reporting_service)
    contractor = Contractor("Charlie", 50000, payroll_service)

    manager.add_report(employee)

    print(f"Employee pay: ${employee.calculate_pay():,.2f}")
    print(f"Manager pay: ${manager.calculate_pay():,.2f}")
    print(f"Contractor pay: ${contractor.calculate_pay():,.2f}")
    print(f"Employee report: {employee.generate_report()}")
    print(f"Manager report: {manager.generate_report()}")
    print(f"Manager reports: {[r for r in manager.get_reports()]}")


if __name__ == "__main__":
    main()
