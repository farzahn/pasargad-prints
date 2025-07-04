import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings')
django.setup()

from products.models import Product

# Get all products and update stock
all_products = Product.objects.filter(is_active=True)

print("Updating stock for all products:\n")

for product in all_products:
    old_stock = product.stock_quantity
    # Set a good amount of stock for testing
    new_stock = 100 if product.price > 50 else 50
    product.stock_quantity = new_stock
    product.save()
    
    print(f"✓ {product.name}")
    print(f"  Previous stock: {old_stock}")
    print(f"  New stock: {new_stock}")
    print(f"  Price: ${product.price}")
    print()

print("\n📊 Stock Summary:")
print(f"Total products: {Product.objects.count()}")
print(f"Active products: {Product.objects.filter(is_active=True).count()}")
print(f"In stock products: {Product.objects.filter(stock_quantity__gt=0).count()}")
print(f"Out of stock products: {Product.objects.filter(stock_quantity=0).count()}")

# Show all products with their current stock
print("\n📦 All Products Stock Status:")
print("-" * 60)
for product in Product.objects.all().order_by('-created_at', 'name'):
    status = "✅ ACTIVE" if product.is_active else "❌ INACTIVE"
    print(f"{product.name:<30} Stock: {product.stock_quantity:>4} {status}")