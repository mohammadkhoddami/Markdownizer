"""Classify a DocObject into a specialized documentation header kind."""

from __future__ import annotations

from markdownizer.parser import DocObject

_DJANGO_MODEL_BASES = {"Model", "AbstractUser", "AbstractBaseUser", "PermissionsMixin"}

_DRF_SERIALIZER_BASES = {
    "Serializer",
    "ModelSerializer",
    "ListSerializer",
    "BaseSerializer",
    "HyperlinkedModelSerializer",
}

_DRF_VIEW_BASES = {
    "ViewSet",
    "ModelViewSet",
    "GenericViewSet",
    "ReadOnlyModelViewSet",
    "APIView",
    "View",
    "GenericAPIView",
}

_DRF_VIEWSET_BASES = {
    "ViewSet",
    "ModelViewSet",
    "GenericViewSet",
    "ReadOnlyModelViewSet",
}

_DJANGO_ADMIN_BASES = {
    "ModelAdmin",
    "TabularInline",
    "StackedInline",
    "AdminSite",
    "InlineModelAdmin",
}

_DJANGO_FORM_BASES = {
    "Form",
    "ModelForm",
    "BaseForm",
    "BaseModelForm",
    "FormSet",
    "BaseFormSet",
    "BaseModelFormSet",
}

_ENUM_BASES = {"Enum", "IntEnum", "StrEnum", "Flag", "IntFlag"}


def _rightmost(name: str) -> str:
    return name.rsplit(".", 1)[-1] if name else ""


def classify(obj: DocObject) -> str:
    """Return a human-readable header label like 'DRF Serializer' or 'Async Function'."""
    if obj.kind == "module":
        if obj.file_path.endswith("__init__.py"):
            return "Package"
        return "Module"

    if obj.kind == "urlconf":
        return "URL Configuration"

    if obj.kind == "signal":
        return "Signal"

    if obj.kind == "class":
        rightmost_bases = {_rightmost(b) for b in obj.base_classes}
        decorator_rightmost = {
            _rightmost(_strip_decorator_prefix(d)) for d in obj.decorators
        }

        if "dataclass" in decorator_rightmost:
            return "Dataclass"

        if rightmost_bases & _ENUM_BASES:
            return "Enum"

        if rightmost_bases & _DRF_VIEWSET_BASES:
            return "DRF ViewSet"

        if rightmost_bases & _DRF_SERIALIZER_BASES:
            return "DRF Serializer"

        if rightmost_bases & {"APIView"}:
            return "DRF API View"

        if rightmost_bases & _DJANGO_ADMIN_BASES:
            return "Django Admin"

        if rightmost_bases & _DJANGO_FORM_BASES:
            return "Django Form"

        if rightmost_bases & _DJANGO_MODEL_BASES:
            return "Django Model"

        if rightmost_bases & {"MiddlewareMixin"} or obj.name.endswith("Middleware"):
            return "Middleware"

        if "BaseCommand" in rightmost_bases:
            return "Management Command"

        return "Class"

    if obj.kind == "function":
        dec_rightmost = {_rightmost(_strip_decorator_prefix(d)) for d in obj.decorators}
        if "property" in dec_rightmost or "cached_property" in dec_rightmost:
            return "Property"
        if "receiver" in dec_rightmost:
            return "Signal Handler"
        if obj.is_method:
            return "Async Method" if obj.is_async else "Method"
        return "Async Function" if obj.is_async else "Function"

    return obj.kind.title()


def _strip_decorator_prefix(dec: str) -> str:
    return dec[1:] if dec.startswith("@") else dec