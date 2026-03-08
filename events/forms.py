from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import (
    ChatChannel,
    ChatMessage,
    Event,
    EventRegistration,
    Skill,
    UserProfile,
)

INPUT_CLASS = 'input'
FILE_INPUT_CLASS = 'input file-input'


def _set_class(field, css_class):
    field.widget.attrs['class'] = css_class


def _set_class_for_fields(fields, css_class, exclude=()):
    excluded = set(exclude)
    for field_name, field in fields.items():
        if field_name in excluded:
            continue
        _set_class(field, css_class)


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(max_length=30, required=True, label='Имя')
    last_name = forms.CharField(max_length=30, required=True, label='Фамилия')
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        label='Я хочу',
        widget=forms.RadioSelect,
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _set_class_for_fields(self.fields, INPUT_CLASS, exclude=('role',))

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            user.profile.role = self.cleaned_data['role']
            user.profile.save()
        return user


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, label='Имя')
    last_name = forms.CharField(max_length=30, required=True, label='Фамилия')
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = UserProfile
        fields = ['bio', 'phone', 'city', 'skills', 'avatar', 'avatar_url']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'skills': forms.CheckboxSelectMultiple(),
            'avatar': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

        _set_class_for_fields(self.fields, INPUT_CLASS, exclude=('skills', 'avatar'))

        if 'avatar' in self.fields:
            _set_class(self.fields['avatar'], FILE_INPUT_CLASS)

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
        if commit:
            profile.save()
            self.save_m2m()
        return profile


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'event_type',
            'date',
            'time',
            'location',
            'city',
            'required_skills',
            'max_volunteers',
            'xp_reward',
            'image_url',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 5}),
            'required_skills': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _set_class_for_fields(self.fields, INPUT_CLASS, exclude=('required_skills',))


class EventListFilterForm(forms.Form):
    STATUS_CHOICES = (
        ('', 'Р’СЃРµ'),
        ('open', 'РћС‚РєСЂС‹С‚ РЅР°Р±РѕСЂ'),
        ('full', 'РњРµСЃС‚ РЅРµС‚'),
        ('mine', 'РњРѕРё СЃРѕР±С‹С‚РёСЏ'),
    )

    skill = forms.ModelChoiceField(queryset=Skill.objects.all(), required=False)
    city = forms.CharField(max_length=100, required=False)
    search = forms.CharField(max_length=200, required=False)
    event_type = forms.ChoiceField(required=False, choices=(('', 'Р’СЃРµ С‚РёРїС‹'), *Event.TYPE_CHOICES))
    status = forms.ChoiceField(required=False, choices=STATUS_CHOICES)
    date_from = forms.DateField(required=False)
    date_to = forms.DateField(required=False)
    participant = forms.CharField(max_length=150, required=False)

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError('Р”Р°С‚Р° "РѕС‚" РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїРѕР·Р¶Рµ РґР°С‚С‹ "РґРѕ".')
        return cleaned_data


class EventRegistrationForm(forms.ModelForm):
    class Meta:
        model = EventRegistration
        fields = ['message']
        widgets = {
            'message': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': 'Расскажите немного о себе и почему хотите участвовать...',
                    'class': INPUT_CLASS,
                }
            ),
        }


class VolunteerSearchForm(forms.Form):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        label='Навыки',
    )
    city = forms.CharField(max_length=100, required=False, label='Город')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _set_class(self.fields['city'], INPUT_CLASS)
        self.fields['city'].widget.attrs['placeholder'] = 'Введите город...'


class ChatChannelForm(forms.ModelForm):
    class Meta:
        model = ChatChannel
        fields = ['name', 'topic']
        widgets = {
            'topic': forms.TextInput(attrs={'placeholder': 'Короткое описание канала'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _set_class_for_fields(self.fields, INPUT_CLASS)


class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': 'Введите сообщение...',
                    'class': INPUT_CLASS,
                }
            ),
        }
