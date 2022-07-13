from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow
from .utils import add_paginator


def index(request):
    post_list = Post.objects.all()
    context = {'page_obj': add_paginator(request, post_list), }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = {'group': group,
               'page_obj': add_paginator(request, post_list), }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_list = author.posts.all()
    context = {'author': author,
               'count': posts_list.count(),
               'page_obj': add_paginator(request, posts_list), }
    if request.user.is_authenticated:
        if request.user.follower.filter(author=author).exists():
            context['following'] = True
    return render(request, 'posts/profile.html', context)


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all()
    comment_form = CommentForm(request.POST or None)
    context = {'post': post,
               'form': comment_form,
               'comments': comments,
               'count': post.author.posts.count(), }
    return render(request, 'posts/post_detail.html', context)


@login_required
def create_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if request.user == post.author:
        if request.method == 'POST':
            if form.is_valid():
                form.save()
                return redirect('posts:post_detail', pk=pk)
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
    post_list = Post.objects.filter(author__following__user=request.user)
    context = {'page_obj': add_paginator(request, post_list), }
    return render(request, 'posts/index.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        if not Follow.objects.filter(
                user=request.user, author=author).exists():
            Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow_record = Follow.objects.filter(user=request.user, author=author)
    if follow_record.exists():
        follow_record.delete()
    return redirect('posts:profile', username=username)
