import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings')
django.setup()

from products.models import Product

# Get all featured products
featured_products = Product.objects.filter(is_featured=True)

print("Updating stock for featured products:\n")

for product in featured_products:
    old_stock = product.stock_quantity
    # Set a good amount of stock for testing
    new_stock = 100
    product.stock_quantity = new_stock
    product.save()
    
    print(f"✓ {product.name}")
    print(f"  Previous stock: {old_stock}")
    print(f"  New stock: {new_stock}")
    print(f"  Price: ${product.price}")
    print()

# Also update non-featured products to have some stock
non_featured = Product.objects.filter(is_featured=False)
for product in non_featured:
    if product.stock_quantity < 50:
        product.stock_quantity = 50
        product.save()
        print(f"✓ Updated {product.name} to 50 units")

print("\n📊 Stock Summary:")
print(f"Total products: {Product.objects.count()}")
print(f"Featured products: {Product.objects.filter(is_featured=True).count()}")
print(f"In stock products: {Product.objects.filter(stock_quantity__gt=0).count()}")
print(f"Out of stock products: {Product.objects.filter(stock_quantity=0).count()}")

# Show all products with their current stock
print("\n📦 All Products Stock Status:")
print("-" * 60)
for product in Product.objects.all().order_by('-is_featured', 'name'):
    status = "⭐ FEATURED" if product.is_featured else ""
    print(f"{product.name:<30} Stock: {product.stock_quantity:>4} {status}")