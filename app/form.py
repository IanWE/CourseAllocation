from flask_appbuilder.fieldwidgets import (
        BS3TextFieldWidget,
        Select2AJAXWidget,
        Select2Widget,
        )
from flask_appbuilder.upload import BS3FileUploadFieldWidget
from flask_appbuilder.forms import DynamicForm
from flask_babel import lazy_gettext as _
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    BooleanField, IntegerField, SelectField, StringField, RadioField)
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, NumberRange, Optional
from flask_babel import lazy_gettext as _
import pandas as pd
from . import utils as U
from wtforms.widgets import Select

class UploadForm(DynamicForm):
    instructor = FileField(
        _('Instructor CSV'),
        description=_('Select the Instructor CSV file to be uploaded!!!'),
        validators=[FileAllowed(['csv'], _('CSV Files Only!'))],
        #widget=BS3TextFieldWidget()
        widget = BS3FileUploadFieldWidget()
    )

    course = FileField(
        _('Course CSV'),
        description=_('Select the Course CSV file to be uploaded!!!'),
        validators=[FileAllowed(['csv'], _('CSV Files Only!'))],
        widget = BS3FileUploadFieldWidget()
        #widget=BS3TextFieldWidget()
    )
    
    sysconfig = FileField(
        _('Configuration CSV'),
        description=_('Select the Configuration CSV file to be uploaded!!!'),
        validators=[FileAllowed(['csv'], _('CSV Files Only!'))],
        widget = BS3FileUploadFieldWidget()
        #widget=BS3TextFieldWidget()
    ) 

class FillupForm(DynamicForm):
    FirstP = SelectField(
        _('First preference'),
        description=_(
            'Select your first preference of course to teach or leave it None.'),
        choices=U.choices,
        widget=Select2Widget()
        )
    SecondP = SelectField(
        _('Second preference'),
        description=_(
            'Select your second preference of course to teach or leave it None.'),
        choices=U.choices,
        widget=Select2Widget()
        )
    ThirdP = SelectField(
        _('Third preference'),
        description=_(
            'Select your third preference of course to teach or leave it None.'),
        choices=U.choices,
        widget=Select2Widget()
        )
    FourthP = SelectField(
        _('Fourth preference'),
        description=_(
            'Select your fourth preference of course to teach or leave it None.'),
        choices=U.choices,
        widget=Select2Widget()
        )
    FifthP = SelectField(
        _('Fifth preference'),
        description=_(
            'Select your fifth preference of course to teach or leave it None.'),
        choices=U.choices,
        widget=Select2Widget()
        )
    FirstN = SelectField(
        _("First unwanted course"),
        description=_(
            "Please choose your first unwanted course or leave it None"),
        choices=U.choices,
        widget=Select2Widget()
        )
    SecondN = SelectField(
        _('Second unwanted course'),
        description=_(
            'Please choose your second unwanted course or leave it None'),
        choices=U.choices,
        widget=Select2Widget()
        )
    ThirdN = SelectField(
        _('Third unwanted course'),
        description=_(
            'Please choose your third unwanted course teach or leave it None'),
        choices=U.choices,
        widget=Select2Widget()
        )
    listoffield = dict()
    #listoffield = {"FirstP":FirstP,"SecondP":SecondP,"ThirdP":ThirdP,"FourthP":FourthP,"FifthP":FifthP,"FirstN":FirstN,"SecondN":SecondN,"ThirdN":ThirdN}
    def __init__(self,*args, **kwargs):
        super(FillupForm,self).__init__(*args, **kwargs) 
        self.listoffield = {"FirstP":self.FirstP,"SecondP":self.SecondP,"ThirdP":self.ThirdP,"FourthP":self.FourthP,"FifthP":self.FifthP,"FirstN":self.FirstN,"SecondN":self.SecondN,"ThirdN":self.ThirdN}

class CalculatorForm(DynamicForm):
    Strategy = RadioField('Strategy', choices=[('s1', 'Strategy 1'), ('s2', 'Strategy 2'), ('s3', 'Strategy 3')],        
            description=_("Plan"))

class CalculatorViewForm(DynamicForm):
    Strategy = RadioField('', 
            choices=[('s', 'Start Calculation')],
            description=_("No Running Thread"))
