import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings')
django.setup()

from products.models import Product, ProductImage

# Placeholder images using Picsum (Lorem Picsum provides random images)
# These simulate professional product photography like iStock
product_images = {
    'Dragon Miniature': [
        'https://picsum.photos/800/600?random=1',  # Main image
        'https://picsum.photos/800/600?random=2',
        'https://picsum.photos/800/600?random=3',
    ],
    'Geometric Planter': [
        'https://picsum.photos/800/600?random=4',  # Main image
        'https://picsum.photos/800/600?random=5',
        'https://picsum.photos/800/600?random=6',
    ],
    'Custom Name Keychain': [
        'https://picsum.photos/800/600?random=7',  # Main image
        'https://picsum.photos/800/600?random=8',
    ],
    'Phone Stand': [
        'https://picsum.photos/800/600?random=9',  # Main image
        'https://picsum.photos/800/600?random=10',
        'https://picsum.photos/800/600?random=11',
    ],
    'Knight Miniature Set': [
        'https://picsum.photos/800/600?random=12',  # Main image
        'https://picsum.photos/800/600?random=13',
        'https://picsum.photos/800/600?random=14',
        'https://picsum.photos/800/600?random=15',
    ],
}

# Update products with main images and create additional images
for product_name, image_urls in product_images.items():
    try:
        product = Product.objects.get(name=product_name)
        
        # Set main image
        product.main_image = image_urls[0]
        product.save()
        print(f"Updated main image for {product_name}")
        
        # Delete existing images for this product
        ProductImage.objects.filter(product=product).delete()
        
        # Create product images
        for idx, image_url in enumerate(image_urls):
            ProductImage.objects.create(
                product=product,
                image=image_url,
                alt_text=f"{product_name} - View {idx + 1}",
                is_main=(idx == 0)
            )
            print(f"  Added image {idx + 1} for {product_name}")
            
    except Product.DoesNotExist:
        print(f"Product '{product_name}' not found")

# Add some new products with images to expand the catalog
new_products = [
    {
        'name': 'Desk Organizer',
        'category': 'Tools & Gadgets',
        'sku': 'TG-DSK-001',
        'price': '34.99',
        'description': 'Multi-compartment desk organizer for office supplies',
        'stock_quantity': 40,
        'weight': '0.25',
        'material': 'PLA',
        'print_time': 5,
        'main_image': 'https://picsum.photos/800/600?random=16',
        'images': [
            'https://picsum.photos/800/600?random=16',
            'https://picsum.photos/800/600?random=17',
            'https://picsum.photos/800/600?random=18',
        ]
    },
    {
        'name': 'Decorative Vase',
        'category': 'Home Decor',
        'sku': 'HD-VSE-001',
        'price': '44.99',
        'description': 'Modern spiral vase for flowers or decoration',
        'stock_quantity': 25,
        'weight': '0.30',
        'material': 'PETG',
        'print_time': 8,
        'main_image': 'https://picsum.photos/800/600?random=19',
        'images': [
            'https://picsum.photos/800/600?random=19',
            'https://picsum.photos/800/600?random=20',
            'https://picsum.photos/800/600?random=21',
        ]
    },
    {
        'name': 'Cable Management Clips',
        'category': 'Tools & Gadgets',
        'sku': 'TG-CBL-001',
        'price': '12.99',
        'description': 'Set of 10 cable management clips',
        'stock_quantity': 100,
        'weight': '0.05',
        'material': 'PLA',
        'print_time': 2,
        'main_image': 'https://picsum.photos/800/600?random=22',
        'images': [
            'https://picsum.photos/800/600?random=22',
            'https://picsum.photos/800/600?random=23',
        ]
    },
    {
        'name': 'Wizard Miniature',
        'category': 'Miniatures',
        'sku': 'MIN-WIZ-001',
        'price': '24.99',
        'description': 'Detailed wizard miniature with staff and spell effects',
        'stock_quantity': 35,
        'weight': '0.04',
        'material': 'Resin',
        'print_time': 3,
        'main_image': 'https://picsum.photos/800/600?random=24',
        'images': [
            'https://picsum.photos/800/600?random=24',
            'https://picsum.photos/800/600?random=25',
            'https://picsum.photos/800/600?random=26',
        ]
    },
    {
        'name': 'Jewelry Box',
        'category': 'Jewelry',
        'sku': 'JWL-BOX-001',
        'price': '29.99',
        'description': 'Elegant jewelry box with multiple compartments',
        'stock_quantity': 20,
        'weight': '0.20',
        'material': 'PLA',
        'print_time': 6,
        'main_image': 'https://picsum.photos/800/600?random=27',
        'images': [
            'https://picsum.photos/800/600?random=27',
            'https://picsum.photos/800/600?random=28',
            'https://picsum.photos/800/600?random=29',
        ]
    }
]

# Create new products
from products.models import Category

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
            print(f"\nCreated new product: {product.name}")
            
            # Create product images
            for idx, image_url in enumerate(images):
                ProductImage.objects.create(
                    product=product,
                    image=image_url,
                    alt_text=f"{product.name} - View {idx + 1}",
                    is_main=(idx == 0)
                )
                print(f"  Added image {idx + 1}")
        else:
            print(f"Product {product.name} already exists")
            
    except Category.DoesNotExist:
        print(f"Category '{prod_data['category']}' not found")

print("\n✓ Product images updated successfully!")
print(f"Total products: {Product.objects.count()}")
print(f"Total product images: {ProductImage.objects.count()}")
print(f"Active products: {Product.objects.filter(is_active=True).count()}")