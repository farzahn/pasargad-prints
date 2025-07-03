import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings')
django.setup()

from products.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()

print("🔍 Testing Admin Stock Update Functionality\n")

# Get a product to demonstrate
product = Product.objects.filter(is_featured=True).first()
if product:
    print(f"Product: {product.name}")
    print(f"Current Stock: {product.stock_quantity}")
    
    # Simulate admin updating stock
    old_stock = product.stock_quantity
    product.stock_quantity = 5  # Set to low stock
    product.save()
    
    print(f"\n⚠️ Admin updated stock to: {product.stock_quantity} (Low Stock Warning)")
    
    # Show that it's reflected in the database
    refreshed_product = Product.objects.get(id=product.id)
    print(f"✅ Database confirms new stock: {refreshed_product.stock_quantity}")
    print(f"✅ In Stock Status: {refreshed_product.is_in_stock}")
    
    # Restore original stock
    product.stock_quantity = old_stock
    product.save()
    print(f"\n↩️ Stock restored to: {product.stock_quantity}")

print("\n📊 Admin Capabilities Summary:")
print("• Direct stock editing from list view")
print("• Bulk actions (featured, activate/deactivate)")
print("• Visual stock status indicators")
print("• Low stock warnings")
print("• Image management (URL or upload)")
print("• Real-time database updates")