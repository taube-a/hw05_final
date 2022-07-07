from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Comment, Follow
from .utils import add_paginator, get_following_list


def index(request):
    post_list = Post.objects.all()
    context = {'title': 'Последние обновления на сайте',
               'page_obj': add_paginator(request, post_list), }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = {'group': group,
               'page_obj': add_paginator(request, post_list), }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_list = Post.objects.filter(author=author)
    context = {'author': author,
               'count': posts_list.count(),
               'page_obj': add_paginator(request, posts_list), }
    if request.user.is_authenticated:
        following_list = get_following_list(request.user)
        if author in following_list:
            context['following'] = True
    return render(request, 'posts/profile.html', context)


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = Comment.objects.filter(post=post)
    comment_form = CommentForm(request.POST or None)
    context = {'post': post,
               'form': comment_form,
               'comments': comments,
               'count': Post.objects.filter(author=post.author).count(), }
    return render(request, 'posts/post_detail.html', context)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect('posts:profile', username=request.user.username)
        return render(request, 'posts/create_post.html', {'form': form})
    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.user == post.author:
        if request.method == 'POST':
            form = PostForm(request.POST or None, files=request.FILES or None,
                            instance=post)
            if form.is_valid():
                form.save()
                return redirect('posts:post_detail', pk=pk)
        else:
            form = PostForm(files=request.FILES or None, instance=post)
        context = {'form': form, 'is_edit': True}
        return render(request, 'posts/create_post.html', context)
    return redirect('posts:post_detail', pk=pk)


@login_required
def add_comment(request, pk):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=pk)
        comment.save()
    return redirect('posts:post_detail', pk=pk)


@login_required
def follow_index(request):
    following_list = get_following_list(request.user)
    post_list = Post.objects.filter(author__in=following_list)
    context = {'title': 'Подписки',
               'page_obj': add_paginator(request, post_list), }
    return render(request, 'posts/index.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        following_list = get_following_list(request.user)
        if author not in following_list:
            Follow.objects.create(user=request.user,
                                  author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        following_list = get_following_list(request.user)
        if author in following_list:
            delete = Follow.objects.get(user=request.user,
                                        author=author)
            delete.delete()
    return redirect('posts:profile', username=username)
