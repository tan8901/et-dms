import json
import requests
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponse, HttpResponseRedirect,
                              get_object_or_404, redirect, render)
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView
from django.db.models import Q
import re

from .forms import *
from .models import *

rnopat = r"[0-9]{2}B81A[0-9]{2}[0-9a-zA-Z]{2}"
emailpat = r"[a-zA-Z0-9.]+@gmail.com"

def admin_home(request):
    total_staff = Staff.objects.all().count()
    total_students = Student.objects.all().count()
    subjects = Subject.objects.filter(~Q(name__startswith='Mentoring')) if Subject.objects.filter(~Q(name__startswith='Mentoring')).exists() else Subject.objects.all()
    total_subject = subjects.count()
    total_branch = Branch.objects.all().count()
    attendance_list = Attendance.objects.filter(subject__in=subjects)
    total_attendance = attendance_list.count()
    attendance_list = []
    subject_list = []
    for subject in subjects:
        attendance_count = Attendance.objects.filter(subject=subject).count()
        subject_list.append(subject.name[:7])
        attendance_list.append(attendance_count)

    # Total Subjects and students in Each Branch
    branch_all = Branch.objects.all()
    branch_name_list = []
    subject_count_list = []
    student_count_list_in_branch = []

    for branch in branch_all:
        subjects = Subject.objects.filter(branch_id=branch.id).count()
        students = Student.objects.filter(branch_id=branch.id).count()
        branch_name_list.append(branch.name)
        subject_count_list.append(subjects)
        student_count_list_in_branch.append(students)
    
    subject_all = Subject.objects.all()
    subject_list = []
    student_count_list_in_subject = []
    for subject in subject_all:
        branch = Branch.objects.get(id=subject.branch.id)
        student_count = Student.objects.filter(branch_id=branch.id).count()
        subject_list.append(subject.name)
        student_count_list_in_subject.append(student_count)


    # For Students
    student_attendance_present_list=[]
    student_attendance_leave_list=[]
    student_name_list=[]

    students = Student.objects.all()
    for student in students:
        
        attendance = AttendanceReport.objects.filter(student_id=student.id, status=True).count()
        absent = AttendanceReport.objects.filter(student_id=student.id, status=False).count()
        student_attendance_present_list.append(attendance)
        student_name_list.append(student.admin.first_name)
    leaves = LeaveReportStaff.objects.filter(status=0).count()
    context = {
        'page_title': "Administrative Dashboard",
        'total_students': total_students,
        'total_staff': total_staff,
        'total_branch': total_branch,
        'total_subject': total_subject,
        'subject_list': subject_list,
        'attendance_list': attendance_list,
        'student_attendance_present_list': student_attendance_present_list,
        
        "student_name_list": student_name_list,
        "student_count_list_in_subject": student_count_list_in_subject,
        "student_count_list_in_branch": student_count_list_in_branch,
        "branch_name_list": branch_name_list,
        "leaves": leaves,

    }
    return render(request, 'hod_template/home_content.html', context)


def add_staff(request):
    form = StaffForm(request.POST or None, request.FILES or None)
    context = {'form': form, 'page_title': 'Add Staff'}
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password')
            branch = form.cleaned_data.get('branch')
            is_class_teacher = form.cleaned_data.get('is_class_teacher')
            fs = FileSystemStorage()
            try:
                if re.fullmatch(emailpat,email) == None:
                    messages.error(request,"Email is Invalid. Please format it as xyz@gmail.com")
                    return redirect(reverse('add_staff'))
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=2, first_name=first_name, last_name=last_name)
                user.gender = gender
                user.address = address
                user.staff.branch = branch
                user.staff.is_class_teacher = is_class_teacher
                user.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_staff'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Please fulfil all requirements")

    return render(request, 'hod_template/add_staff_template.html', context)


