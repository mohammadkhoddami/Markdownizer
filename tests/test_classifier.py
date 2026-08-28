"""Tests for the framework-aware classifier."""

from __future__ import annotations

from markdownizer.classifier import classify
from markdownizer.parser import DocObject


def _obj(
    kind: str,
    name: str = "X",
    base_classes: list[str] | None = None,
    decorators: list[str] | None = None,
    is_async: bool = False,
    is_method: bool = False,
    file_path: str = "mod.py",
) -> DocObject:
    return DocObject(
        name=name,
        qualified_name=name,
        kind=kind,
        lineno=1,
        end_lineno=1,
        anchor_lineno=1,
        docstring=None,
        decorators=decorators or [],
        source="",
        base_classes=base_classes or [],
        is_async=is_async,
        is_method=is_method,
        file_path=file_path,
    )


def test_module():
    assert classify(_obj("module", file_path="mod.py")) == "Module"


def test_package():
    assert classify(_obj("module", file_path="pkg/__init__.py")) == "Package"


def test_urlconf():
    assert classify(_obj("urlconf")) == "URL Configuration"


def test_signal():
    assert classify(_obj("signal")) == "Signal"


def test_plain_class():
    assert classify(_obj("class")) == "Class"


def test_django_model():
    assert classify(_obj("class", base_classes=["models.Model"])) == "Django Model"
    assert classify(_obj("class", base_classes=["AbstractUser"])) == "Django Model"


def test_django_form():
    assert classify(_obj("class", base_classes=["forms.ModelForm"])) == "Django Form"


def test_django_admin():
    assert classify(_obj("class", base_classes=["admin.ModelAdmin"])) == "Django Admin"


def test_middleware():
    assert classify(_obj("class", base_classes=["MiddlewareMixin"])) == "Middleware"
    assert classify(_obj("class", name="AuthMiddleware")) == "Middleware"


def test_management_command():
    assert classify(_obj("class", base_classes=["BaseCommand"])) == "Management Command"


def test_drf_serializer():
    assert classify(_obj("class", base_classes=["serializers.ModelSerializer"])) == "DRF Serializer"


def test_drf_viewset():
    assert classify(_obj("class", base_classes=["viewsets.ModelViewSet"])) == "DRF ViewSet"


def test_drf_api_view():
    assert classify(_obj("class", base_classes=["APIView"])) == "DRF API View"


def test_enum():
    assert classify(_obj("class", base_classes=["Enum"])) == "Enum"
    assert classify(_obj("class", base_classes=["IntEnum"])) == "Enum"


def test_dataclass():
    assert classify(_obj("class", decorators=["@dataclass"])) == "Dataclass"


def test_dataclass_with_call_args():
    assert classify(_obj("class", decorators=["@dataclass(frozen=True)"])) == "Dataclass"


def test_function():
    assert classify(_obj("function")) == "Function"


def test_async_function():
    assert classify(_obj("function", is_async=True)) == "Async Function"


def test_method():
    assert classify(_obj("function", is_method=True)) == "Method"


def test_async_method():
    assert classify(_obj("function", is_async=True, is_method=True)) == "Async Method"


def test_property():
    assert classify(_obj("function", decorators=["@property"])) == "Property"


def test_cached_property():
    assert classify(_obj("function", decorators=["@cached_property"])) == "Property"


def test_signal_handler():
    assert classify(_obj("function", decorators=["@receiver"])) == "Signal Handler"


def test_signal_handler_with_call_args():
    assert (
        classify(
            _obj(
                "function",
                decorators=["@receiver(post_save, sender=User)"],
            )
        )
        == "Signal Handler"
    )


def test_signal_handler_method_with_call_args():
    assert (
        classify(
            _obj(
                "function",
                decorators=["@receiver(post_save, sender=User)"],
                is_method=True,
            )
        )
        == "Signal Handler"
    )


def test_dotted_decorator():
    assert (
        classify(
            _obj(
                "function",
                decorators=["@django.utils.functional.cached_property"],
            )
        )
        == "Property"
    )


def test_unknown_kind_falls_back_to_title():
    assert classify(_obj("weird")) == "Weird"
