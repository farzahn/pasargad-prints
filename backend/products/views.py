from rest_framework import generics, filters, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, Min, Max, F, Prefetch
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from .models import Category, Product, ProductReview, ProductImage
from .serializers import CategorySerializer, ProductListSerializer, ProductDetailSerializer, ProductReviewSerializer
from utils.cache import CacheMixin, cache_response, CacheKeys, get_or_set_cache
import logging

logger = logging.getLogger(__name__)


class CategoryListView(CacheMixin, generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True).prefetch_related(
        Prefetch('products', queryset=Product.objects.filter(is_active=True))
    )
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    cache_timeout = 3600  # 1 hour
    cache_key_prefix = 'category_list'
    
    def list(self, request, *args, **kwargs):
        # Try to get from cache first
        cached_response = self.get_cached_response()
        if cached_response:
            return Response(cached_response)
        
        # Get fresh data
        response = super().list(request, *args, **kwargs)
        
        # Cache the response
        self.set_cached_response(response)
        
        return response


class ProductListView(CacheMixin, generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'description', 'material']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']
    cache_timeout = 60  # 1 minute
    cache_key_prefix = 'product_list'

    def get_queryset(self):
        # Optimize queries with select_related and prefetch_related
        queryset = Product.objects.filter(is_active=True).select_related(
            'category'
        ).prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.filter(is_main=True)),
            'reviews'
        ).annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        )
        
        # Price range filtering
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # In stock filtering
        in_stock = self.request.query_params.get('in_stock')
        if in_stock:
            if in_stock.lower() == 'true':
                queryset = queryset.filter(stock_quantity__gt=0)
            elif in_stock.lower() == 'false':
                queryset = queryset.filter(stock_quantity=0)
        
        # Full-text search optimization
        search_query = self.request.query_params.get('search')
        if search_query:
            # Use database-agnostic search for compatibility
            from django.conf import settings
            if getattr(settings, 'DATABASE_TYPE', 'sqlite') == 'postgresql':
                # Use PostgreSQL full-text search
                queryset = queryset.filter(
                    Q(search_vector=SearchQuery(search_query)) |
                    Q(name__icontains=search_query) |
                    Q(description__icontains=search_query)
                )
            else:
                # Use simple text search for SQLite
                queryset = queryset.filter(
                    Q(name__icontains=search_query) |
                    Q(description__icontains=search_query) |
                    Q(material__icontains=search_query) |
                    Q(category__name__icontains=search_query)
                )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Check cache first
        cache_key = CacheKeys.get_product_list_key(**request.query_params.dict())
        
        def get_data():
            response = super(ProductListView, self).list(request, *args, **kwargs)
            return response.data
        
        cached_data = get_or_set_cache(
            cache_key,
            get_data,
            timeout=self.cache_timeout,
            cache_alias='api'
        )
        
        return Response(cached_data)


class ProductDetailView(CacheMixin, generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True).select_related(
        'category'
    ).prefetch_related(
        'images',
        Prefetch('reviews', queryset=ProductReview.objects.select_related('user').order_by('-created_at'))
    )
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    cache_timeout = 600  # 10 minutes
    cache_key_prefix = 'product_detail'
    
    def retrieve(self, request, *args, **kwargs):
        # Try cache first
        cache_key = f"{CacheKeys.PRODUCT_DETAIL.format(id=kwargs.get('pk'))}"
        
        def get_data():
            response = super(ProductDetailView, self).retrieve(request, *args, **kwargs)
            return response.data
        
        cached_data = get_or_set_cache(
            cache_key,
            get_data,
            timeout=self.cache_timeout,
            cache_alias='api'
        )
        
        return Response(cached_data)




class ProductReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        product_id = self.kwargs['product_id']
        return ProductReview.objects.filter(product_id=product_id)

    def perform_create(self, serializer):
        product_id = self.kwargs['product_id']
        serializer.save(product_id=product_id)


class ProductReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProductReview.objects.filter(user=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_products(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return Response({'results': [], 'count': 0})
    
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query) |
        Q(category__name__icontains=query) |
        Q(material__icontains=query),
        is_active=True
    )[:10]
    
    serializer = ProductListSerializer(products, many=True, context={'request': request})
    return Response({
        'results': serializer.data,
        'count': products.count()
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def advanced_search(request):
    """Advanced search with full-text search and multiple filters."""
    try:
        # Get search query
        query = request.GET.get('q', '').strip()
        
        # Start with active products
        products = Product.objects.filter(is_active=True)
        
        # Full-text search if query provided
        if query and len(query) >= 2:
            from django.conf import settings
            if getattr(settings, 'DATABASE_TYPE', 'sqlite') == 'postgresql':
                # Use PostgreSQL full-text search
                search_query = SearchQuery(query)
                search_vector = SearchVector('name', weight='A') + \
                               SearchVector('description', weight='B') + \
                               SearchVector('category__name', weight='C') + \
                               SearchVector('material', weight='D')
                
                products = products.annotate(
                    search=search_vector,
                    rank=SearchRank(search_vector, search_query)
                ).filter(search=search_query).order_by('-rank')
            else:
                # Use simple text search for SQLite
                products = products.filter(
                    Q(name__icontains=query) |
                    Q(description__icontains=query) |
                    Q(category__name__icontains=query) |
                    Q(material__icontains=query)
                ).order_by('-created_at')
        
        # Category filter
        category_ids = request.GET.getlist('category[]')
        if category_ids:
            products = products.filter(category_id__in=category_ids)
        
        # Price range filter
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
        
        # Stock filter
        stock_filter = request.GET.get('stock')
        if stock_filter == 'in_stock':
            products = products.filter(stock_quantity__gt=0)
        elif stock_filter == 'low_stock':
            products = products.filter(
                stock_quantity__gt=0,
                stock_quantity__lte=F('low_stock_threshold')
            )
        elif stock_filter == 'out_of_stock':
            products = products.filter(stock_quantity=0)
        
        # Material filter
        materials = request.GET.getlist('material[]')
        if materials:
            products = products.filter(material__in=materials)
        
        # Weight range filter
        min_weight = request.GET.get('min_weight')
        max_weight = request.GET.get('max_weight')
        if min_weight:
            products = products.filter(weight__gte=min_weight)
        if max_weight:
            products = products.filter(weight__lte=max_weight)
        
        # Print time filter
        max_print_time = request.GET.get('max_print_time')
        if max_print_time:
            products = products.filter(print_time__lte=max_print_time)
        
        
        # Rating filter
        min_rating = request.GET.get('min_rating')
        if min_rating:
            products = products.annotate(
                avg_rating=Avg('reviews__rating')
            ).filter(avg_rating__gte=min_rating)
        
        # Sorting
        sort_by = request.GET.get('sort', '-created_at')
        sort_options = {
            'price_asc': 'price',
            'price_desc': '-price',
            'name_asc': 'name',
            'name_desc': '-name',
            'newest': '-created_at',
            'oldest': 'created_at',
            'rating': '-avg_rating',
            'popularity': '-view_count'
        }
        
        if sort_by == 'rating':
            products = products.annotate(avg_rating=Avg('reviews__rating'))
        elif sort_by == 'popularity':
            products = products.annotate(view_count=Count('views'))
        
        if sort_by in sort_options:
            products = products.order_by(sort_options[sort_by])
        
        # Pagination
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        offset = (page - 1) * per_page
        
        total_count = products.count()
        products = products[offset:offset + per_page]
        
        # Get available filters
        all_products = Product.objects.filter(is_active=True)
        available_filters = {
            'categories': list(Category.objects.filter(
                products__in=all_products
            ).distinct().values('id', 'name')),
            'materials': list(all_products.values_list('material', flat=True).distinct()),
            'price_range': {
                'min': float(all_products.aggregate(min_price=Min('price'))['min_price'] or 0),
                'max': float(all_products.aggregate(max_price=Max('price'))['max_price'] or 0)
            },
            'weight_range': {
                'min': float(all_products.aggregate(min_weight=Min('weight'))['min_weight'] or 0),
                'max': float(all_products.aggregate(max_weight=Max('weight'))['max_weight'] or 0)
            }
        }
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        
        return Response({
            'results': serializer.data,
            'count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page,
            'filters': available_filters
        })
        
    except Exception as e:
        logger.error(f"Error in advanced search: {str(e)}")
        return Response(
            {'error': 'Search failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_low_stock_products(request):
    """Get products that are low in stock."""
    try:
        # Only accessible by staff
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        products = Product.objects.filter(
            is_active=True,
            stock_quantity__gt=0,
            stock_quantity__lte=F('low_stock_threshold')
        ).order_by('stock_quantity')
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        
        return Response({
            'results': serializer.data,
            'count': products.count()
        })
        
    except Exception as e:
        logger.error(f"Error getting low stock products: {str(e)}")
        return Response(
            {'error': 'Failed to get low stock products'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )