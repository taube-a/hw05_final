from django.core.paginator import Paginator
from django.conf import settings

from .models import Follow


def add_paginator(request, post_list):
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def get_following_list(user):
    user_following = Follow.objects.filter(user=user)
    following_list = []
    for follow in user_following:
        following_list.append(follow.author)
    return following_list
