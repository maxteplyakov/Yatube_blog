from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {'group': group, 'page': page, 'paginator': paginator}
    )


@login_required()
def new_post(request):
    if request.method != 'POST':
        form = PostForm()
        form_header = 'Создать пост'
        button_text = 'Опубликовать'
        return render(request, 'new_post.html', {
            'form': form,
            'form_header': form_header,
            'button_text': button_text,
        })
    form = PostForm(request.POST, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('index')
    return render(request, 'new_post.html', {'form': form})


def profile(request, username):
    cur_author = get_object_or_404(User, username=username)
    post_list = cur_author.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = cur_author.following.filter(user__id=request.user.id).exists()
    followers = cur_author.following.count()
    follows = cur_author.follower.count()
    return render(
        request,
        'profile.html',
        {
            'page': page,
            'paginator': paginator,
            'cur_author': cur_author,
            'following': following,
            'followers': followers,
            'follows': follows,
        }
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST)
    comments = Comment.objects.filter(post=post)
    cur_author = get_object_or_404(User, username=username)
    post_amnt = cur_author.posts.count()
    return render(request, 'post.html', {
        'post': post,
        'cur_author': cur_author,
        'post_amnt': post_amnt,
        'form': form,
        'comments': comments,
    })


@login_required()
def post_edit(request, username, post_id):
    instance = get_object_or_404(Post, id=post_id)
    if request.user.username != username:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None, instance=instance)
    form_header = 'Редактировать пост'
    button_text = 'Сохранить'
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'new_post.html', {
        'form': form,
        'post': Post.objects.get(id=post_id),
        'form_header': form_header,
        'button_text': button_text,
    })

@login_required()
def add_comment(request, username, post_id):
    if request.method != 'POST':
        return redirect('post', username=username, post_id=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = Post.objects.get(id=post_id)
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'follow.html',
        {'page': page, 'paginator': paginator}
    )
    return render(request, "follow.html", {...})

@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('profile', username=username)

@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('profile', username=username)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)