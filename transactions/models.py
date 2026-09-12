from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

# Create your models here.

class Category(models.Model):
    """
    User-owned category for transactions, supporting a two-level hierarchy.

    Categories can have an optional parent, allowing subcategories. This design
    assumes categories are at most two levels deep (top-level or one-level child);
    deeper nesting would require changes to dashboard aggregation logic.
      """

    class Type(models.TextChoices):
        """Enumeration of category kinds: Income or Expense.

        Used to classify top-level categories, with the constraint that all
        subcategories must inherit the same kind as their parent. This supports
        the dashboard's aggregation by kind and prevents mixing transaction types
        within a single parent category.
        """
        INCOME = "In", "Income"
        EXPENSE = "Ex", "Expense"

    name = models.CharField(max_length=200,)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # 'kind' (Income/Expense) is stored on Category, not Transaction, because all
    # transactions within a category must share the same type. This supports the
    # two-level hierarchy design and enables dashboard aggregation by kind.
    kind = models.CharField(
                max_length=3,
                choices=Type.choices)


    def __str__(self):
        """Return the category name."""
        return self.name

class Transaction(models.Model):
    """
    A single financial transaction recorded by a user.

    Transactions are scoped to a user and optionally associated with a category.
    If a category is deleted, the transaction remains with category=NULL.
    """
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_time = models.DateTimeField(default=timezone.now)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.CharField(max_length=100, default='', blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    

    def __str__(self):
        """
        Return a human-readable string representation.

        Shows date, category name, and amount if category is set; otherwise
        returns 'Unknown' to handle transactions with deleted categories.
        """
        if self.category:
            return f"{self.date_time.date()}: {self.category.name} - {self.amount}"
        else:
            return "Unknown"
