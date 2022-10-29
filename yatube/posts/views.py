from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow
from .utils import paginate


@cache_page(60 * 15)
def index(request):
    page_index = paginate(Post.objects.all(), request)
    form = PostForm()
    return render(request, 'posts/index.html',
                  {'page_obj': page_index, 'form': form})


@cache_page(60 * 15)
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.selected_posts.select_related('author')
    page_group_posts = paginate(posts, request)
    form = PostForm()
    context = {
        'group': group,
        'page_obj': page_group_posts,
        'form': form,
    }
    return render(request, 'posts/group_list.html', context)


@cache_page(60 * 15)
def profile(request, username):
    author = get_object_or_404(User, username=username)
    user_post = author.posts.select_related('author')
    post_count = user_post.count()
    page_profile = paginate(user_post, request)
    form = PostForm()
    context = {
        'author': author,
        'post_count': post_count,
        'page_obj': page_profile,
        'form': form,
    }
    return render(request, 'posts/profile.html', context)


@cache_page(60 * 15)
def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    count = post.author.posts.count()
    form = CommentForm(request.POST or None)
    posts_comment = Post.objects.select_related('comments')
    form_ = PostForm()
    context = {
        'post': post,
        'count': count,
        'form': form,
        'posts_comment': posts_comment,
        'form_': form_,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if request.method == 'POST':
        if not form.is_valid():
            return render(request, 'posts/create_post.html', {'form': form})
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'post': post,
        'is_edit': True
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


@login_required
def follow_index(request):
    following_author = Follow.objects.filter(
        user=request.user).values('author')
    post = Post.objects.filter(author=following_author)
    page_obj = paginate(request, post)
    context = {
        'page_obj': page_obj,
        'following_author': following_author
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    unfollow = get_object_or_404(
        Follow,
        user=request.user,
        username=username)
    if Follow.objects.filter(user=request.user, author=unfollow).exists():
        Follow.objects.filter(user=request.user, author=unfollow).delete()
        return redirect('posts:profile', username)
