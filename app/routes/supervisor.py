from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.forms.employee_form import EmployeeForm
from app.forms.attendance_form import AttendanceForm
from app.models import User, Employee, Supervisor, Attendance, Location
from app.utils.excel_export import generate_attendance_excel
from app import db
from datetime import datetime, timedelta
import os

supervisor_bp = Blueprint('supervisor', __name__)

@supervisor_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'supervisor':
        return redirect(url_for('auth.login'))
    
    # Get all employees supervised by the current user
    employees = Employee.query.filter_by(supervisor_id=current_user.supervisor.id).all()
    return render_template('supervisor/dashboard.html', employees=employees)

@supervisor_bp.route('/employee_list')
@login_required
def employee_list():
    if current_user.role != 'supervisor':
        abort(403)

    supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()
    if not supervisor:
        flash('Supervisor not found', 'danger')
        return redirect(url_for('supervisor.dashboard'))

    employees = Employee.query.filter_by(location_id=supervisor.location_id).all()
    return render_template('supervisor/employee_list.html', employees=employees)

@supervisor_bp.route('/my_employees')
@login_required
def my_employees():
    if current_user.role != 'supervisor':
        return redirect(url_for('auth.login'))
    
    supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()
    if not supervisor:
        flash('Supervisor not found', 'danger')
        return redirect(url_for('supervisor.dashboard'))

    employees = Employee.query.filter_by(location_id=supervisor.location_id).all()
    return render_template('supervisor/my_employees.html', employees=employees)

