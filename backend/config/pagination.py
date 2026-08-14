from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Стандартная пагинация с настраиваемым размером страницы."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
