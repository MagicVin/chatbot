import openai
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import ChatMessage
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User
import re
from django.contrib import messages

@login_required
def index(request):
    all_messages = ChatMessage.objects.filter(user=request.user).order_by("-timestamp")
    paginator = Paginator(all_messages, 10) # 10 messages per page

    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'index.html', {'history': page_obj.object_list, 'page_obj': page_obj})


@csrf_exempt
@login_required
def chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message')

        # ChatGPT call
        try:
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": user_message}],
            )
            reply = completion.choices[0].message.content
        except Exception as e:
            reply = f"Error: {str(e)}"

        # Save to DB
        ChatMessage.objects.create(user=request.user, message=user_message, response=reply)

        return JsonResponse({'reply': reply})

@csrf_exempt
@login_required
def chat_view(request):
    messages = request.session.get("chat_messages", [])
    if request.method == 'POST':
        user_input = request.POST.get("message")
        messages.append({"role": "user", "content": user_input})
        # ChatGPT call
        try:
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": user_input}],
            )
            reply = completion.choices[0].message.content
            messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            messages.append({"role": "assistant", "content": f"[Error: {e}]"})

        request.session['chat_messages'] = messages
    return render(request, "chat.html", {"messages": messages})

@csrf_exempt
@require_POST
@login_required
def clear_chat(request):
    ChatMessage.objects.filter(user=request.user).delete()
    return JsonResponse({'status': 'ok'})

@login_required
def chat_history(request):
    page_number = request.GET.get("page", 1)
    messages = ChatMessage.objects.filter(user=request.user).order_by('-timestamp')
    paginator = Paginator(messages, 10)
    page_obj = paginator.get_page(page_number)

    data = [
        {"message": msg.message, "response": msg.response}
        for msg in page_obj.object_list
    ]
    return JsonResponse({
        "history": data,
        "has_next": page_obj.has_next(),
        "has_previous": page_obj.has_previous(),
        "num_pages": paginator.num_pages,
        "current_page": page_obj.number
    })

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, { user.username }!")
            return redirect('index')
        else:
            return render(request, 'login.html', {'form': {'errors': True}})

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    # Clear messages manually after logout
    list(messages.get_messages(request))
    return render(request, 'logout.html')

def signup_view(request):

    def is_strong_password(password):
        return (len(password) >= 8
            and re.search(r'[a-z]', password)
            and re.search(r'[A-Z]', password)
            and re.search(r'[0-9]', password)
            # and re.search(r'[!@#$%^&*()-=,.?":{}<>]')
        )

    if request.method == 'POST':
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        email = request.POST['email']

        if password1 != password2:
            return render(request, 'signup.html', {"error": "Passwords do not match."})

        if not is_strong_password(password1):
            return render(request, 'signup.html', {"error": """Password must be at least 8
            characters and include uppercase, lowercase, and a number"""})

        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {"error": "Username already taken."})

        user = User.objects.create_user(username=username, password=password1, email=email)
        messages.success(request, "Welcome, your account was created.")
        login(request, user)
        return redirect('index')
    return render(request, 'signup.html')