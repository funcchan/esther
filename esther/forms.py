from sqlalchemy.sql import exists
from flask.ext.wtf import (Form, TextField, TextAreaField, PasswordField,
                           BooleanField, SelectField, ValidationError,
                           Required, Length, Email)

from esther import bcrypt, db
from esther.models import User, PostStatus, Post

### Validators

def unique(column, message=None):
    if message is None:
        message = u'{0} is not unique.'

    def validator(form, field):
        if (field.object_data != field.data and
            db.session.query(exists().where(column == field.data)).scalar()):
            raise ValidationError(message.format(field.label.text))

    return validator

### General


class ContactForm(Form):
    name = TextField(u'Name', [Required(), Length(min=2, max=128)])
    email = TextField(u'E-mail', [Required(), Email()])
    message = TextAreaField(u'Your message', [Required()])


### Auth


class LoginForm(Form):
    email = TextField(u'E-mail', [Required(), Email()])
    password = PasswordField(u'Password', [Required()])

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None
        self.auth_failed = False

    def validate(self, *args, **kwargs):
        success = super(LoginForm, self).validate(*args, **kwargs)
        if not success:
            return success

        user = User.query.filter_by(email=self.email.data,
                                    is_active_user=True).first()

        if (user is not None and
            bcrypt.check_password_hash(user.password, self.password.data)):
            self.user = user
            return True

        self.auth_failed = True
        return False


class UserForm(Form):
    email = TextField(u'E-mail', [Required(), Email(), unique(User.email)])
    full_name = TextField(u'Full name')
    short_name = TextField(u'Short name', [Required()])
    is_admin = BooleanField(u'Is admin?')


class AddUserForm(UserForm):
    password = PasswordField(u'Password', [Required()])


### Blog


class StatusField(SelectField):
    def populate_obj(self, obj, name):
        setattr(obj, name, PostStatus.from_string(self.data))

    def process_data(self, value):
        """ If the field is being populated by a ``Post`` object, set its
        value to the field's string representation. """
        try:
            self.data = value.value
        except AttributeError:
            self.data = value


class PostForm(Form):
    title = TextField(u'Title', [Required(), Length(max=255)])
    slug = TextField(u'Slug', [Required(), Length(max=80), unique(Post.slug)])
    status = StatusField(u'Status', choices=[(v, h) for v, h in PostStatus])
    body = TextAreaField(u'Post body', [Required()])