def add_student(request):
    student_form = StudentForm(request.POST or None, request.FILES or None)
    students = Student.objects.all()
    context = {
        'form': student_form, 
        'page_title': 'Add Student'}
    if request.method == 'POST':
        if student_form.is_valid():
            first_name = student_form.cleaned_data.get('first_name')
            last_name = student_form.cleaned_data.get('last_name')
            rollno = student_form.cleaned_data.get('rollno')
            address = student_form.cleaned_data.get('address')
            email = student_form.cleaned_data.get('email')
            gender = student_form.cleaned_data.get('gender')
            password = student_form.cleaned_data.get('password')
            branch = student_form.cleaned_data.get('branch')
            session = student_form.cleaned_data.get('session')
            subjects = student_form.cleaned_data.get('subjects')
            try:
                
                if re.fullmatch(rnopat,rollno)== None:
                    messages.error(request,"Roll Number is Invalid")
                    return redirect(reverse('add_student'))
                for s in students:
                    if rollno == s.rollno:
                        messages.error(request,"Roll Number is already Taken")
                        return redirect(reverse('add_student'))
                if re.fullmatch(emailpat,email) == None:
                    messages.error(request,"Email is Invalid. Please format it as xyz@gmail.com")
                    return redirect(reverse('add_student'))
                for s in subjects:
                    if s.branch != branch:
                        messages.error(request,"Please select Subject from Student's Branch")
                        return redirect(reverse('add_student'))
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=3, first_name=first_name, last_name=last_name)
                user.gender = gender
                user.address = address
                user.student.session = session
                user.student.branch = branch
                user.student.rollno = rollno
                user.save()
                messages.success(request, "Successfully Added")
                for s in subjects:
                    s.students.add(user.student)
                    s.save()
                return redirect(reverse('add_student'))
            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))
        else:
            messages.error(request, "Could Not Add: ")
    return render(request, 'hod_template/add_student_template.html', context)


def add_branch(request):
    form = BranchForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Branch'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            existing_branches = Branch.objects.all()
            print(existing_branches)
            try:
                branch = Branch()
                branch.name = name
                for e in existing_branches:
                    if branch.name == e.name:
                        messages.error(request,"Branch Already Exists")
                        return redirect(reverse('add_branch'))
                branch.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_branch'))
            except:
                messages.error(request, "Could Not Add")
        else:
            messages.error(request, "Could Not Add")
    return render(request, 'hod_template/add_branch_template.html', context)


def add_subject(request):
    form = SubjectForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Subject'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            branch = form.cleaned_data.get('branch')
            staff = form.cleaned_data.get('staff')
            existing_subjects = Subject.objects.all()
            try:
                subject = Subject()
                subject.name = name
                subject.staff = staff
                subject.branch = branch
                for s in existing_subjects:
                    if s.name==subject.name and s.staff==subject.staff:
                        messages.error(request,"This Subject is already being taught by this Staff Member")
                        return redirect(reverse('add_subject'))
                subject.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_subject'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'hod_template/add_subject_template.html', context)


def manage_staff(request):
    allStaff = CustomUser.objects.filter(user_type=2)
    context = {
        'allStaff': allStaff,
        'page_title': 'Manage Staff'
    }
    return render(request, "hod_template/manage_staff.html", context)


def manage_student(request):
    students = CustomUser.objects.filter(user_type=3)
    context = {
        'students': students,
        'page_title': 'Manage Students'
    }
    return render(request, "hod_template/manage_student.html", context)


def manage_branch(request):
    branches = Branch.objects.all()
    context = {
        'branches': branches,
        'page_title': 'Manage Branches'
    }
    return render(request, "hod_template/manage_branch.html", context)


def manage_subject(request):
    subjects = Subject.objects.filter(~Q(name__startswith='Mentoring'))
    classes = Subject.objects.filter(Q(name__startswith='Mentoring')) if Subject.objects.filter(~Q(name__startswith='Mentoring')).exists() else None
    context = {
        'subjects': subjects,
        'classes':classes,
        'page_title': 'Manage Subjects'
    }
    return render(request, "hod_template/manage_subject.html", context)


