from sqlalchemy.orm import joinedload

@admin_bp.route('/employees/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    form = EmployeeForm(obj=employee)

    # Populate supervisor and location choices
    from sqlalchemy.orm import joinedload
    supervisors = db.session.query(Supervisor).options(joinedload(Supervisor.user)).all()
    form.supervisor_id.choices = [(sup.user.id, f"{sup.first_name} {sup.last_name}") for sup in supervisors]
    form.location_id.choices = [(l.id, l.name) for l in Location.query.all()]

    if form.validate_on_submit():
        employee.first_name = form.first_name.data
        employee.middle_name = form.middle_name.data
        employee.last_name = form.last_name.data
        employee.phone = form.phone.data
        employee.dob = form.dob.data
        employee.doj = form.doj.data
        employee.employee_code = form.employee_code.data
        employee.designation = form.designation.data
        employee.aadhaar_no = form.aadhaar_no.data
        employee.pan_no = form.pan_no.data
        employee.account_number = form.account_number.data
        employee.ifsc = form.ifsc.data
        employee.bank_name = form.bank_name.data
        employee.current_address = form.current_address.data
        employee.permanent_address = form.permanent_address.data
        employee.supervisor_id = form.supervisor_id.data
        employee.location_id = form.location_id.data

        # Handle file uploads
        def save_file(file_field, attr_name):
            if file_field.data:
                filename = secure_filename(file_field.data.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file_field.data.save(file_path)
                setattr(employee, attr_name, f'documents/{filename}')

        save_file(form.aadhaar_image, 'aadhaar_image')
        save_file(form.pan_image, 'pan_image')
        save_file(form.passbook_image, 'passbook_image')
        save_file(form.profile_image, 'profile_image')

        db.session.commit()
        flash('Employee updated successfully!', 'success')
        return redirect(url_for('admin.view_employees'))

    return render_template('admin/edit_employee.html', form=form, employee=employee)
