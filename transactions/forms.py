from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from .models import Category
from .models import Transaction

class FormStyling():
    """Apply Bootstrap CSS classes to every field widget in a form.

    Mix this into any Django form subclass (``forms.Form`` or ``forms.ModelForm``) so
    all forms share the same styling in one place (DRY). Select widgets, including subclasses, get ``form-select``; every
    other widget gets ``form-control``. Classes are added with ``attrs.update()``,
    so attributes Django sets, such as ``step="0.01"`` or ``maxlength``, are kept.
    Templates can then render ``{{ form.as_p }}`` and still receive the styling.

    List this class leftmost in the bases, e.g. ``class X(FormStyling, forms.ModelForm)``.
    ``super()`` follows the MRO of the instance being built, so FormStyling reaches the
    next ``__init__`` in the chain without inheriting from it: ``BaseModelForm.__init__``
    for a ModelForm (which ``ModelForm`` inherits), or ``BaseForm.__init__`` for a plain Form. If it is listed after
    ``ModelForm``, the chain stops at Django's ``BaseForm.__init__``, which does not
    call ``super()``. No error is raised, but the inputs are silently left unstyled.
    """

    def __init__(self, *args, **kwargs):
        """Run Django's form ``__init__`` first, then style the fields.

        ``self.fields`` is created inside Django's ``__init__``, so the loop must run
        after ``super().__init__()``. Looping first raises ``AttributeError``.
        """
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            if isinstance(field.widget, forms.widgets.Select):
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

class CustomUserCreationForm(FormStyling, UserCreationForm):
    """Add an email field to Django's registration form and style its widgets.

    Extends ``UserCreationForm`` with an ``email`` field, so the form shows ``username``,
    ``email``, ``password1``, and ``password2``. ``FormStyling`` is listed leftmost in the
    bases, so every widget receives its Bootstrap class (``form-control`` or ``form-select``).

    The inner ``Meta`` inherits from ``UserCreationForm.Meta``, which keeps the parent's
    ``field_classes`` (``username`` uses ``UsernameField``). It then overrides ``model`` and
    ``fields``. The parent's ``Meta.fields`` is ``("username",)``, so the override is what
    adds ``email`` to the form.
    """
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class CustomAuthForm(FormStyling, AuthenticationForm):
    """Provide a Bootstrap-styled login form based on Django's AuthenticationForm.

    ``AuthenticationForm`` is a plain ``forms.Form``, not a ModelForm, so this class has no
    inner ``Meta``. Its ``username`` and ``password`` fields are declared directly on the
    parent class. ``FormStyling`` is listed leftmost in the bases, so its ``__init__`` runs
    and applies the Bootstrap classes to both inputs. This class defines no ``__init__``
    of its own because the inherited one is enough.
    """


class TransactionForm(FormStyling, forms.ModelForm):
    """User-scoped transaction form that filters categories by ownership and hierarchy.

    Expects 'user' as a keyword argument on instantiation. Restricts the category
    dropdown to only show subcategories (parent__isnull=False) belonging to that user.
    This prevents category leakage across users and enforces the UI constraint that
    only leaf categories are selectable for transactions.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the form with user-scoped category choices.

        Pops 'user' from kwargs (with None default) so callers that omit it do not crash.
        Restricts the category queryset to subcategories owned by the user. Widget
        styling is applied by the FormStyling parent class.
        """
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=self.user, parent__isnull=False)

    class Meta:
        model = Transaction
        exclude = ['user']

class CategoryForm(FormStyling, forms.ModelForm):
    """User-scoped category form that enforces two-level hierarchy and kind consistency.

    Restricts the parent dropdown to show only top-level categories owned by the user,
    preventing users from accidentally creating deeper nesting. The clean() method
    rejects a duplicate name at the same level and enforces that subcategories must have
    the same kind (Income/Expense) as their parent, maintaining type consistency across
    the two-level hierarchy.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the form with user-scoped parent category filtering.

        Pops 'user' from kwargs (with None default) so callers that omit it do not crash.
        Restricts parent queryset to only top-level categories (parent__isnull=True)
        owned by the user, enforcing the two-level hierarchy design.
        """
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = Category.objects.filter(user=self.user, parent__isnull=True)
        self.fields['parent'].empty_label = "None (turn into a top-level category)"

    def clean(self):
        """Run the duplicate-name check, then the kind-consistency check.

        First, rejects a name the user already has at the same level: same user, same
        name, and same parent, where a parent of None means a top-level category.
        Second, when a parent is set, rejects a kind (Income or Expense) that differs
        from the parent's kind, so income and expense never mix within one parent.

        The duplicate check lives in the form because ``user`` is excluded from this form.
        During ``is_valid()``, Django skips model-level validation of a UniqueConstraint
        when any of its fields is excluded, so without this check a duplicate would reach
        the database and raise ``IntegrityError``.
        """
        self.cleaned_data = super().clean()

        category_exists = Category.objects.filter(user=self.user, name=self.cleaned_data.get('name'), parent=self.cleaned_data.get('parent')).exists()

        if category_exists:
            raise forms.ValidationError(f"You already have a category named: {self.cleaned_data.get('name')}.")

        if self.cleaned_data.get('parent') is not None:
            if not self.cleaned_data.get('kind') == self.cleaned_data['parent'].kind:
                raise forms.ValidationError(f"The new category ({self.cleaned_data.get('name')}), does not match the parent's kind")

        return self.cleaned_data

    class Meta:
        model = Category
        exclude = ['user']



