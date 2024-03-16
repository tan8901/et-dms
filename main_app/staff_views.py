import json,math

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from datetime import date
from .forms import *
from .models import *


def staff_home(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    total_students=0
    for s in subjects:
        total_students += Subject.objects.get(id=s.id).students.count()
    total_leave = LeaveReportStaff.objects.filter(staff=staff,status=1).count()
    leaves_left = 16-total_leave
    if staff.is_class_teacher:
        total_subject = subjects.count()-1
    else:
        total_subject = subjects.count()
    attendance_list = Attendance.objects.filter(subject__in=subjects)
    total_attendance = attendance_list.count()
    attendance_list = []
    subject_list = []
    for subject in subjects:
        attendance_count = Attendance.objects.filter(subject=subject).count()
        subject_list.append(subject.name)
        attendance_list.append(attendance_count)
    context = {
        'page_title': 'Staff Panel - ' + str(staff.admin.last_name) +" "+ str(staff.admin.first_name),
        'total_students': total_students,
        'total_attendance': total_attendance,
        'total_leave': total_leave,
        'leave_history': LeaveReportStaff.objects.filter(staff=staff),
        'total_subject': total_subject,
        'subject_list': subject_list,
        'attendance_list': attendance_list,
        'leaves_left' : leaves_left
    }
    return render(request, 'staff_template/home_content.html', context)


def staff_take_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(Q(staff_id=staff.id) & ~Q(name__startswith='Mentoring'))
    context = {
        'subjects': subjects,
        'page_title': 'Take Attendance'
    }

    return render(request, 'staff_template/staff_take_attendance.html', context)

#WIP
def staff_attendance_report(request):
    staff = get_object_or_404(Staff,admin=request.user)
    subjects = Subject.objects.get(staff=staff,name__startswith='Mentoring')
    students = Subject.objects.get(id=subjects.id).students.all()
    attendances = TotalAttendance.objects.all()
    context = {
        'students' : students,
        'subjects' : subjects,
        'attendances': attendances,
        'page_title' : 'Attendance Report'
    }
    return render(request, 'staff_template/staff_attendance_report.html', context)

@csrf_exempt
def get_students(request):
    subject_id = request.POST.get('subject')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        students = Subject.objects.get(id=subject.id).students.filter(session=subject.session).order_by('rollno')
        student_data = []
        for student in students:
            data = {
                    "id": student.id,
                    "name": student.admin.last_name + " " + student.admin.first_name,
                    "rollno": student.rollno
                    }
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return e


@csrf_exempt
def save_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    subject_id = request.POST.get('subject')
    students = json.loads(student_data)
    try:
        
        subject = get_object_or_404(Subject, id=subject_id)

        attendance = Attendance(session=subject.session, subject=subject, date=date)
        attendance.save()

        for student_dict in students:
            student = get_object_or_404(Student, id=student_dict.get('id'))
            attendance_report = AttendanceReport(student=student, attendance=attendance, status=student_dict.get('status'))
            attendance_report.save()
            total_attendance(student)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None

    return HttpResponse("OK")

@csrf_exempt
def total_attendance(student):
    from dateutil.relativedelta import relativedelta

    #deleting previous records so that there's no prior entries
    if TotalAttendance.objects.filter(student=student).exists():
        TotalAttendance.objects.get(student=student).delete()
    
    #adding the attendance to the Total Attendance report... using GET method instead of POST 
    att = TotalAttendance(student=student)
    att.total_classes=AttendanceReport.objects.filter(student=student).count()
    att.total_present=AttendanceReport.objects.filter(student=student,status=True).count()
    eight_total=AttendanceReport.objects.filter(student=student,attendance__date__range=[student.session.start_year,student.session.eight_weeks]).count()
    eight_present=AttendanceReport.objects.filter(student=student,attendance__date__range=[student.session.start_year,student.session.eight_weeks],status=True).count()
    if att.total_classes == 0:
        att.present_percentage = 0
    else:
        att.present_percentage = math.floor((att.total_present/att.total_classes) * 100)
    if eight_total == 0:
        att.eight_present = 0
    else:
        att.eight_present = math.floor((eight_present/eight_total)*100)
    att.save()



@csrf_exempt
def staff_update_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(Q(staff_id=staff) & ~Q(name__startswith='Mentoring'))
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Update Attendance'
    }

    return render(request, 'staff_template/staff_update_attendance.html', context)


