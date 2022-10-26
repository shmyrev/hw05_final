from django.views.decorators.cache import cache_page
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
# from django.core.cache import cache

from .models import Post, Group, Follow
from .forms import PostForm, CommentForm


User = get_user_model()

POST_NUMBERS = 10


def paginator_view(request, posts, number):
    paginator = Paginator(posts, number)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(20, key_prefix="index_page")
def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    page_obj = paginator_view(request, posts, POST_NUMBERS)
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


# Подписки на авторов
@login_required
def follow_index(request):
    template = 'posts/follow.html'
    user = request.user
    posts = Post.objects.filter(author__following__user=user)
    page_obj = paginator_view(request, posts, POST_NUMBERS)
    context = {'page_obj': page_obj}
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    user = request.user
    if user != author:
        Follow.objects.get_or_create(
            user=user,
            author=author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    # Отписка
    user = request.user
    author = get_object_or_404(User, username=username)
    get_object_or_404(Follow, user=user, author=author).delete()
    return redirect('posts:profile', username=username)