@supervisor_bp.route('/mark_attendance', methods=['GET', 'POST'])
@supervisor_bp.route('/mark_attendance/<int:week_offset>', methods=['GET', 'POST'])
@login_required
def mark_attendance(week_offset=0):
    # Handle negative week offset (previous weeks)
    if week_offset < 0:
        flash("No previous attendance records available.", "info")
        return redirect(url_for('supervisor.mark_attendance', week_offset=0))
        
    # Get supervisor and verify they exist
    supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()
    if not supervisor or not supervisor.location_id:
        flash("Supervisor profile or location not found.", "danger")
        return redirect(url_for("supervisor.dashboard"))

    # Get all employees at the supervisor's location
    employees = Employee.query.filter_by(location_id=supervisor.location_id).order_by(Employee.first_name).all()
    
    if not employees:
        flash("No employees found at your location.", "warning")
        return redirect(url_for("supervisor.dashboard"))

    # Calculate the target date based on week offset
    target_date = datetime.now().date() + timedelta(weeks=week_offset)
    
    # Calculate week start (Monday) and dates for the week
    start_of_week = target_date - timedelta(days=target_date.weekday())
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
    
    # Get existing attendance data for the week
    attendance_data = {}
    for emp in employees:
        emp_attendance = {}
        for date in week_dates:
            attendance = Attendance.query.filter_by(
                employee_id=emp.id,
                date=date
            ).first()
            
            if attendance:
                emp_attendance[str(date)] = {
                    'status': attendance.status,
                    'overtime_hours': attendance.overtime_hours
                }
            else:
                emp_attendance[str(date)] = {
                    'status': 'Absent',
                    'overtime_hours': 0.0
                }
        attendance_data[emp.id] = emp_attendance

    # POST = save attendance
    if request.method == 'POST':
        # Only process current date
        current_date = datetime.now().date()
        
        for emp in employees:
            # Only process current date
            date = current_date
            # Check if attendance checkbox is checked for this employee and date
            is_present = f'attendance_{emp.id}_{date}' in request.form
            overtime_key = f'overtime_{emp.id}_{date}'
            overtime_hours = float(request.form.get(overtime_key, 0))
            
            # Skip if no attendance data for this date
            if not is_present and overtime_hours == 0:
                continue
                
            # Update or create attendance record
            attendance = Attendance.query.filter_by(
                employee_id=emp.id,
                date=date
            ).first()
            
            if attendance:
                # Update existing record
                attendance.status = 'Present' if is_present else 'Absent'
                attendance.overtime_hours = overtime_hours
                attendance.marked_by = current_user.id
                attendance.timestamp = datetime.utcnow()
            else:
                # Create new record
                attendance = Attendance(
                    employee_id=emp.id,
                    date=date,
                    status='Present' if is_present else 'Absent',
                    overtime_hours=overtime_hours,
                    marked_by=current_user.id,
                    timestamp=datetime.utcnow()
                )
                db.session.add(attendance)
        
        try:
            db.session.commit()
            flash('Attendance updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating attendance: {str(e)}", "danger")
            
        return redirect(url_for('supervisor.mark_attendance', week_offset=week_offset))

    # Preload attendance data for all employees and dates
    attendance_data = {}
    for emp in employees:
        emp_attendance = {}
        for date in week_dates:
            attendance = Attendance.query.filter_by(
                employee_id=emp.id, 
                date=date
            ).first()
            if attendance:
                emp_attendance[str(date)] = {
                    'status': attendance.status,
                    'overtime_hours': attendance.overtime_hours
                }
        attendance_data[emp.id] = emp_attendance

    # GET = render page
    form = AttendanceForm()
    # Calculate current week number (1-5 in the month)
    today = datetime.now().date()
    first_day = today.replace(day=1)
    week_no = (today.day - 1) // 7 + 1
    
    return render_template("supervisor/mark_attendance.html",
                           form=form,
                           employees=employees,
                           week_dates=week_dates,
                           attendance_data=attendance_data,
                           location_name=supervisor.location.name,
                           month_name=target_date.strftime('%B'),
                           week_no=week_no,
                           week_offset=week_offset,
                           target_date=target_date,
                           supervisor_name=f"{supervisor.first_name} {supervisor.last_name}")

@supervisor_bp.route('/download_attendance')
@login_required
def download_attendance():
    supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()
    if not supervisor:
        flash("Supervisor not found", "danger")
        return redirect(url_for('supervisor.dashboard'))

    location_id = supervisor.location_id
    week_start = datetime.today().date() - timedelta(days=datetime.today().weekday() + 1)
    week_dates = [week_start + timedelta(days=i) for i in range(7)]

    employees = Employee.query.filter_by(location_id=location_id).all()
    data = []

    for emp in employees:
        row = {
            'Name': f"{emp.first_name} {emp.last_name}",
            'Location': emp.location.name
        }
        for day in week_dates:
            att = Attendance.query.filter_by(employee_id=emp.id, date=day).first()
            row[day.strftime("%A (%d-%b)")] = att.status if att else ''
        data.append(row)

    file_path = generate_attendance_excel(data)
    return send_file(file_path, as_attachment=True, download_name="attendance.xlsx")

@supervisor_bp.route('/edit_employee/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    if current_user.role != 'supervisor':
        abort(403)

    employee = Employee.query.get_or_404(employee_id)
    supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()

    # Verify employee belongs to this supervisor's location
    if employee.location_id != supervisor.location_id:
        flash('You cannot edit this employee.', 'danger')
        return redirect(url_for('supervisor.employee_list'))

    form = EmployeeForm(obj=employee)

    if form.validate_on_submit():
        # Update employee fields
        employee.first_name = form.first_name.data
        employee.middle_name = form.middle_name.data
        employee.last_name = form.last_name.data
        employee.dob = form.dob.data
        employee.doj = form.doj.data
        employee.phone = form.phone.data
        employee.employee_code = form.employee_code.data
        employee.designation = form.designation.data
        employee.aadhaar_no = form.aadhaar_no.data
        employee.pan_no = form.pan_no.data
        employee.account_number = form.account_number.data
        employee.ifsc = form.ifsc.data
        employee.bank_name = form.bank_name.data
        employee.current_address = form.current_address.data
        employee.permanent_address = form.permanent_address.data

        # Handle image uploads
        def save_image(image_field):
            if image_field.data:
                filename = secure_filename(image_field.data.filename)
                path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                image_field.data.save(path)
                return f'uploads/{filename}'
            return None

        if form.aadhaar_image.data:
            employee.aadhaar_image = save_image(form.aadhaar_image)
        if form.pan_image.data:
            employee.pan_image = save_image(form.pan_image)
        if form.passbook_image.data:
            employee.passbook_image = save_image(form.passbook_image)
        if form.profile_image.data:
            employee.profile_image = save_image(form.profile_image)

        db.session.commit()
        flash('Employee updated successfully.', 'success')
        return redirect(url_for('supervisor.employee_list'))

    return render_template('supervisor/edit_employee.html', form=form, employee=employee)

@supervisor_bp.route('/add_employee', methods=['GET', 'POST'])
@login_required
def add_employee():
    if current_user.role != 'supervisor':
        return redirect(url_for('auth.login'))

    form = EmployeeForm()
    
    # Set choices for SelectFields
    from app.models import Location
    form.location_id.choices = [(loc.id, loc.name) for loc in Location.query.all()]
    # For supervisor, since it's the current user, we can set it directly
    form.supervisor_id.choices = [(current_user.supervisor.id, current_user.supervisor.user.username)]

    # Debug: Print form data and validation status
    print("\n=== Form Debug ===")
    print(f"Method: {request.method}")
    print(f"Form validated: {form.validate()}")
    if not form.validate():
        print("Form errors:", form.errors)
    print("Form data:", form.data)
    print("================\n")

    if form.validate_on_submit():
        print("\n=== Processing Form Submission ===")
        def save_image(image_field):
            if not image_field.data:
                return None
            try:
                filename = secure_filename(image_field.data.filename)
                path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                image_field.data.save(path)
                return f'uploads/{filename}'
            except Exception as e:
                print(f"Error saving image {image_field.name}: {str(e)}")
                return None

        try:
            # Create uploads directory if it doesn't exist
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            new_employee = Employee(
                supervisor_id=current_user.supervisor.id,
                location_id=form.location_id.data,
                first_name=form.first_name.data,
                middle_name=form.middle_name.data,
                last_name=form.last_name.data,
                dob=form.dob.data,
                doj=form.doj.data,
                phone=form.phone.data,
                employee_code=form.employee_code.data,
                designation=form.designation.data,
                aadhaar_no=form.aadhaar_no.data,
                pan_no=form.pan_no.data,
                account_number=form.account_number.data,
                ifsc=form.ifsc.data,
                bank_name=form.bank_name.data,
                current_address=form.current_address.data,
                permanent_address=form.permanent_address.data,
                aadhaar_image=save_image(form.aadhaar_image),
                pan_image=save_image(form.pan_image),
                passbook_image=save_image(form.passbook_image),
                profile_image=save_image(form.profile_image),
                status='pending'
            )

            db.session.add(new_employee)
            db.session.commit()
            print("Employee added successfully!")
            flash('Employee added successfully. Pending approval.', 'success')
            return redirect(url_for('supervisor.dashboard'))
        except Exception as e:
            db.session.rollback()
            print(f"Error adding employee: {str(e)}")
            flash('An error occurred while adding the employee. Please try again.', 'danger')

    return render_template('supervisor/add_employee.html', form=form)
