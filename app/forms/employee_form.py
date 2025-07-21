from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, FileField, SelectField  # Add SelectField here
from wtforms.validators import DataRequired, Regexp, Optional
from flask_wtf.file import FileAllowed

class EmployeeForm(FlaskForm):
    # Basic Info
    supervisor_id = SelectField('Supervisor', coerce=int, validators=[DataRequired()])
    location_id = SelectField('Location', coerce=int, validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    middle_name = StringField('Middle Name', validators=[Optional()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    dob = DateField('Date of Birth', validators=[DataRequired()])
    doj = DateField('Date of Joining', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired(), Regexp(r'^\d{10}$')])
    employee_code = StringField('Employee Code', validators=[DataRequired()])
    designation = StringField('Designation', validators=[DataRequired()])

    # ID Details
    aadhaar_no = StringField('Aadhaar No', validators=[DataRequired(), Regexp(r'^\d{12}$')])
    pan_no = StringField('PAN No', validators=[DataRequired(), Regexp(r'^[A-Z]{5}[0-9]{4}[A-Z]$')])

    # Bank Details
    account_number = StringField('Account Number', validators=[DataRequired()])
    ifsc = StringField('IFSC Code', validators=[DataRequired(), Regexp(r'^[A-Z]{4}0[A-Z0-9]{6}$')])
    bank_name = StringField('Bank Name', validators=[DataRequired()])

    # Address
    current_address = StringField('Current Address', validators=[DataRequired()])
    permanent_address = StringField('Permanent Address', validators=[DataRequired()])

    # Images (optional in edit)
    aadhaar_image = FileField('Aadhaar Image', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png'])])
    pan_image = FileField('PAN Image', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png'])])
    passbook_image = FileField('Passbook Image', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png'])])
    profile_image = FileField('Profile Image', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png'])])

    submit = SubmitField('Save')
