from django.core.exceptions import FieldError
from django.db.models.fields import Field
from django.forms import Field as FormField
from django.forms.boundfield import BoundField


class NullModelOptions(object):
    def __init__(self, field_name):
        self.field_name = field_name

    @property
    def pk(self):
        return self.get_field("pk")

    def get_field(self, name):
        raise FieldError(
            "Cannot resolve keyword %r into field. Join on '%s'"
            " not permitted." % (name, self.field_name)
        )


class EmptyPathInfo(object):
    def __init__(self, field):
        self.join_field = field
        self.to_opts = NullModelOptions(field.name)
        self.target_fields = (field,)

    def __iter__(self):
        return self

    def __next__(self):
        raise StopIteration()

    def next(self):
        raise StopIteration()

    def __getitem__(self, key):
        if key == -1:
            return self
        raise Exception("This shouldn't be called: {}".format(key))


class DeprecatedField(Field):
    @staticmethod
    def warn(message):
        import warnings

        warnings.warn(message, DeprecationWarning)

    def __init__(self, field_path):
        super(DeprecatedField, self).__init__()
        self.field_path = field_path

    def __get__(self, instance, instance_type=None):
        self._warn()
        return getattr(instance, self.field_path)

    def __set__(self, instance, value):
        self._warn()
        setattr(instance, self.field_path, value)

    def _warn(self):
        message = 'Field {module}.{model}#{name} is deprecated. Please, use field "{field_path}".'
        DeprecatedField.warn(
            message.format(
                module=self.model.__module__,
                model=self.model.__name__,
                name=self.name,
                field_path=self.field_path,
            )
        )

    @property
    def aliased_field(self):
        return self.model._meta.get_field(self.field_path)

    def contribute_to_class(self, cls, name):
        super(DeprecatedField, self).contribute_to_class(cls, name, True)
        setattr(cls, name, self)

    def formfield(self, **kwargs):
        return DeprecatedFormField(aliased_field_name=self.field_path, **kwargs)

    def get_attname_column(self):
        attname = self.get_attname()
        # This method is overriden because this field does not corresponds to a column.
        # Because of this, self.concrete is False.
        column = None
        return attname, column

    def get_path_info(self, filtered_relation=None):
        aliased_field = self.aliased_field
        if hasattr(aliased_field, "get_path_info"):
            func = aliased_field.get_path_info
            if hasattr(func, "im_func"):
                func = func.im_func
            kwargs = {}
            if func.__code__.co_argcount > 1:
                kwargs["filtered_relation"] = filtered_relation
            return aliased_field.get_path_info(**kwargs)
        else:
            return EmptyPathInfo(aliased_field)

    def save_form_data(self, instance, data):
        """
        Avoid deleting data in the aliased field if no value was provided for
        the deprecated field; if both the deprecated field and alias field
        are blank, and blank is False, Django will raise a ValidationError.
        """
        aliased_field = self.aliased_field
        if not aliased_field.blank and data is None:
            return
        return super().save_form_data(instance, data)

    def value_from_object(self, obj):
        """
        Used by model_to_dict() and elsewhere; because this isn't a direct
        access, avoid using the __get__() method and triggering a warning.
        """
        return getattr(obj, self.field_path)


class DeprecatedFormField(FormField):
    def __init__(self, aliased_field_name, **kwargs):
        self.aliased_field_name = aliased_field_name
        super().__init__(**kwargs)
        self.required = False

    def widget_attrs(self, widget):
        return {"disabled": True}
