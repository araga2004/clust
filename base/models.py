from django.db import models
import uuid
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from datetime import datetime, timedelta
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set.')
        if not username:
            raise ValueError('The Username field must be set.')

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)

class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=200, unique=True)
    email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']  # Required when creating a superuser

    objects = CustomUserManager()

    def __str__(self):
        return self.username

class Topic(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Room(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    participants = models.ManyToManyField(User, related_name='participants', blank=True)
    description = models.TextField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    is_private = models.BooleanField(default=False)

    class Meta:
        ordering = ['-updated', '-created']
        indexes = [
            models.Index(fields=['id']),
        ]
    
    def __str__(self):
        return self.name

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    body = models.TextField()
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.body[0:50]

class RoomInvitation(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = datetime.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def send_invitation_email(self, request):
        invitation_url = request.build_absolute_uri(
            reverse('join_room', args=[str(self.token)])
        )
        
        context = {
            'room_name': self.room.name,
            'invitation_url': invitation_url,
            'expiry_date': self.expires_at.strftime('%Y-%m-%d %H:%M'),
            'inviter_name': self.created_by.get_full_name() or self.created_by.username
        }
        
        html_message = render_to_string("invitation.html", context)
        plain_message = f"""
        You've been invited to join {self.room.name}!
        Click here to join: {invitation_url}
        This invitation expires on {self.expires_at.strftime('%Y-%m-%d %H:%M')}
        """
        
        send_mail(
            subject=f'Invitation to join {self.room.name}',
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            fail_silently=False,
        )

class RoomMembership(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('MEMBER', 'Member'),
        ('OUTSIDER', 'Outsider')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='OUTSIDER')
    joined_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='invites_sent'
    )

    class Meta:
        unique_together = ['user', 'room']

    def __str__(self):
        return f"{self.user.username} - {self.room.name} ({self.role})"

class CodeSnippets(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='snippets')
    version_number = models.IntegerField()
    is_full = models.BooleanField(default=False)
    code_diff = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('room', 'version_number')
        ordering = ['version_number']
        indexes = [
                models.Index(fields=['room', '-version_number']),
            ]
