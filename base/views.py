from django.shortcuts import render, redirect
from django.db.models import Q
from django.http import HttpResponse
from django.contrib.auth.models import User
from .models import Room, Topic, Message, RoomInvitation, RoomMembership
from .forms import RoomForm, UserForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username OR Password does not exist')
    context = {'page' : page}
    return render(request, 'base/login_register.html', context)
def logoutUser(request):
    logout(request)
    return redirect('home')


def registerPage(request):
    page = 'register'

    form = UserCreationForm()
    context = {'form' : form}

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occured')
    return render(request, 'base/login_register.html', context)

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))[0:5]
    context = {'rooms' : rooms, 'topics': topics, 'room_count': room_count,
    'room_messages' : room_messages}
    return render(request, 'base/home.html', context)
def room(request, pk):
    try:
        room = Room.objects.get(id=pk)
        
        # Check if user has membership
        try:
            membership = RoomMembership.objects.get(user=request.user, room=room)
            is_member = membership.role in ['ADMIN', 'MEMBER']
        except RoomMembership.DoesNotExist:
            is_member = False
        
        # Allow access if user is member or room is public
        if is_member or not room.is_private:
            room_messages = room.message_set.all().order_by('created')
            participants = room.participants.all()
            
            if request.method == 'POST':
                message = Message.objects.create(
                    user=request.user,
                    room=room,
                    body=request.POST.get('body')
                )
                room.participants.add(request.user)
                return redirect('room', pk=room.id)
            
            context = {
                'room': room,
                'room_messages': room_messages,
                'participants': participants,
                'is_member': is_member
            }
            return render(request, 'base/room.html', context)
        else:
            return HttpResponseForbidden("You are not allowed to access this room!")
            
    except Room.DoesNotExist:
        return HttpResponseForbidden("Room does not exist!")

def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user' : user, 'rooms' : rooms, 'room_messages' : room_messages, 'topics' : topics}
    return render(request, 'base/profile.html', context)
@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        private_bool = False
        if request.POST.get('is_private') == 'on':
            private_bool = True
        room = Room.objects.create(
            host = request.user,
            topic = topic,
            name = request.POST.get('name'),
            description = request.POST.get('description'),
            is_private = private_bool
        )
        RoomMembership.objects.create(
            user = request.user,
            room = room,
            role = 'ADMIN'
        )
        return redirect('home')
    context = {'form' : form, 'topics' : topics }
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()
    if request.user != room.host:
        return HttpResponse('You are not allowed here!!')
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        if request.POST.get('is_private') == 'on':
            room.is_private = True
        else:
            room.is_private = False
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')
    context = {'form' : form, 'topics' : topics , 'room' : room }
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    context = {'obj' : room}
    if request.user != room.host:
        return HttpResponse('You are not allowed here!!')
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', context)

@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)
    context = {'obj' : message}
    if request.user != message.user:
        return HttpResponse('You are not allowed here!!')
    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'base/delete.html', context)
@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
    return render(request, 'base/update-user.html', {'form' : form})

def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    context = {'topics' : topics }
    return render(request, 'base/topics.html', context)

def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'base/activity.html', {'room_messages' : room_messages })
def roomCode(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by('created')
    participants = room.participants.all()
    context = {'room' : room, 'room_messages' : room_messages, 'participants' : participants}
    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)
    return render(request, 'base/room-code.html', context)

@login_required(login_url='login')
def invite_to_room(request, room_id):
    if request.method == 'POST':
        room = get_object_or_404(Room, id=room_id)
        
        try:
            membership = RoomMembership.objects.get(user=request.user, room=room)
            if membership.role not in ['ADMIN']:
                return HttpResponseForbidden("You don't have permission to invite users")
            
            email = request.POST.get('email')
            if not email:
                return HttpResponseBadRequest("Email is required")
            
            invitation = RoomInvitation.objects.create(
                room=room,
                email=email,
                created_by=request.user
            )
            
            invitation.send_invitation_email(request)
            
            return JsonResponse({
                'status': 'success',
                'message': f'Invitation sent to {email}'
            })
            
        except RoomMembership.DoesNotExist:
            return HttpResponseForbidden("You are not a member of this room")

def join_room(request, token):
    invitation = get_object_or_404(RoomInvitation, token=token)
    
    # Check if invitation is expired
    if invitation.expires_at < timezone.now():
        return HttpResponseBadRequest("This invitation has expired")
    
    # Check if invitation is already used
    if invitation.is_used:
        return HttpResponseBadRequest("This invitation has already been used")
    
    # Check if user is logged in
    if not request.user.is_authenticated:
        # Store invitation token in session and redirect to login
        request.session['pending_invitation'] = str(token)
        return redirect('login')
    
    # Check if user's email matches invitation email
    if request.user.email != invitation.email:
        return HttpResponseForbidden("This invitation was sent to a different email address")
    
    # Create room membership
    RoomMembership.objects.create(
        user=request.user,
        room=invitation.room,
        role='MEMBER'
    )
    # Mark invitation as used
    invitation.is_used = True
    invitation.save()
    
    return redirect('room', id=invitation.room.id)





