from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import Category

from .models import Transaction

class CustomUserCreationForm(UserCreationForm):
    """User registration form that adds an email field to the default Django form."""
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']    

class TransactionForm(forms.ModelForm):
    """User-scoped transaction form that filters categories by ownership and hierarchy.

    Expects 'user' as a keyword argument on instantiation. Restricts the category
    dropdown to only show subcategories (parent__isnull=False) belonging to that user.
    This prevents category leakage across users and enforces the UI constraint that
    only leaf categories are selectable for transactions.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the form with user-scoped category filtering.

        Pops 'user' from kwargs (with None default) so callers that omit it do not
        crash. Restricts category queryset to subcategories owned by the user.
        """
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=self.user, parent__isnull=False)

    class Meta:
        model = Transaction
        exclude = ['user']

class CategoryForm(forms.ModelForm):
    """User-scoped category form that enforces two-level hierarchy and kind consistency.

    Restricts the parent dropdown to show only top-level categories owned by the user,
    preventing users from accidentally creating deeper nesting. The clean() method
    enforces that subcategories must have the same kind (Income/Expense) as their parent,
    maintaining type consistency across the two-level hierarchy.
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
        """Validate that a subcategory's kind matches its parent's kind.

        The two-level category hierarchy requires that all categories at a given level
        share the same kind (Income or Expense). This validation prevents mixing
        income and expense transactions within a single parent category.
        """
        self.cleaned_data = super().clean()
        if self.cleaned_data.get('parent') is not None:
            if not self.cleaned_data.get('kind') == self.cleaned_data['parent'].kind:
                raise forms.ValidationError(f'The new category ({self.cleaned_data.get('name')}), does not match the parents kind')

        return self.cleaned_data

    class Meta:
        model = Category
        exclude = ['user']

        




