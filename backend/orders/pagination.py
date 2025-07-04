from rest_framework.pagination import PageNumberPagination


class OrderPagination(PageNumberPagination):
    """Custom pagination for orders with flexible page size."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """Add additional metadata to paginated response."""
        response = super().get_paginated_response(data)
        response.data['page_size'] = self.get_page_size(self.request)
        response.data['total_pages'] = self.page.paginator.num_pages
        return response