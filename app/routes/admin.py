import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_required, current_user
from app.forms.location_form import LocationForm
from app.forms.supervisor_form import SupervisorForm
from app.forms.employee_form import EmployeeForm
from app.models import User, Supervisor, Location, Employee, Attendance
from app import db
from sqlalchemy import or_
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
import uuid

def save_uploaded_file(file, upload_folder, subfolder=''):
    """
    Save an uploaded file to the specified directory with a unique filename.
    
    Args:
        file: The file object from request.files
        upload_folder: Base directory to save the file
        subfolder: Optional subdirectory within upload_folder
        
    Returns:
        str: Relative path to the saved file, or None if no file was provided
    """
    if not file or file.filename == '':
        return None
        
    # Create a secure filename
    filename = secure_filename(file.filename)
    # Add a unique identifier to avoid filename collisions
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    
    # Create the full upload path
    if subfolder:
        upload_path = os.path.join(upload_folder, subfolder)
    else:
        upload_path = upload_folder
        
    # Create directory if it doesn't exist
    os.makedirs(upload_path, exist_ok=True)
    
    # Save the file
    file_path = os.path.join(upload_path, unique_filename)
    file.save(file_path)
    
    # Return the relative path from the static folder
    return os.path.join('uploads', subfolder, unique_filename) if subfolder else os.path.join('uploads', unique_filename)


admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    return render_template('admin/dashboard.html')

@admin_bp.route('/employees', methods=['GET'])
@login_required
def view_employees():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    
    supervisor_id = request.args.get('supervisor_id')
    location_id = request.args.get('location_id')
    search = request.args.get('search')

    query = Employee.query

    if supervisor_id:
        query = query.filter(Employee.supervisor_id == supervisor_id)
    if location_id:
        query = query.filter(Employee.location_id == location_id)
    if search:
        query = query.filter(
            or_(
                Employee.first_name.ilike(f"%{search}%"),
                Employee.phone.ilike(f"%{search}%"),
                Employee.aadhaar_no.ilike(f"%{search}%")
            )
        )

    employees = query.all()
    supervisors = Supervisor.query.all()
    locations = Location.query.all()

    return render_template('admin/employee_list.html', employees=employees,
                           supervisors=supervisors, locations=locations)

@admin_bp.route('/locations', methods=['GET', 'POST'])
@login_required
def locations():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))

    form = LocationForm()
    locations = Location.query.all()

    if form.validate_on_submit():
        existing = Location.query.filter_by(name=form.name.data.strip()).first()
        if existing:
            flash('Location already exists.', 'warning')
        else:
            new_location = Location(name=form.name.data.strip())
            db.session.add(new_location)
            db.session.commit()
            flash('Location added successfully.', 'success')
            return redirect(url_for('admin.locations'))

    return render_template('admin/locations.html', form=form, locations=locations)

@admin_bp.route('/add_supervisor', methods=['GET', 'POST'])
@login_required
def add_supervisor():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))

    form = SupervisorForm()
    form.location_id.choices = [(loc.id, loc.name) for loc in Location.query.all()]

    if form.validate_on_submit():
        # Create user
        user = User(
            username=form.username.data,
            name=f"{form.first_name.data} {form.last_name.data}",
            role='supervisor'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        def save_image(image_field):
            filename = secure_filename(image_field.data.filename)
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image_field.data.save(path)
            return f'uploads/{filename}'

        supervisor = Supervisor(
            user_id=user.id,
            location_id=form.location_id.data,
            first_name=form.first_name.data,
            middle_name=form.middle_name.data,
            last_name=form.last_name.data,
            dob=form.dob.data,
            doj=form.doj.data,
            phone=form.phone.data,
            employee_code=form.employee_code.data,
            esic_no=form.esic_no.data,
            uan_no=form.uan_no.data,
            aadhaar_no=form.aadhaar_no.data,
            pan_no=form.pan_no.data,
            designation=form.designation.data,
            account_number=form.account_number.data,
            ifsc=form.ifsc.data,
            bank_name=form.bank_name.data,
            aadhaar_image=save_image(form.aadhaar_image),
            pan_image=save_image(form.pan_image),
            passbook_image=save_image(form.passbook_image),
            profile_image=save_image(form.profile_image),
            current_address=form.current_address.data,
            permanent_address=form.permanent_address.data
        )

        db.session.add(supervisor)
        db.session.commit()

        flash('Supervisor registered successfully!', 'success')
        return redirect(url_for('admin.add_supervisor'))

    return render_template('admin/add_supervisor.html', form=form)

@admin_bp.route('/supervisors')
@login_required
def view_supervisors():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))

    supervisors = Supervisor.query.all()
    return render_template('admin/view_supervisors.html', supervisors=supervisors)

