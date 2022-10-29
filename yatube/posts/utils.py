from django.core.paginator import Paginator

LAST_POSTS: int = 10


def paginate(queryset, request):
    paginator = Paginator(queryset, LAST_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
