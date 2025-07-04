import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings')
django.setup()

from products.models import Category, Product, ProductImage

# Create categories
categories_data = [
    {
        'name': 'Miniatures',
        'description': 'Detailed miniature figures for gaming and display'
    },
    {
        'name': 'Home Decor',
        'description': 'Beautiful 3D printed items for your home'
    },
    {
        'name': 'Jewelry',
        'description': 'Custom 3D printed jewelry and accessories'
    },
    {
        'name': 'Tools & Gadgets',
        'description': 'Practical 3D printed tools and gadgets'
    }
]

categories = {}
for cat_data in categories_data:
    category, created = Category.objects.get_or_create(
        name=cat_data['name'],
        defaults={'description': cat_data['description'], 'is_active': True}
    )
    categories[cat_data['name']] = category
    if created:
        print(f"Created category: {category.name}")

# Create products
products_data = [
    {
        'name': 'Dragon Miniature',
        'category': 'Miniatures',
        'sku': 'MIN-DRG-001',
        'price': Decimal('29.99'),
        'description': 'Detailed dragon miniature perfect for tabletop gaming',
        'stock_quantity': 50,
        'weight': '0.05',
        'material': 'PLA',
        'print_time': 4
    },
    {
        'name': 'Geometric Planter',
        'category': 'Home Decor',
        'sku': 'HD-PLT-001',
        'price': Decimal('24.99'),
        'description': 'Modern geometric planter for small plants',
        'stock_quantity': 30,
        'weight': '0.15',
        'material': 'PETG',
        'print_time': 6
    },
    {
        'name': 'Custom Name Keychain',
        'category': 'Jewelry',
        'sku': 'JWL-KEY-001',
        'price': Decimal('9.99'),
        'description': 'Personalized keychain with your name',
        'stock_quantity': 100,
        'weight': '0.02',
        'material': 'PLA',
        'print_time': 1
    },
    {
        'name': 'Phone Stand',
        'category': 'Tools & Gadgets',
        'sku': 'TG-PHN-001',
        'price': Decimal('14.99'),
        'description': 'Adjustable phone stand for desk use',
        'stock_quantity': 75,
        'weight': '0.08',
        'material': 'ABS',
        'print_time': 3
    },
    {
        'name': 'Knight Miniature Set',
        'category': 'Miniatures',
        'sku': 'MIN-KNT-001',
        'price': Decimal('39.99'),
        'description': 'Set of 5 detailed knight miniatures',
        'stock_quantity': 25,
        'weight': '0.10',
        'material': 'Resin',
        'print_time': 8
    }
]

for prod_data in products_data:
    category = categories[prod_data.pop('category')]
    product, created = Product.objects.get_or_create(
        name=prod_data['name'],
        category=category,
        defaults=prod_data
    )
    if created:
        print(f"Created product: {product.name}")

print("\nSample data creation completed!")
print(f"Total categories: {Category.objects.count()}")
print(f"Total products: {Product.objects.count()}")