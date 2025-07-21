from flask_wtf import FlaskForm
from wtforms import (
    StringField, DateField, SubmitField, SelectField, TextAreaField
)
from wtforms.validators import DataRequired, Length, Regexp, Optional
from flask_wtf.file import FileAllowed, FileField


class SupervisorForm(FlaskForm):
    # Login & Location Info
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[Optional()], 
                         description="Leave blank to keep current password")
    location_id = SelectField('Location', coerce=int, validators=[DataRequired()])

    # Personal Info
    first_name = StringField('First Name', validators=[DataRequired()])
    middle_name = StringField('Middle Name')
    last_name = StringField('Last Name', validators=[DataRequired()])
    dob = DateField('Date of Birth', validators=[DataRequired()])
    doj = DateField('Date of Joining', validators=[DataRequired()])
    phone = StringField('Phone', validators=[
        DataRequired(),
        Regexp(r'^\d{10}$', message="Enter 10 digit phone number")
    ])
    employee_code = StringField('Employee Code', validators=[DataRequired()])
    esic_no = StringField('ESIC No')
    uan_no = StringField('UAN No')
    aadhaar_no = StringField('Aadhaar No', validators=[
        DataRequired(),
        Regexp(r'^\d{12}$', message="Enter 12 digit Aadhaar number")
    ])
    pan_no = StringField('PAN No', validators=[
        DataRequired(),
        Regexp(r'^[A-Z]{5}[0-9]{4}[A-Z]$', message="Enter valid PAN number")
    ])
    designation = StringField('Designation', validators=[DataRequired()])

    # Bank Info
    account_number = StringField('Account Number', validators=[DataRequired()])
    ifsc = StringField('IFSC Code', validators=[
        DataRequired(),
        Regexp(r'^[A-Z]{4}0[A-Z0-9]{6}$', message="Enter valid IFSC code")
    ])
    bank_name = StringField('Bank Name', validators=[DataRequired()])

    # Document Uploads (Optional during edit)
    aadhaar_image = FileField('Aadhaar Image (Leave empty to keep current)', validators=[
        Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    pan_image = FileField('PAN Image (Leave empty to keep current)', validators=[
        Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    passbook_image = FileField('Passbook Image (Leave empty to keep current)', validators=[
        Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    profile_image = FileField('Profile Image (Leave empty to keep current)', validators=[
        Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])

    # Address Fields
    current_address = TextAreaField('Current Address', validators=[DataRequired()])
    permanent_address = TextAreaField('Permanent Address', validators=[DataRequired()])

    submit = SubmitField('Save Changes')
