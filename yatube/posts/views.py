from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.cache import cache

from .models import Post, Group
from .forms import PostForm, CommentForm


User = get_user_model()

POST_NUMBERS = 10


def paginator_view(request, posts, number):
    paginator = Paginator(posts, number)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    template = 'posts/index.html'
    page_cache = cache.get('index_page')
    if not page_cache:
        posts = Post.objects.all()
        page_obj = paginator_view(request, posts, POST_NUMBERS)
        cache.set('index_page', page_cache, timeout=20)
    return render(request, template, {'page_obj': page_obj})


def group_posts(request, group_slug):
    group = get_object_or_404(Group, slug=group_slug)
    template = 'posts/group_list.html'
    posts = group.posts.all()
    page_obj = paginator_view(request, posts, POST_NUMBERS)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = paginator_view(request, posts, POST_NUMBERS)
    context = {
        'author': author,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.select_related("author", "post").all()
    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required()
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if request.method == "POST":
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required()
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if request.user != post.author:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)

    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)
