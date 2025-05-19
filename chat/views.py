import openai
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import ChatMessage
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.core import serializers
from django.http import JsonResponse

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