"""Tests for Prototype Pattern implementations."""
import pytest
from prototype.document_prototype import ReportDocument
from prototype.user_prototype import (
    AdminUser,
    RegularUser,
    UserPrototypeRegistry,
    Permission,
)


class TestDocumentPrototype:
    """Tests for document cloning."""

    def test_clone_returns_independent_copy(self):
        template = ReportDocument("Annual Report", "Author")
        clone = template.clone()
        assert clone is not template
        assert clone.title == template.title
        assert clone.author == template.author

    def test_clone_deep_copies_sections(self):
        template = ReportDocument("Report", "Author")
        clone = template.clone()
        clone.add_section("Appendix")
        assert "Appendix" in clone.sections
        assert "Appendix" not in template.sections

    def test_clone_deep_copies_metadata(self):
        template = ReportDocument("Report", "Author")
        clone = template.clone()
        clone.set_metadata("custom_key", "custom_value")
        assert "custom_key" in clone.metadata
        assert "custom_key" not in template.metadata

    def test_clone_does_not_reload_from_db(self, capsys):
        template = ReportDocument("Report", "Author")
        captured1 = capsys.readouterr()
        clone = template.clone()
        captured2 = capsys.readouterr()
        assert "[DB]" in captured1.out
        assert "[DB]" not in captured2.out

    def test_multiple_clones_are_independent(self):
        template = ReportDocument("Report", "Author")
        c1 = template.clone()
        c2 = template.clone()
        c1.set_title("C1")
        c2.set_title("C2")
        assert template.title == "Report"
        assert c1.title == "C1"
        assert c2.title == "C2"


class TestUserPrototype:
    """Tests for user prototype pattern."""

    def test_admin_clone_has_full_permissions(self):
        admin = AdminUser()
        clone = admin.clone()
        assert clone.permissions == {Permission.READ, Permission.WRITE,
                                     Permission.DELETE, Permission.ADMIN}

    def test_clone_is_independent(self):
        admin = AdminUser()
        clone = admin.clone()
        clone.remove_permission(Permission.DELETE)
        assert Permission.DELETE in admin.permissions
        assert Permission.DELETE not in clone.permissions

    def test_regular_user_clone(self):
        user = RegularUser()
        clone = user.clone()
        clone.add_permission(Permission.WRITE)
        assert Permission.WRITE in clone.permissions
        assert user.permissions == {Permission.READ}

    def test_registry_creates_clones(self):
        registry = UserPrototypeRegistry()
        registry.register("admin", AdminUser())
        user1 = registry.create("admin")
        user2 = registry.create("admin")
        assert user1 is not user2
        assert user1.permissions == user2.permissions

    def test_registry_missing_prototype_raises(self):
        registry = UserPrototypeRegistry()
        with pytest.raises(KeyError, match="No prototype registered"):
            registry.create("nonexistent")

    def test_registry_unregister(self):
        registry = UserPrototypeRegistry()
        registry.register("admin", AdminUser())
        registry.unregister("admin")
        assert "admin" not in registry.list_prototypes()