def edit_staff(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id)
    form = StaffForm(request.POST or None, instance=staff)
    context = {
        'form': form,
        'staff_id': staff_id,
        'page_title': 'Edit Staff'
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            branch = form.cleaned_data.get('branch')
            try:
                if re.fullmatch(emailpat,email) == None:
                    messages.error(request,"Email is Invalid. Please format it as xyz@gmail.com")
                    return redirect(reverse('edit_staff'))
                user = CustomUser.objects.get(id=staff.admin.id)
                user.username = username
                user.email = email
                if password != None:
                    user.set_password(password)
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                user.address = address
                staff.branch = branch
                user.save()
                staff.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_staff', args=[staff_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Please fil form properly")
    else:
        if staff_id==7:
            user = CustomUser.objects.get(id=staff_id+1)
        else:
            user = CustomUser.objects.get(id=staff_id)
        staff = Staff.objects.get(id=user.id)
        return render(request, "hod_template/edit_staff_template.html", context)


def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    form = StudentForm(request.POST or None, instance=student)
    context = {
        'form': form,
        'student_id': student_id,
        'page_title': 'Edit Student'
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            branch = form.cleaned_data.get('branch')
            session = form.cleaned_data.get('session')
            subjects = form.cleaned_data.get('subjects')

            try:
                if re.fullmatch(emailpat,email) == None:
                    messages.error(request,"Email is Invalid. Please format it as xyz@gmail.com")
                    return redirect(reverse('edit_student'))
                user = CustomUser.objects.get(id=student.admin.id)
                user.username = username
                user.email = email
                if password != None:
                    user.set_password(password)
                user.first_name = first_name
                user.last_name = last_name
                student.session = session
                user.gender = gender
                user.address = address
                student.branch = branch
                for s in subjects:
                    s.students.add(user.student)
                    s.save()
                user.save()
                student.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_student', args=[student_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Please Fill Form Properly!")
    else:
        return render(request, "hod_template/edit_student_template.html", context)


def edit_branch(request, branch_id):
    instance = get_object_or_404(Branch, id=branch_id)
    form = BranchForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'branch_id': branch_id,
        'page_title': 'Edit Branch'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            try:
                branch = Branch.objects.get(id=branch_id)
                branch.name = name
                branch.save()
                messages.success(request, "Successfully Updated")
            except:
                messages.error(request, "Could Not Update")
        else:
            messages.error(request, "Could Not Update")

    return render(request, 'hod_template/edit_branch_template.html', context)


def edit_subject(request, subject_id):
    instance = get_object_or_404(Subject, id=subject_id)
    form = SubjectForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'subject_id': subject_id,
        'page_title': 'Edit Subject'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            branch = form.cleaned_data.get('branch')
            staff = form.cleaned_data.get('staff')
            try:
                subject = Subject.objects.get(id=subject_id)
                subject.name = name
                subject.staff = staff
                subject.branch = branch
                subject.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_subject', args=[subject_id]))
            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
    return render(request, 'hod_template/edit_subject_template.html', context)


def add_session(request):
    form = SessionForm(request.POST or None)
    sessions = Session.objects.all()
    context = {'form': form, 'page_title': 'Add Semester'}
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            start_year = form.cleaned_data.get('start_year')
            end_year = form.cleaned_data.get('end_year')
            try:
                
                duration = (end_year.year - start_year.year) * 12 + (end_year.month - start_year.month)
                if duration != 4:
                    messages.error(request,"Semester should be at least 4 months in duration")
                    return redirect(reverse('add_session'))
                for s in sessions:
                    if (start_year==s.start_year and end_year==s.end_year) or name==s.name:
                        messages.error(request,"Semester already exists... please Update in Manage Semester")
                        return redirect(reverse('add_session'))
                session = Session()
                session.name=name
                session.start_year=start_year
                session.end_year=end_year
                session.save()
                messages.success(request, "Semester Created")
                return redirect(reverse('add_session'))
            except Exception as e:
                messages.error(request, 'Could Not Add ' + str(e))
        else:
            messages.error(request, 'Fill Form Properly ')
    return render(request, "hod_template/add_session_template.html", context)


def manage_session(request):
    sessions = Session.objects.all().order_by('name')
    context = {'sessions': sessions, 'page_title': 'Manage Semesters'}
    return render(request, "hod_template/manage_session.html", context)


def edit_session(request, session_id):
    instance = get_object_or_404(Session, id=session_id)
    form = SessionForm(request.POST or None, instance=instance)
    context = {'form': form, 'session_id': session_id,
               'page_title': 'Edit Semester'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Semester Updated")
                return redirect(reverse('edit_session', args=[session_id]))
            except Exception as e:
                messages.error(
                    request, "Session Could Not Be Updated " + str(e))
                return render(request, "hod_template/edit_session_template.html", context)
        else:
            messages.error(request, "Invalid Form Submitted ")
            return render(request, "hod_template/edit_session_template.html", context)

    else:
        return render(request, "hod_template/edit_session_template.html", context)


@csrf_exempt
def check_email_availability(request):
    email = request.POST.get("email")
    try:
        user = CustomUser.objects.filter(email=email).exists()
        if user:
            return HttpResponse(True)
        return HttpResponse(False)
    except Exception as e:
        return HttpResponse(False)



@csrf_exempt
def view_staff_leave(request):
    if request.method != 'POST':
        from django.utils import timezone
        allLeave = LeaveReportStaff.objects.all().order_by('from_date')
        current_date = timezone.now().date()
        pending = LeaveReportStaff.objects.filter(status=0)
        for leave in pending:
            if current_date > leave.from_date:
                leave.status=-1
                leave.save()
        context = {
            'allLeave': allLeave,
            'current_date':current_date,
            'page_title': 'Leave Applications From Staff'
        }
        return render(request, "hod_template/staff_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            
            leave = get_object_or_404(LeaveReportStaff, id=id)
            
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return False



def admin_view_attendance(request):
    students = Student.objects.all().order_by('rollno')
    sessions = Session.objects.all().order_by('name')
    branches = Branch.objects.all()
    attendance = TotalAttendance.objects.all()
    #att_report = AttendanceReport.objects.all().order_by('student__rollno')
    context = {
        'students': students,
        'sessions': sessions,
        'attendance': attendance,
        'branches': branches,
        'page_title': 'Attendance Report'
    }

    return render(request, "hod_template/admin_view_attendance.html", context)


def admin_view_results(request):
    students = Student.objects.all().order_by('rollno')
    sessions = Session.objects.all()
    branches = Branch.objects.all()
    results = StudentResult.objects.all()
    subjects = Subject.objects.filter(~Q(name__startswith='Mentoring'))
    context = {
        'students': students,
        'sessions': sessions,
        'results': results,
        'branches': branches,
        'subjects': subjects,
        'page_title': 'Results Report'
    }

    return render(request, "hod_template/admin_view_results.html", context)


@csrf_exempt
def get_admin_attendance(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        attendance = get_object_or_404(
            Attendance, id=attendance_date_id, session=session)
        attendance_reports = AttendanceReport.objects.filter(
            attendance=attendance)
        json_data = []
        for report in attendance_reports:
            data = {
                "status":  str(report.status),
                "name": str(report.student)
            }
            json_data.append(data)
        return JsonResponse(json.dumps(json_data), safe=False)
    except Exception as e:
        return None


def admin_view_profile(request):
    admin = get_object_or_404(Admin, admin=request.user)
    form = AdminForm(request.POST or None, request.FILES or None,
                     instance=admin)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                custom_user = admin.admin
                if password != None:
                    custom_user.set_password(password)
                custom_user.first_name = first_name
                custom_user.last_name = last_name
                custom_user.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('admin_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
    return render(request, "hod_template/admin_view_profile.html", context)


def admin_notify_staff(request):
    staff = CustomUser.objects.filter(user_type=2)
    context = {
        'page_title': "Send Notifications To Staff",
        'allStaff': staff
    }
    return render(request, "hod_template/staff_notification.html", context)




@csrf_exempt
def send_staff_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    staff = get_object_or_404(Staff, admin_id=id)
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "Student Management System",
                'body': message,
                'click_action': reverse('staff_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': staff.admin.fcm_token
        }
        headers = {'Authorization':
                   'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
                   'Content-Type': 'application/json'}
        data = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationStaff(staff=staff, message=message)
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def delete_staff(request, staff_id):
    staff = get_object_or_404(CustomUser, staff__id=staff_id)
    staff.delete()
    messages.success(request, "Staff deleted successfully!")
    return redirect(reverse('manage_staff'))


def delete_student(request, student_id):
    student = get_object_or_404(CustomUser, student__id=student_id)
    student.delete()
    messages.success(request, "Student deleted successfully!")
    return redirect(reverse('manage_student'))


def delete_branch(request, branch_id):
    branch = get_object_or_404(Branch, id=branch_id)
    try:
        branch.delete()
        messages.success(request, "Branch deleted successfully!")
    except Exception:
        messages.error(
            request, "Sorry, some students are assigned to this branch already. Kindly change the affected student branch and try again")
    return redirect(reverse('manage_branch'))


def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    subject.delete()
    messages.success(request, "Subject deleted successfully!")
    return redirect(reverse('manage_subject'))


def delete_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    try:
        session.delete()
        messages.success(request, "Semester deleted successfully!")
    except Exception:
        messages.error(
            request, "There are students assigned to this semester. Please move them to another semester.")
    return redirect(reverse('manage_session'))

def admin_report(request):
    subjects = Subject.objects.all()
    students = Student.objects.all().order_by('rollno')
    attendances = TotalAttendance.objects.all()
    context = {
        'students' : students,
        'subjects' : subjects,
        'attendances': attendances,
        'page_title' : 'Attendance Report'
    }
    return render(request, 'staff_template/staff_attendance_report.html', context)

@csrf_exempt
def get_filtered_subjects(request, branch_id):
    session_id = request.GET.get('session_id')
    subjects = Subject.objects.filter(branch_id=branch_id,session_id=session_id)
    data = [{'id': subject.id, 'name': subject.name} for subject in subjects]
    return JsonResponse({'subjects': data})

