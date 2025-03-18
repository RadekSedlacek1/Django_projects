from django.shortcuts import render, redirect
from .forms import RegisterForm, PostForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import Post

# Create your views here.

@login_required(login_url="/login")     # if not login, redirect to: /login
def index(request):
    posts = Post.objects.all()

    if request.method == "POST":
        post_id = request.POST.get("post-id")
        post = Post.objects.filter(id=post_id).first()
        if post and post.author == request.user:
            post.delete()
        print(post_id)

    return render(request, 'main/index.html', {"posts":posts})


@login_required(login_url="/login")
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False) # Ještě neodesílej data do databáze
            post.author = request.user
            post.save() # defaultně je commit = True - nemusím to psát a odešlou se data do databáze
            return redirect ('/index')
    else:
        form = PostForm()
    return render(request, 'main/create_post.html', {"form": form})

def sign_up(request):
    if request.method =='POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/index')
    else:
        form = RegisterForm()

    return render(request, 'registration/sign_up.html', {"form": form})


