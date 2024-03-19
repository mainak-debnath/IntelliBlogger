import os
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from pytube import YouTube
from django.conf import settings
import assemblyai as aai
import google.generativeai as genai
from .models import BlogPost
import markdown
import nltk
from dotenv import load_dotenv


load_dotenv()

# Create your views here.

def home(request):
    return render(request, 'home.html')

@login_required
def index(request):
    return render(request, 'index.html')

@csrf_exempt
def generate_blog(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    try:
        data = json.loads(request.body)
        yt_link = data['link'] 
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid data sent'}, status=400)

    # get yt title
    title = yt_title(yt_link)

    # get transcript
    transcription = get_transcription(yt_link)
    if not transcription:
        return JsonResponse({'error': " Failed to get transcript"}, status=500)


    # use gemini to generate the blog
    blog_content = generate_blog_from_transcription(transcription)
    if not blog_content:
        return JsonResponse({'error': " Failed to generate blog article"}, status=500)


    # save blog to db
    new_blog_article = BlogPost.objects.create(
        user=request.user,
        youtube_title=title,
        youtube_link=yt_link,
        generated_content=blog_content,
    )
    new_blog_article.save()

    # return blog as a response
    return JsonResponse({'content': blog_content})
    
def yt_title(link):
    yt = YouTube(link)
    title = yt.title
    return title

def download_audio(link):
    yt = YouTube(link)
    video = yt.streams.filter(only_audio=True).first()
    out_file = video.download(output_path=settings.MEDIA_ROOT)
    base, ext = os.path.splitext(out_file)
    new_file = f'{base}.mp3'
    os.rename(out_file, new_file)
    return new_file

def get_transcription(link):
    audio_file = download_audio(link)
    API_Key = os.getenv("ASSEMBLY_API_KEY")
    aai.settings.api_key = API_Key
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)
    return transcript.text

def generate_blog_from_transcription(transcription):
    API_Key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=API_Key)
    prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but dont make it look like a youtube video, make it look like a proper blog article:\n\n{transcription}\n\nArticle:"
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return markdown.markdown(response.text)

def blog_list(request):
    blog_articles = BlogPost.objects.filter(user=request.user)
    return render(request, "all-blogs.html", {'blog_articles': blog_articles})

def blog_details(request, pk):
    blog_article_detail = BlogPost.objects.get(id=pk)
    sentences = nltk.sent_tokenize(blog_article_detail.generated_content)
    if request.user == blog_article_detail.user:
        initial_sentences = sentences[:3]  # Adjust the number of sentences as needed
        initial_content = ' '.join(initial_sentences)
        remaining_sentences = sentences[3:]  # Remaining sentences
        remaining_content = ' '.join(remaining_sentences)
        return render(request, 'blog-details.html', {
            'blog_article_detail': blog_article_detail,
            'truncated_content': initial_content,
            'remaining_content': remaining_content
        })
    else:
        return redirect('/')
    
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/index')
        else:
            error_message = "Invalid username or password"
            return render(request, 'login.html', {'error_message': error_message})
        
    return render(request, 'login.html')

def user_signup(request):
    if request.method == 'POST':
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']

        if password == repeatPassword:
            username = request.POST['username']
            email = request.POST['email']
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/index')
            except:
                error_message = 'Error creating account'
                return render(request, 'signup.html', {'error_message':error_message})
        else:
            error_message = 'Password do not match'
            return render(request, 'signup.html', {'error_message':error_message})

    return render(request, 'signup.html')
def user_logout(request):
    logout(request)
    return redirect('/')

def delete_blog(request, blog_id):
    if request.method == 'POST':
        try:
            blog_post = BlogPost.objects.get(pk=blog_id)
            new_blog_title = os.path.splitext(blog_post.youtube_title)[0]
            mp3_file = os.path.join(settings.MEDIA_ROOT, f"{new_blog_title}.mp3")
            print(mp3_file)
            if os.path.exists(mp3_file):
                os.remove(mp3_file)
            # Delete blog post from database
            blog_post.delete()
            return redirect('blog-list')
        except BlogPost.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Blog post does not exist'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})