@admin_bp.route('/supervisors/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_supervisor(id):
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
        
    supervisor = Supervisor.query.get_or_404(id)
    
    # Get locations for dropdown
    locations = Location.query.all()
    
    # Initialize form with the supervisor object for both GET and POST
    form = SupervisorForm(obj=supervisor)
    form.location_id.choices = [(loc.id, loc.name) for loc in locations]
    
    if request.method == 'POST':
        # For POST request, populate form from request data
        form = SupervisorForm(request.form, obj=supervisor)
        form.location_id.choices = [(loc.id, loc.name) for loc in locations]
        
        # Handle file uploads
        form.aadhaar_image.data = request.files.get('aadhaar_image')
        form.pan_image.data = request.files.get('pan_image')
        form.passbook_image.data = request.files.get('passbook_image')
        form.profile_image.data = request.files.get('profile_image')
    
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
        try:
            # Update supervisor fields (excluding password)
            update_fields = [
                'username', 'location_id', 'first_name', 'middle_name', 'last_name',
                'dob', 'doj', 'phone', 'employee_code', 'designation', 'esic_no',
                'uan_no', 'aadhaar_no', 'pan_no', 'account_number', 'ifsc',
                'bank_name', 'current_address', 'permanent_address'
            ]
            
            for field in update_fields:
                if hasattr(form, field):
                    setattr(supervisor, field, getattr(form, field).data)
                    print(f"Updated {field}: {getattr(supervisor, field)}")
            
            # Only update password if a new one is provided
            if form.password.data:
                print("Updating password")
                # Get the associated user and update the password
                user = User.query.get(supervisor.user_id)
                if user:
                    user.set_password(form.password.data)
                    db.session.add(user)
                else:
                    print(f"Error: User with ID {supervisor.user_id} not found")
            
            if form.profile_image.data:
                file_ext = form.profile_image.data.filename.rsplit('.', 1)[1].lower()
                filename = f"profile_{supervisor.id}.{file_ext}"
                save_dir = os.path.join(current_app.static_folder, 'uploads', 'profiles')
                save_dir = os.path.join(current_app.static_folder, 'uploads', 'profiles')
                os.makedirs(save_dir, exist_ok=True)
                # Save the file
                filepath = os.path.join(save_dir, filename)
                form.profile_image.data.save(filepath)
                # Store only the relative path from static folder
                supervisor.profile_image = f"uploads/profiles/{filename}"
                
            if form.aadhaar_image.data:
                file_ext = form.aadhaar_image.data.filename.rsplit('.', 1)[1].lower()
                filename = f"aadhaar_{supervisor.id}.{file_ext}"
                save_dir = os.path.join(current_app.static_folder, 'uploads', 'documents')
                os.makedirs(save_dir, exist_ok=True)
                filepath = os.path.join(save_dir, filename)
                form.aadhaar_image.data.save(filepath)
                supervisor.aadhaar_image = f"uploads/documents/{filename}"
                
            if form.pan_image.data:
                file_ext = form.pan_image.data.filename.rsplit('.', 1)[1].lower()
                filename = f"pan_{supervisor.id}.{file_ext}"
                save_dir = os.path.join(current_app.static_folder, 'uploads', 'documents')
                os.makedirs(save_dir, exist_ok=True)
                filepath = os.path.join(save_dir, filename)
                form.pan_image.data.save(filepath)
                supervisor.pan_image = f"uploads/documents/{filename}"
                
            if form.passbook_image.data:
                file_ext = form.passbook_image.data.filename.rsplit('.', 1)[1].lower()
                filename = f"passbook_{supervisor.id}.{file_ext}"
                save_dir = os.path.join(current_app.static_folder, 'uploads', 'documents')
                os.makedirs(save_dir, exist_ok=True)
                filepath = os.path.join(save_dir, filename)
                form.passbook_image.data.save(filepath)
                supervisor.passbook_image = f"uploads/documents/{filename}"
            
            # Commit changes to database
            db.session.commit()
            print("Changes committed to database")
            flash('Supervisor updated successfully!', 'success')
            return redirect(url_for('admin.view_supervisors'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Error updating supervisor: {str(e)}"
            print(error_msg)
            current_app.logger.error(error_msg)
            flash('An error occurred while updating the supervisor. Please check the logs.', 'danger')
    else:
        print("Form validation failed. Errors:", form.errors)
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", 'danger')
    
    return render_template('admin/edit_supervisor.html', form=form, supervisor=supervisor)

@admin_bp.route('/approve-employees')
@login_required
def approve_employees():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    pending_employees = Employee.query.filter_by(status='pending').all()
    return render_template('admin/approve_employees.html', employees=pending_employees)

@admin_bp.route('/download-attendance', methods=['GET'])
@login_required
def download_attendance():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))

    # Get filter parameters
    supervisor_id = request.args.get('supervisor_id')
    location_id = request.args.get('location_id')
    search = request.args.get('search', '').strip()
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    # Build the base query
    query = db.session.query(
        Employee, Attendance
    ).join(
        Attendance, Employee.id == Attendance.employee_id, isouter=True
    )

    # Apply filters
    if supervisor_id:
        query = query.filter(Employee.supervisor_id == supervisor_id)
    if location_id:
        query = query.filter(Employee.location_id == location_id)
    if search:
        query = query.filter(
            or_(
                Employee.first_name.ilike(f'%{search}%'),
                Employee.last_name.ilike(f'%{search}%'),
                Employee.phone.ilike(f'%{search}%'),
                Employee.aadhaar_no.ilike(f'%{search}%')
            )
        )
    if from_date:
        try:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.date >= from_date)
        except ValueError:
            pass
    if to_date:
        try:
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.date <= to_date)
        except ValueError:
            pass

    # Get all supervisors and locations for the filter form
    supervisors = Supervisor.query.all()
    locations = Location.query.all()

    # If it's a form submission (has any filter), generate Excel
    if any([supervisor_id, location_id, search, from_date, to_date]):
        records = query.all()
        
        # Prepare data for Excel
        data = []
        for emp, att in records:
            if att:  # Only include records with attendance
                data.append({
                    'Date': att.date.strftime('%Y-%m-%d'),
                    'Employee Name': f"{emp.first_name} {emp.last_name}",
                    'Employee Code': emp.employee_code,
                    'Location': emp.location.name if emp.location else '',
                    'Supervisor': f"{emp.supervisor.first_name} {emp.supervisor.last_name}" if emp.supervisor else '',
                    'Status': att.status,
                    'Overtime Hours': att.overtime_hours if att.overtime_hours is not None else 0
                })
        
        # Create DataFrame and Excel file in memory
        if data:
            df = pd.DataFrame(data)
            output = BytesIO()
            df.to_excel(output, index=False, sheet_name='Attendance')
            output.seek(0)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"attendance_report_{timestamp}.xlsx"
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
        else:
            flash('No attendance records found matching the criteria.', 'info')
    
    # If it's just a page load or no records found, render the template
    return render_template(
        'admin/download_attendance.html',
        supervisors=supervisors,
        locations=locations,
        current_supervisor=supervisor_id,
        current_location=location_id,
        current_search=search,
        current_from_date=from_date,
        current_to_date=to_date
    )

