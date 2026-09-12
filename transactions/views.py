from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from transactions.models import Transaction, Category
from .forms import CustomUserCreationForm, TransactionForm, CategoryForm
from django.shortcuts import render, redirect
from django.db.models import Sum
from django.db.models.functions import Coalesce  
import json
# Create your views here.

def home(request):
    """
    Root entry point that redirects authenticated users to dashboard,
    unauthenticated users to registration.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    return redirect('register')

@login_required
def dashboard(request):
    """
    Display user's spending aggregated by category and subcategory.

    Uses two-pass aggregation: first query rolls all transactions into top-level
    categories (using Coalesce to treat parentless categories as top-level), then
    a second pass attaches subcategory breakdown to each parent. This assumes
    categories are at most two levels deep; deeper hierarchies would require
    recursive aggregation.
    """
    user = request.user

    transactions = Transaction.objects.filter(user=user)

    category_kind = transactions.values('category__kind').annotate(total=Sum('amount'))
    totals_by_kind = {item['category__kind']: item['total'] for item in category_kind}
    
    spending_by_category = transactions.annotate(
        top_level_name=Coalesce('category__parent__name', 'category__name')).values(
            'top_level_name').annotate(total=Sum('amount'))

    spending_by_subcategory = transactions.values("category__name", "category__parent__name").annotate(total=Sum("amount"))

    category_data = {}

    total_expense = totals_by_kind.get("Ex", 0)
    total_income = totals_by_kind.get("In", 0)
    net = total_income - total_expense

    for item in spending_by_category:
        category_name = item['top_level_name']
        category_total = item['total']
        category_data[category_name] = {"total": category_total, "subcategories": []}

    for item in spending_by_subcategory:
        parent_name = item["category__parent__name"]
        # Subcategories are only attached to parents that were already aggregated.
        # This filters out orphaned transactions and top-level categories with no parent.
        if parent_name != None and parent_name in category_data:
            subcategory_name = item['category__name']
            sub_total = item.get("total")
            category_data[parent_name]['subcategories'].append({"name": subcategory_name, "total": sub_total})


    
    context = {
        "total_expense": total_expense,
        "total_income": total_income,
        "net": net,
        "category_data": category_data
    }
    
    return render(request, "transactions/dashboard.html", context)

def register(request):
    """Create a new user account and immediately log them in upon success."""
    if request.method == "POST":
        f = CustomUserCreationForm(request.POST)
        if f.is_valid():
            user = f.save()
            login(request, user)
            return redirect('dashboard')

    else:
        f = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form' : f})

@login_required
def add_transaction(request):
    """Create a transaction for the logged-in user from form data."""
    if request.method == "POST":
        f = TransactionForm(request.POST, user=request.user)

        if f.is_valid():
            transaction = f.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('dashboard')

    else:
        f = TransactionForm(user=request.user)

    return render(request, 'transactions/add.html', {'form' : f}) 

@login_required
def add_category(request):
    """Create a category for the logged-in user from form data."""
    if request.method == "POST":
        f = CategoryForm(request.POST, user=request.user)

        if f.is_valid():
            category = f.save(commit=False)
            category.user = request.user
            category.save()
            return redirect('view_categories')

    else:
        f = CategoryForm(user=request.user)

    return render(request, 'transactions/add_category.html', {'form' : f})

@login_required
def view_categories(request):
    user = request.user
    categories = Category.objects.filter(user=user)

    context = {'categories': categories
               }

    return render(request, 'transactions/view_categories.html', context)












