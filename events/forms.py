from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Event, EventRegistration, Skill


class UserRegisterForm(UserCreationForm):
    """Форма регистрации с выбором роли"""
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(max_length=30, required=True, label='Имя')
    last_name = forms.CharField(max_length=30, required=True, label='Фамилия')
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        label='Я хочу',
        widget=forms.RadioSelect
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tailwind стили для полей
        for field_name, field in self.fields.items():
            if field_name != 'role':
                field.widget.attrs['class'] = 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition-all outline-none'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Обновляем роль профиля
            user.profile.role = self.cleaned_data['role']
            user.profile.save()
        return user


class UserProfileForm(forms.ModelForm):
    """Форма редактирования профиля"""
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
        
        # Tailwind стили
        for field_name, field in self.fields.items():
            if field_name not in ['skills', 'avatar']:
                field.widget.attrs['class'] = 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition-all outline-none'
        
        # Стили для поля загрузки аватара
        if 'avatar' in self.fields:
            self.fields['avatar'].widget.attrs['class'] = 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition-all outline-none file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-forest-50 file:text-forest-700 hover:file:bg-forest-100'
    
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
    """Форма создания/редактирования события"""
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'time', 'location', 'city', 
                  'required_skills', 'max_volunteers', 'image_url']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 5}),
            'required_skills': forms.CheckboxSelectMultiple(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['required_skills']:
                field.widget.attrs['class'] = 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition-all outline-none'


class EventRegistrationForm(forms.ModelForm):
    """Форма заявки на событие"""
    class Meta:
        model = EventRegistration
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Расскажите немного о себе и почему хотите участвовать...',
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition-all outline-none'
            }),
        }


class VolunteerSearchForm(forms.Form):
    """Форма поиска волонтёров"""
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        label='Навыки'
    )
    city = forms.CharField(max_length=100, required=False, label='Город')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['city'].widget.attrs['class'] = 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition-all outline-none'
        self.fields['city'].widget.attrs['placeholder'] = 'Введите город...'