@admin_bp.route('/employee_action/<int:emp_id>/<string:action>')
@login_required
def employee_action(emp_id, action):
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))

    employee = Employee.query.get_or_404(emp_id)

    if action == 'accept':
        employee.status = 'approved'
        flash('Employee approved.', 'success')
    elif action == 'reject':
        employee.status = 'rejected'
        flash('Employee rejected.', 'danger')

    db.session.commit()
    return redirect(url_for('admin.approve_employees'))
@admin_bp.route('/employees/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    form = EmployeeForm(obj=employee)

    # Populate supervisor and location choices
    from sqlalchemy.orm import joinedload
    supervisors = db.session.query(Supervisor).options(joinedload(Supervisor.user)).all()
    form.supervisor_id.choices = [(sup.id, f"{sup.first_name} {sup.last_name}") for sup in supervisors]  # Using sup.id instead of sup.user.id
    form.location_id.choices = [(l.id, l.name) for l in Location.query.all()]

    if form.validate_on_submit():
        employee.first_name = form.first_name.data
        employee.middle_name = form.middle_name.data
        employee.last_name = form.last_name.data
        employee.phone = form.phone.data
        employee.designation = form.designation.data
        employee.dob = form.dob.data
        employee.doj = form.doj.data
        employee.aadhaar_no = form.aadhaar_no.data
        employee.pan_no = form.pan_no.data
        employee.account_number = form.account_number.data
        employee.ifsc = form.ifsc.data
        employee.bank_name = form.bank_name.data
        employee.current_address = form.current_address.data
        employee.permanent_address = form.permanent_address.data
        employee.supervisor_id = form.supervisor_id.data
        employee.location_id = form.location_id.data
        employee.employee_code = form.employee_code.data

        # Save and assign file paths if files were uploaded
        upload_folder = os.path.join(current_app.root_path, 'static/uploads')

        profile_path = save_uploaded_file(form.profile_image.data, upload_folder, f"E{employee.id}_images")
        aadhaar_path = save_uploaded_file(form.aadhaar_image.data, upload_folder, f"E{employee.id}_adhar")
        pan_path = save_uploaded_file(form.pan_image.data, upload_folder, f"E{employee.id}_pan")
        passbook_path = save_uploaded_file(form.passbook_image.data, upload_folder, f"E{employee.id}_pass")

        if profile_path:
            employee.profile_image = profile_path
        if aadhaar_path:
            employee.aadhaar_image = aadhaar_path
        if pan_path:
            employee.pan_image = pan_path
        if passbook_path:
            employee.passbook_image = passbook_path

        db.session.commit()
        flash("Employee updated successfully.", "success")
        return redirect(url_for("admin.view_employees"))

    return render_template("admin/edit_employee.html", form=form, employee=employee)

    employee = Employee.query.get_or_404(id)
    form = EmployeeForm(obj=employee)

    # Populate supervisor and location choices
    form.supervisor_id.choices = [(u.id, u.username) for u in User.query.filter_by(role='Supervisor').all()]
    form.location_id.choices = [(l.id, l.name) for l in Location.query.all()]

    if form.validate_on_submit():
        form.populate_obj(employee)

        # Image handling
        upload_fields = {
            'aadhaar_image': 'aadhaar_image_path',
            'pan_image': 'pan_image_path',
            'passbook_image': 'passbook_image_path',
            'profile_image': 'image_path'
        }

        for field_name, attr_name in upload_fields.items():
            file = getattr(form, field_name).data
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                setattr(employee, attr_name, filename)

        db.session.commit()
        flash('Employee updated successfully!', 'success')
        return redirect(url_for('admin.view_employees'))

    return render_template('admin/edit_employee.html', form=form, employee=employee)

@admin_bp.route('/employees/<int:id>/delete', methods=['POST'])
@login_required
def delete_employee(id):
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    employee = Employee.query.get_or_404(id)
    db.session.delete(employee)
    db.session.commit()
    flash('Employee deleted successfully!', 'success')
    return redirect(url_for('admin.view_employees'))

@admin_bp.route('/supervisors/delete/<int:id>', methods=['POST'])
@login_required
def delete_supervisor(id):
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    
    try:
        # Get the supervisor and associated user
        supervisor = Supervisor.query.get_or_404(id)
        user = User.query.get(supervisor.user_id)
        
        if user:
            # Delete the supervisor record first to avoid foreign key constraint
            db.session.delete(supervisor)
            # Then delete the user
            db.session.delete(user)
            db.session.commit()
            flash('Supervisor deleted successfully!', 'success')
        else:
            flash('Associated user not found!', 'danger')
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting supervisor: {str(e)}')
        flash('An error occurred while deleting the supervisor.', 'danger')
    
    return redirect(url_for('admin.view_supervisors'))
