from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from transactions.models import Transaction
from .forms import CustomUserCreationForm, TransactionForm
from django.shortcuts import render, redirect
from django.db.models import Sum
from django.db.models.functions import Coalesce  
# Create your views here.

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    return redirect('register')

@login_required
def dashboard(request):
    user = request.user

    transactions = Transaction.objects.filter(user=user)


    spending_by_category = transactions.annotate(
        top_level_name=Coalesce('category__parent__name', 'category__name')).values(
            'top_level_name').annotate(total=Sum('amount'))

    spending_by_subcategory = transactions.values("category__name", "category__parent__name").annotate(total=Sum("amount"))

    total_spent = transactions.aggregate(total=Sum("amount"))["total"] or 0

    category_data = {}

    for item in spending_by_category:
        category_name = item['top_level_name']
        category_total = item['total']
        category_data[category_name] = {"total": category_total, "subcategories": []}

    for item in spending_by_subcategory:
        parent_name = item["category__parent__name"]
        if parent_name != None and parent_name in category_data:
            subcategory_name = item['category__name']
            sub_total = item.get("total")
            category_data[parent_name]['subcategories'].append({"name": subcategory_name, "total": sub_total})


    
    context = {
        "total_spent": total_spent,
        "category_data": category_data,
    }

    print(category_data)
    
    return render(request, "transactions/dashboard.html", context)

def register(request):
    if request.method == "POST":
        f = CustomUserCreationForm(request.POST)
        if f.is_valid():
            user = f.save()
            login(request, user)
            return redirect('dashboard')

    else:
        f = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form' : f})

def add_transaction(request):
    if request.method == "POST":
        f = TransactionForm(request.POST)

        if f.is_valid():
            transaction = f.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('dashboard')

    else: 
        f = TransactionForm()

    return render(request, 'transactions/add.html', {'form' : f}) 










