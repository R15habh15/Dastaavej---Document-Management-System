from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, TextAreaField, FileField, HiddenField, EmailField, BooleanField
from wtforms.fields import DateField  # Add this import for DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp
from flask_wtf.file import FileField, FileRequired, FileAllowed
import re  # Add this import for regular expressions
from datetime import date
from flask_wtf.file import FileField, FileRequired, FileAllowed

class UpdateStatusForm(FlaskForm):
    status = SelectField('Status', 
                        choices=[
                            ('pending', 'Pending'),
                            ('under review', 'Under Review'),
                            ('approved', 'Approved'),
                            ('rejected', 'Rejected')
                        ],
                        validators=[DataRequired()])
    comment = TextAreaField('Comment')

class PassportDocumentForm(FlaskForm):
    id_proof = FileField('ID Proof', 
                        validators=[
                            FileRequired(),
                            FileAllowed(['jpg', 'png', 'pdf'], 'Images and PDF only!')
                        ])
    photo = FileField('Photo',
                     validators=[
                         FileRequired(),
                         FileAllowed(['jpg', 'png'], 'Images only!')
                     ])
    address_proof = FileField('Address Proof',
                            validators=[
                                FileRequired(),
                                FileAllowed(['jpg', 'png', 'pdf'], 'Images and PDF only!')
                            ])
    dob_proof = FileField('Proof of Date of Birth',
                         validators=[
                             FileRequired(),
                             FileAllowed(['jpg', 'png', 'pdf'], 'Images and PDF only!')
                         ])
    submit = SubmitField('Upload Documents')

class PanCardDocumentForm(FlaskForm):
    id_proof = FileField('ID Proof (Aadhaar/Voter ID/Driving License)', 
                        validators=[FileRequired(), FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'PDF or images only!')])
    photo = FileField('Recent Passport Size Photo', 
                     validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    address_proof = FileField('Address Proof', 
                             validators=[FileRequired(), FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'PDF or images only!')])
    signature = FileField('Signature', 
                         validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    submit = SubmitField('Upload Documents')

class ForgotPasswordForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), 
                                             EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Reset Password')

def validate_username(form, field):
    # Check for minimum 8 characters, one uppercase, one lowercase, one number
    if len(field.data) < 8:
        raise ValidationError('Username must be at least 8 characters long')
    
    if not re.search(r'[A-Z]', field.data):
        raise ValidationError('Username must contain at least one uppercase letter')
    
    if not re.search(r'[a-z]', field.data):
        raise ValidationError('Username must contain at least one lowercase letter')
    
    if not re.search(r'[0-9]', field.data):
        raise ValidationError('Username must contain at least one number')

def validate_password(form, field):
    # Check for 8-20 characters, one uppercase, one lowercase, one number, one special symbol
    if len(field.data) < 8 or len(field.data) > 20:
        raise ValidationError('Password must be between 8 and 20 characters long')
    
    if not re.search(r'[A-Z]', field.data):
        raise ValidationError('Password must contain at least one uppercase letter')
    
    if not re.search(r'[a-z]', field.data):
        raise ValidationError('Password must contain at least one lowercase letter')
    
    if not re.search(r'[0-9]', field.data):
        raise ValidationError('Password must contain at least one number')
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', field.data):
        raise ValidationError('Password must contain at least one special character')
    
    # Check if password contains username
    if form.username.data and form.username.data.lower() in field.data.lower():
        raise ValidationError('Password must not contain your username')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        validate_username
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        validate_password
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[('citizen', 'Citizen'), ('agency', 'Agency Official')], validators=[DataRequired()])
    government_id = StringField('Government ID Number') 
    submit = SubmitField('Register')  # Make sure this line exists

class OTPVerificationForm(FlaskForm):
    otp = StringField('Enter OTP sent to your email', validators=[DataRequired()])
    submit = SubmitField('Verify OTP')


class PassportApplicationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=3, max=100, message="Name must be between 3 and 100 characters")
    ])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()], format='%Y-%m-%d')
    gender = SelectField('Gender', choices=[
        ('male', 'Male'), 
        ('female', 'Female'), 
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    # Permanent Address Fields with enhanced validation
    permanent_address = TextAreaField('Permanent Address', validators=[
        DataRequired(),
        Length(min=10, max=500, message="Address must be between 10 and 500 characters")
    ])
    permanent_state = StringField('State', validators=[
        DataRequired(),
        Length(min=2, max=50, message="State name must be between 2 and 50 characters"),
        Regexp(r'^[A-Za-z\s]+$', message="State must contain only letters and spaces")
    ])
    permanent_pincode = StringField('Pincode', validators=[
        DataRequired(),
        Regexp(r'^\d{6}$', message="Pincode must be exactly 6 digits")
    ])
    permanent_country = SelectField('Country', choices=[
        ('india', 'India'),
        ('usa', 'United States'),
        ('uk', 'United Kingdom'),
        ('canada', 'Canada'),
        ('australia', 'Australia'),
        ('other', 'Other')
    ], default='india', validators=[DataRequired()])
    
    # Current Address Fields with option to copy from permanent
    same_as_permanent = BooleanField('Current Address Same as Permanent Address')
    
    current_address = TextAreaField('Current Address', validators=[
        DataRequired(),
        Length(min=10, max=500, message="Address must be between 10 and 500 characters")
    ])
    current_state = StringField('State', validators=[
        DataRequired(),
        Length(min=2, max=50, message="State name must be between 2 and 50 characters"),
        Regexp(r'^[A-Za-z\s]+$', message="State must contain only letters and spaces")
    ])
    current_pincode = StringField('Pincode', validators=[
        DataRequired(),
        Regexp(r'^\d{6}$', message="Pincode must be exactly 6 digits")
    ])
    current_country = SelectField('Country', choices=[
        ('india', 'India'),
        ('usa', 'United States'),
        ('uk', 'United Kingdom'),
        ('canada', 'Canada'),
        ('australia', 'Australia'),
        ('other', 'Other')
    ], default='india', validators=[DataRequired()])
    
    # Phone field with validation
    phone = StringField('Phone Number', validators=[
        DataRequired(),
        Regexp(r'^\d{10}$', message="Phone number must be exactly 10 digits")
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email(message="Please enter a valid email address")
    ])
    # Emergency Contact fields with enhanced validation
    next_of_kin = StringField('Emergency Contact Name', validators=[
        DataRequired(),
        Length(min=3, max=100, message="Name must be between 3 and 100 characters")
    ])
    next_of_kin_relation = SelectField('Relationship', choices=[
        ('parent', 'Parent'),
        ('spouse', 'Spouse'),
        ('sibling', 'Sibling'),
        ('child', 'Child'),
        ('friend', 'Friend'),
        ('relative', 'Other Relative')
    ], validators=[DataRequired()])
    next_of_kin_phone = StringField('Emergency Contact Phone', validators=[
        DataRequired(),
        Regexp(r'^\d{10}$', message="Phone number must be exactly 10 digits")
    ])
    submit = SubmitField('Continue to Document Upload')
    
    def validate_next_of_kin_phone(self, field):
        if field.data == self.phone.data:
            raise ValidationError('Emergency contact number cannot be the same as your phone number')

    # Remove the age limit validation by commenting it out or removing it
    def validate_date_of_birth(self, field):
        if field.data:
            today = date.today()
            age = today.year - field.data.year - ((today.month, today.day) < (field.data.month, field.data.day))
            # Removed age limit validation
            if age > 120:
                raise ValidationError('Please enter a valid date of birth')

    def validate(self, extra_validators=None):
        # First run the standard validation
        if not super(PassportApplicationForm, self).validate(extra_validators=extra_validators):
            return False
        
        # If "same as permanent" is checked, copy permanent address values to current address
        if self.same_as_permanent.data:
            self.current_address.data = self.permanent_address.data
            self.current_state.data = self.permanent_state.data
            self.current_pincode.data = self.permanent_pincode.data
            self.current_country.data = self.permanent_country.data
            
            # Clear any errors on these fields since we've populated them
            if 'current_address' in self.errors:
                del self.errors['current_address']
            if 'current_state' in self.errors:
                del self.errors['current_state']
            if 'current_pincode' in self.errors:
                del self.errors['current_pincode']
            if 'current_country' in self.errors:
                del self.errors['current_country']
        
        return True

class PanCardApplicationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=3, max=100, message="Name must be between 3 and 100 characters")
    ])
    father_name = StringField('Father\'s Name', validators=[
        DataRequired(),
        Length(min=3, max=100, message="Name must be between 3 and 100 characters")
    ])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()], format='%Y-%m-%d')
    gender = SelectField('Gender', choices=[
        ('male', 'Male'), 
        ('female', 'Female'), 
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    # Permanent Address Fields
    permanent_address = TextAreaField('Permanent Address', validators=[
        DataRequired(),
        Length(min=10, max=500, message="Address must be between 10 and 500 characters")
    ])
    permanent_state = StringField('State', validators=[
        DataRequired(),
        Length(min=2, max=50, message="State name must be between 2 and 50 characters")
    ])
    permanent_pincode = StringField('Pincode', validators=[
        DataRequired(),
        Regexp(r'^\d{6}$', message="Pincode must be 6 digits")
    ])
    permanent_country = SelectField('Country', choices=[
        ('india', 'India'),
        ('usa', 'United States'),
        ('uk', 'United Kingdom'),
        ('canada', 'Canada'),
        ('australia', 'Australia'),
        ('other', 'Other')
    ], default='india', validators=[DataRequired()])
    
    # Current Address Fields with option to copy from permanent
    same_as_permanent = BooleanField('Current Address Same as Permanent Address')
    
    current_address = TextAreaField('Current Address', validators=[
        DataRequired(),
        Length(min=10, max=500, message="Address must be between 10 and 500 characters")
    ])
    current_state = StringField('State', validators=[
        DataRequired(),
        Length(min=2, max=50, message="State name must be between 2 and 50 characters")
    ])
    current_pincode = StringField('Pincode', validators=[
        DataRequired(),
        Regexp(r'^\d{6}$', message="Pincode must be 6 digits")
    ])
    current_country = SelectField('Country', choices=[
        ('india', 'India'),
        ('usa', 'United States'),
        ('uk', 'United Kingdom'),
        ('canada', 'Canada'),
        ('australia', 'Australia'),
        ('other', 'Other')
    ], default='india', validators=[DataRequired()])
    
    phone = StringField('Phone Number', validators=[
        DataRequired(), 
        Length(min=10, max=15),
        Regexp(r'^\d+$', message="Phone number must contain only digits")
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email(message="Please enter a valid email address")
    ])
    aadhaar_number = StringField('Aadhaar Number', validators=[
        DataRequired(), 
        Length(min=12, max=12, message="Aadhaar number must be exactly 12 digits"),
        Regexp(r'^\d{12}$', message="Aadhaar number must contain exactly 12 digits")
    ])
    submit = SubmitField('Continue to Document Upload')
    
    def validate_date_of_birth(self, field):
        if field.data:
            today = date.today()
            age = today.year - field.data.year - ((today.month, today.day) < (field.data.month, field.data.day))
            if age < 18:
                raise ValidationError('You must be at least 18 years old to apply for a PAN card')
            if age > 120:
                raise ValidationError('Please enter a valid date of birth')

class UploadDocumentForm(FlaskForm):
    """Form for uploading documents"""
    document_type = SelectField('Document Type', 
                              choices=[('passport', 'Passport'), ('pancard', 'PAN Card')],
                              validators=[DataRequired()])
    
    # Fields for passport
    id_proof = FileField('ID Proof', 
                       validators=[FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Images and PDFs only!')])
    photo = FileField('Photo', 
                    validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    address_proof = FileField('Address Proof', 
                           validators=[FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Images and PDFs only!')])
    dob_proof = FileField('Date of Birth Proof', 
                        validators=[FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Images and PDFs only!')])
    
    # Fields for PAN Card
    pan_id_proof = FileField('ID Proof', 
                          validators=[FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Images and PDFs only!')])
    pan_photo = FileField('Photo', 
                       validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    pan_address_proof = FileField('Address Proof', 
                              validators=[FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Images and PDFs only!')])
    pan_signature = FileField('Signature', 
                           validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    
    submit = SubmitField('Upload Documents')
