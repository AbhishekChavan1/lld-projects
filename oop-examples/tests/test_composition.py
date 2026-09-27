import pytest

from composition.employee import (
    Contractor,
    Employee,
    Manageable,
    Manager,
    Payable,
    PayrollService,
    ReportingService,
    Reportable,
    TaxService,
)


@pytest.fixture
def payroll():
    return PayrollService(TaxService())


@pytest.fixture
def reporting():
    return ReportingService()


class TestAbcContracts:
    def test_payable_is_abstract(self):
        with pytest.raises(TypeError):
            Payable()

    def test_reportable_is_abstract(self):
        with pytest.raises(TypeError):
            Reportable()

    def test_manageable_is_abstract(self):
        with pytest.raises(TypeError):
            Manageable()

    def test_payable_declares_one_method(self):
        assert set(Payable.__abstractmethods__) == {"calculate_pay"}

    def test_manageable_declares_two_methods(self):
        assert set(Manageable.__abstractmethods__) == {"add_report", "get_reports"}


class TestClassHierarchy:
    def test_employee_is_payable_and_reportable(self, payroll, reporting):
        employee = Employee("Alice", 60000, payroll, reporting)
        assert isinstance(employee, Payable)
        assert isinstance(employee, Reportable)
        assert not isinstance(employee, Manageable)

    def test_manager_is_payable_reportable_and_manageable(self, payroll, reporting):
        manager = Manager("Bob", 100000, payroll, reporting)
        assert isinstance(manager, Payable)
        assert isinstance(manager, Reportable)
        assert isinstance(manager, Manageable)

    def test_contractor_is_only_payable(self, payroll):
        contractor = Contractor("Charlie", 50000, payroll)
        assert isinstance(contractor, Payable)
        assert not isinstance(contractor, Reportable)
        assert not isinstance(contractor, Manageable)

    def test_contractor_cannot_be_managed(self, payroll, reporting):
        contractor = Contractor("Charlie", 50000, payroll)
        with pytest.raises(AttributeError):
            contractor.add_report(contractor)


class TestTaxService:
    def test_tax_is_twenty_percent(self):
        assert TaxService().calculate_tax(1000) == 200.0

    def test_tax_on_zero(self):
        assert TaxService().calculate_tax(0) == 0.0


class TestPayrollService:
    def test_net_pay_is_gross_minus_tax(self, payroll):
        assert payroll.calculate_net_pay(1000) == 800.0

    def test_tax_service_is_injected_not_hardcoded(self):
        class FlatTaxService:
            def calculate_tax(self, income):
                return 0.0

        assert PayrollService(FlatTaxService()).calculate_net_pay(1000) == 1000

    def test_tax_rate_can_be_changed_without_touching_payroll(self):
        class HighTaxService:
            def calculate_tax(self, income):
                return income * 0.50

        assert PayrollService(HighTaxService()).calculate_net_pay(1000) == 500.0

    def test_tax_service_is_mangled(self, payroll):
        assert hasattr(payroll, "_PayrollService__tax_service")
        assert not hasattr(payroll, "tax_service")


class TestEmployee:
    def test_pay_is_salary_after_tax(self, payroll, reporting):
        assert Employee("Alice", 60000, payroll, reporting).calculate_pay() == 48000.0

    def test_report_names_the_role(self, payroll, reporting):
        report = Employee("Alice", 60000, payroll, reporting).generate_report()
        assert report == "Report for Alice (Employee)"

    def test_attributes_are_mangled(self, payroll, reporting):
        employee = Employee("Alice", 60000, payroll, reporting)
        assert employee._Employee__salary == 60000
        assert not hasattr(employee, "__salary")
        assert not hasattr(employee, "salary")

    def test_payroll_service_is_swappable(self, reporting):
        class NoTaxService:
            def calculate_tax(self, income):
                return 0.0

        gross = PayrollService(NoTaxService())
        assert Employee("Alice", 60000, gross, reporting).calculate_pay() == 60000


class TestManager:
    def test_pay_is_salary_after_tax(self, payroll, reporting):
        assert Manager("Bob", 100000, payroll, reporting).calculate_pay() == 80000.0

    def test_report_names_the_manager_role(self, payroll, reporting):
        report = Manager("Bob", 100000, payroll, reporting).generate_report()
        assert report == "Report for Bob (Manager)"

    def test_starts_with_no_reports(self, payroll, reporting):
        assert Manager("Bob", 100000, payroll, reporting).get_reports() == []

    def test_add_report(self, payroll, reporting):
        manager = Manager("Bob", 100000, payroll, reporting)
        employee = Employee("Alice", 60000, payroll, reporting)
        manager.add_report(employee)
        assert manager.get_reports() == [employee]

    def test_reports_accumulate_in_order(self, payroll, reporting):
        manager = Manager("Bob", 100000, payroll, reporting)
        first = Employee("Alice", 60000, payroll, reporting)
        second = Employee("Carol", 70000, payroll, reporting)
        manager.add_report(first)
        manager.add_report(second)
        assert manager.get_reports() == [first, second]

    def test_get_reports_returns_a_copy(self, payroll, reporting):
        manager = Manager("Bob", 100000, payroll, reporting)
        manager.add_report(Employee("Alice", 60000, payroll, reporting))
        reports = manager.get_reports()
        reports.clear()
        assert len(manager.get_reports()) == 1

    def test_reports_are_mangled(self, payroll, reporting):
        manager = Manager("Bob", 100000, payroll, reporting)
        assert hasattr(manager, "_Manager__reports")
        assert not hasattr(manager, "reports")


class TestContractor:
    def test_pay_is_contract_amount_after_tax(self, payroll):
        assert Contractor("Charlie", 50000, payroll).calculate_pay() == 40000.0

    def test_contract_amount_drives_pay(self, payroll):
        assert Contractor("Charlie", 25000, payroll).calculate_pay() == 20000.0

    def test_name_is_mangled(self, payroll):
        contractor = Contractor("Charlie", 50000, payroll)
        assert contractor._Contractor__contract_amount == 50000
        assert not hasattr(contractor, "contract_amount")


class TestPayrollAcrossRoles:
    def test_all_roles_are_paid_consistently(self, payroll, reporting):
        employee = Employee("Alice", 100000, payroll, reporting)
        manager = Manager("Bob", 100000, payroll, reporting)
        contractor = Contractor("Charlie", 100000, payroll)
        for worker in (employee, manager, contractor):
            assert isinstance(worker, Payable)
            assert worker.calculate_pay() == 80000.0

    def test_reporting_service_is_swappable(self, payroll):
        class TerseReportingService:
            def generate(self, name, role):
                return f"{role}:{name}"

        employee = Employee("Alice", 60000, payroll, TerseReportingService())
        assert employee.generate_report() == "Employee:Alice"
