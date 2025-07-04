import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings')
django.setup()

from products.models import Product, ProductImage

# High-quality placeholder images that simulate iStock-style product photography
product_images = {
    'Dragon Miniature': [
        'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1581833971358-2c8b550f87b3?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1609205807107-e8ec83120f9d?w=800&h=600&fit=crop&q=80',
    ],
    'Geometric Planter': [
        'https://images.unsplash.com/photo-1485955900006-10f4d324d411?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1509937528035-ad76254b0356?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=800&h=600&fit=crop&q=80',
    ],
    'Custom Name Keychain': [
        'https://images.unsplash.com/photo-1516975080664-ed2fc6a32937?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1564466809058-bf4114d55352?w=800&h=600&fit=crop&q=80',
    ],
    'Phone Stand': [
        'https://images.unsplash.com/photo-1586253634026-8cb574908d1e?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1605236453806-6ff36851218e?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1625948515291-69613efd103f?w=800&h=600&fit=crop&q=80',
    ],
    'Knight Miniature Set': [
        'https://images.unsplash.com/photo-1606923829579-0cb981a83e2e?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1552820728-8b83bb6b773f?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1632501641765-e568d28b0015?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1609205807490-b15b9677c6b9?w=800&h=600&fit=crop&q=80',
    ],
    'Desk Organizer': [
        'https://images.unsplash.com/photo-1544816565-c199d6f5d2b3?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1518112166137-85f9979a43aa?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1524634126442-357e0eac3c14?w=800&h=600&fit=crop&q=80',
    ],
    'Decorative Vase': [
        'https://images.unsplash.com/photo-1581783342308-f792dbdd27c5?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1612198188060-c7c2a3b66eae?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1578500494198-246f612d3b3d?w=800&h=600&fit=crop&q=80',
    ],
    'Cable Management Clips': [
        'https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1625772452888-103c566d4c9a?w=800&h=600&fit=crop&q=80',
    ],
    'Wizard Miniature': [
        'https://images.unsplash.com/photo-1566140967404-b8b3932483f5?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1609343236319-edc0cb8d57d3?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1569163139394-de4798aa4aac?w=800&h=600&fit=crop&q=80',
    ],
    'Jewelry Box': [
        'https://images.unsplash.com/photo-1515709969750-23a0f4d9f8f0?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1606760227091-3dd870d97f1d?w=800&h=600&fit=crop&q=80',
        'https://images.unsplash.com/photo-1598532163257-ae3c6b2524b6?w=800&h=600&fit=crop&q=80',
    ]
}

# Delete all existing product images
ProductImage.objects.all().delete()
print("Cleared existing product images")

# Add images to products
for product_name, image_urls in product_images.items():
    try:
        product = Product.objects.get(name=product_name)
        
        for idx, image_url in enumerate(image_urls):
            ProductImage.objects.create(
                product=product,
                image_url=image_url,
                alt_text=f"{product_name} - View {idx + 1}",
                is_main=(idx == 0)
            )
        
        print(f"✓ Added {len(image_urls)} images for {product_name}")
            
    except Product.DoesNotExist:
        print(f"✗ Product '{product_name}' not found")

# Create some additional featured products with images
from decimal import Decimal
from products.models import Category

new_products = [
    {
        'name': 'Architectural Model House',
        'category': 'Home Decor',
        'sku': 'HD-ARC-001',
        'price': Decimal('89.99'),
        'description': 'Detailed miniature architectural model of a modern house',
        'stock_quantity': 15,
        'weight': '0.75',
        'dimensions': '30 x 20 x 15',
        'material': 'PLA',
        'print_time': 12,
        'images': [
            'https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800&h=600&fit=crop&q=80',
            'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&h=600&fit=crop&q=80',
            'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&h=600&fit=crop&q=80',
        ]
    },
    {
        'name': 'Articulated Robot Figure',
        'category': 'Tools & Gadgets',
        'sku': 'TG-ROB-001',
        'price': Decimal('54.99'),
        'description': 'Fully articulated robot figure with movable joints',
        'stock_quantity': 25,
        'weight': '0.15',
        'dimensions': '15 x 10 x 5',
        'material': 'ABS',
        'print_time': 6,
        'images': [
            'https://images.unsplash.com/photo-1563207153-f403bf289096?w=800&h=600&fit=crop&q=80',
            'https://images.unsplash.com/photo-1516192518150-0d8fee5425e3?w=800&h=600&fit=crop&q=80',
            'https://images.unsplash.com/photo-1535378620166-273708d44e4c?w=800&h=600&fit=crop&q=80',
        ]
    }
]

for prod_data in new_products:
    try:
        category = Category.objects.get(name=prod_data['category'])
        images = prod_data.pop('images')
        
        product, created = Product.objects.get_or_create(
            name=prod_data['name'],
            defaults={
                **prod_data,
                'category': category
            }
        )
        
        if created:
            print(f"\n✓ Created new product: {product.name}")
            
            # Create product images
            for idx, image_url in enumerate(images):
                ProductImage.objects.create(
                    product=product,
                    image_url=image_url,
                    alt_text=f"{product.name} - View {idx + 1}",
                    is_main=(idx == 0)
                )
            print(f"  Added {len(images)} images")
            
    except Category.DoesNotExist:
        print(f"✗ Category '{prod_data['category']}' not found")

print("\n✅ Product image population completed!")
print(f"Total products: {Product.objects.count()}")
print(f"Total product images: {ProductImage.objects.count()}")
# Featured products functionality removed