@csrf_exempt
def get_student_attendance(request):
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        date = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_data = AttendanceReport.objects.filter(attendance=date)
        student_data = []
        for attendance in attendance_data:
            data = {"id": attendance.student.admin.id,
                    "name": attendance.student.admin.last_name + " " + attendance.student.admin.first_name,
                    "status": attendance.status}
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e


@csrf_exempt
def update_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    students = json.loads(student_data)
    try:
        attendance = get_object_or_404(Attendance, id=date)

        for student_dict in students:
            student = get_object_or_404(Student, admin=student_dict.get('id'))
            attendance_report = get_object_or_404(AttendanceReport, student=student, attendance=attendance)
            attendance_report.status = student_dict.get('status')
            attendance_report.save()
    except Exception as e:
        return None

    return HttpResponse("OK")

def staff_apply_leave(request):
    form = LeaveReportStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    leaves_left = 16 - LeaveReportStaff.objects.filter(staff=staff,status=1).count()
    current_date = date.today().isoformat()
    context = {
        'form': form,
        'leaves_left':leaves_left,
        'current_date':current_date,
        'page_title': 'Apply for Leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            from_date = form.cleaned_data['from_date']
            to_date = form.cleaned_data['to_date']
            try:

                if from_date > to_date:
                    messages.error(request,"From Date cannot be later than To Date")
                    return redirect(reverse('staff_apply_leave'))
                
                
                
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(request, "Application for leave has been submitted for review")
                return redirect(reverse('staff_apply_leave'))
            except Exception:
                messages.error(request, "Could not apply!")
                import traceback
                traceback.print_exc()
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_apply_leave.html", context)




def staff_view_profile(request):
    staff = get_object_or_404(Staff, admin=request.user)
    form = StaffEditForm(request.POST or None, request.FILES or None,instance=staff)
    context = {'form': form, 'page_title': 'View/Update Profile'}
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                admin = staff.admin
                if password != None:
                    admin.set_password(password)
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                staff.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('staff_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
                return render(request, "staff_template/staff_view_profile.html", context)
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
            return render(request, "staff_template/staff_view_profile.html", context)

    return render(request, "staff_template/staff_view_profile.html", context)


@csrf_exempt
def staff_fcmtoken(request):
    token = request.POST.get('token')
    try:
        staff_user = get_object_or_404(CustomUser, id=request.user.id)
        staff_user.fcm_token = token
        staff_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def staff_view_notification(request):
    staff = get_object_or_404(Staff, admin=request.user)
    notifications = NotificationStaff.objects.filter(staff=staff)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "staff_template/staff_view_notification.html", context)


def staff_add_result(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(Q(staff=staff) & ~Q(name__startswith='Mentoring'))
    sessions = Session.objects.all()
    context = {
        'page_title': 'Result Upload',
        'subjects': subjects,
    }
    if request.method == 'POST':
        try:
            records = int(request.POST.get('hiddeninput'))
            sturecords = json.loads(request.POST.get('sturecords'))
            jsonData = []
            for i in range(1,records+1):
                jsonData.append({
                    'rollno':sturecords[i-1]['rollno'],
                    'mid':int(request.POST.get('mid-'+str(i))),
                    'assg':int(request.POST.get(str('assg-'+str(i)))),
                })
            exam = request.POST.get('exam')
            subject_id = request.POST.get('subject')
            subject = get_object_or_404(Subject, id=subject_id)
            try:
                
                if exam=='mid1':
                    for sdata in jsonData:
                        student=Student.objects.get(rollno = sdata['rollno'])
                        attendance = get_object_or_404(TotalAttendance,student=student)
                        mid1,assg1=int(sdata['mid']),int(sdata['assg'])
                        mid1total=math.ceil(mid1/2)+assg1+2 if (attendance.eight_present>=75) else math.ceil(mid1/2)+assg1
                        defaults={"mid2":0,"assg2":0,"mid2total":0,"internal":0}
                        stu_res,created= StudentResult.objects.update_or_create(
                            student=student,
                            subject=subject,
                            defaults={
                                'mid1':mid1,
                                'assg1':assg1,
                                'mid1total':mid1total,
                                **defaults},
                            
                        )
                        stu_res.save()
                        #update internal marks...
                        sr = StudentResult.objects.get(student=student)
                        sr.internal = math.ceil(sr.mid1total+sr.mid2total)/2
                        sr.save()
                else:
                    for sdata in jsonData:
                        student=Student.objects.get(rollno = sdata['rollno'])
                        attendance = get_object_or_404(TotalAttendance,student=student)
                        mid2,assg2=int(sdata['mid']),int(sdata['assg'])
                        mid2total=math.ceil(mid2/2)+assg2+2 if (attendance.present_percentage>=75) else math.ceil(mid2/2)+assg2
                        defaults={"mid1":0,"assg1":0,"mid1total":0,"internal":0}
                        stu_res,created= StudentResult.objects.update_or_create(
                            student=student,
                            subject=subject,
                            
                            defaults={
                                'mid2':mid2,
                                'assg2':assg2,
                                'mid2total': mid2total
                            },
                            create_defaults={"mid1":0,"assg1":0,"mid1total":0,"internal":0}
                        )
                        stu_res.save()
                        #update internal marks...
                        sr = StudentResult.objects.get(student=student)
                        sr.internal = math.ceil((sr.mid1total+sr.mid2total)/2)
                        sr.save()
                messages.success(request, "Scores Updated")
            except Exception as e:
                messages.warning(request, e)
                print("exception 1: ",e)
        except Exception as e:
            messages.warning(request, e)
            import traceback
            traceback.print_exc()
            print("exception2: ",request," ",e)
    return render(request, "staff_template/staff_add_result.html", context)


@csrf_exempt
def fetch_student_result(request):
    try:
        subject_id = request.POST.get('subject')
        student_id = request.POST.get('student')
        student = get_object_or_404(Student, id=student_id)
        subject = get_object_or_404(Subject, id=subject_id)
        result = StudentResult.objects.get(student=student, subject=subject)
        result_data = {
            'mid1': result.mid1,
            'mid2': result.mid2,
            'assg1': result.assg1,
            'assg2': result.assg2,
        }
        return HttpResponse(json.dumps(result_data))
    except Exception as e:
        return HttpResponse('False')

@csrf_exempt
def fetch_results(request):
    try:
        subject_id = request.POST.get('subject')
        subject = get_object_or_404(Subject, id=subject_id)
        results = StudentResult.objects.filter(subject=subject)
        result_data = {
            'results' : results,
        }
        return HttpResponse(json.dumps(result_data))
    except Exception as e:
        return HttpResponse('False')
    
@csrf_exempt
def staff_marks_report(request):
    staff = get_object_or_404(Staff,admin=request.user)
    subjects = Subject.objects.filter(Q(staff=staff) & ~Q(name__startswith='Mentoring'))
    students = Student.objects.all()
    results = StudentResult.objects.all()

    context = {
        'students' : students,
        'subjects' : subjects,
        'results' : results,
        'page_title' : 'Marks Report'
    }
    return render(request, 'staff_template/staff_marks_report.html', context)

@csrf_exempt
def staff_midterm_report(request):
    staff = get_object_or_404(Staff,admin=request.user)
    subjects = Subject.objects.filter(Q(staff=staff) & ~Q(name__startswith='Mentoring'))
    students = Student.objects.all()
    results = StudentResult.objects.all()

    context = {
        'students' : students,
        'subjects' : subjects,
        'results' : results,
        'page_title' : 'Marks Report'
    }
    return render(request, 'staff_template/staff_midterm_report.html', context)