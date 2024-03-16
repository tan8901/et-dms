from django import forms
from django.forms.widgets import DateInput, TextInput

import json
from .models import *


class FormSettings(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSettings, self).__init__(*args, **kwargs)
        # Here make some changes such as:
        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'


class CustomUserForm(FormSettings):
    email = forms.EmailField(required=True,widget=forms.EmailInput(attrs={'autocomplete': 'new-password'}))
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')])
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    address = forms.CharField(widget=forms.Textarea)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)
        
        
        if kwargs.get('instance'):
            instance = kwargs.get('instance').admin.__dict__
            self.fields['password'].required = False
            for field in CustomUserForm.Meta.fields:
                self.fields[field].initial = instance.get(field)
            if self.instance.pk is not None:
                self.fields['password'].widget.attrs['placeholder'] = "Fill this only if you wish to update password"

                

    def clean_email(self, *args, **kwargs):
        formEmail = self.cleaned_data['email'].lower()
        if self.instance.pk is None:  # Insert
            if CustomUser.objects.filter(email=formEmail).exists():
                raise forms.ValidationError(
                    "The given email is already registered")
        else:  # Update
            dbEmail = self.Meta.model.objects.get(
                id=self.instance.pk).admin.email.lower()
            if dbEmail != formEmail:  # There has been changes
                if CustomUser.objects.filter(email=formEmail).exists():
                    raise forms.ValidationError("The given email is already registered")

        return formEmail

    class Meta:
        fields = ['first_name', 'last_name', 'email', 'gender', 'address','password']


class StudentForm(CustomUserForm):
    subjects = forms.ModelMultipleChoiceField(queryset=Subject.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}))
    
    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            instance = kwargs.get('instance').admin.__dict__
            self.fields['subjects'].required = False
        subjects_choices = [
            (subject.id, f"{subject.name} - {subject.branch.name}")
            for subject in Subject.objects.all()
        ]
        self.fields['subjects'].choices = subjects_choices        

    class Meta(CustomUserForm.Meta):
        model = Student
        fields = ['rollno'] + CustomUserForm.Meta.fields + \
            ['branch', 'session','subjects']


class AdminForm(CustomUserForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),label="Update Password")
    def __init__(self, *args, **kwargs):
        super(AdminForm, self).__init__(*args, **kwargs)
        self.fields['address'].required = False
        


    class Meta(CustomUserForm.Meta):
        model = Admin
        fields = ['password','first_name', 'last_name', 'email', 'gender', 'address']
        


class StaffForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(StaffForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Staff
        fields = CustomUserForm.Meta.fields + \
            ['branch','is_class_teacher']


class BranchForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(BranchForm, self).__init__(*args, **kwargs)

    class Meta:
        fields = ['name']
        model = Branch


class SubjectForm(FormSettings):

    def __init__(self, *args, **kwargs):
        super(SubjectForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Subject
        fields = ['name', 'staff', 'branch','session']


class SessionForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(SessionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Session
        fields = '__all__'
        widgets = {
            'start_year': DateInput(attrs={'type': 'date'}),
            'end_year': DateInput(attrs={'type': 'date'}),
            'eight_weeks': DateInput(attrs={'type':'date'})
        }


class LeaveReportStaffForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeaveReportStaffForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeaveReportStaff
        fields = ['from_date','to_date', 'days','message']
        widgets = {
            'from_date': DateInput(attrs={'type': 'date'}),
            'to_date': DateInput(attrs={'type': 'date'}),
        }



class StudentEditForm(CustomUserForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),label="Update Password",initial="")
    def __init__(self, *args, **kwargs):
        super(StudentEditForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Student
        fields = ['password','first_name','last_name','email','gender','address']


class StaffEditForm(CustomUserForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),label="Update Password",)
    def __init__(self, *args, **kwargs):
        super(StaffEditForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Staff
        fields = ['password','first_name','last_name','email','gender','address','branch']


class EditResultForm(FormSettings):
    session_list = Session.objects.all()
    session_year = forms.ModelChoiceField(
        label="Semester", queryset=session_list, required=True)

    def __init__(self, *args, **kwargs):
        super(EditResultForm, self).__init__(*args, **kwargs)
    
    class Meta:
        model = StudentResult
        fields = ['session_year', 'subject', 'student', 'mid1', 'mid2', 'assg1', 'assg2']

class MarksReport(FormSettings):
    def __init__(self, *args, **kwargs):
        super(MarksReport,self).__init__(*args, **kwargs)
    
    class Meta:
        model=StudentResult
        fields = ['subject']

    