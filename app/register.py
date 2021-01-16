from flask_appbuilder.security.registerviews import RegisterUserDBView
from flask_appbuilder.security.registerviews import BaseRegisterUser 
from flask_appbuilder.security.sqla.manager import SecurityManager

import logging
from flask import flash, redirect, request, session, url_for
from flask_babel import lazy_gettext
from flask_appbuilder.security.forms import LoginForm_oid, RegisterUserDBForm, RegisterUserOIDForm
from flask_appbuilder import const as c
from flask_appbuilder._compat import as_unicode
from flask_appbuilder.validators import Unique
from flask_appbuilder.views import expose, PublicFormView

from wtforms import BooleanField, PasswordField, StringField
from wtforms.validators import DataRequired, Email, EqualTo
from flask_appbuilder.fieldwidgets import BS3PasswordFieldWidget, BS3TextFieldWidget
from flask_appbuilder.forms import DynamicForm
import pandas as pd
import os
from config import ADMIN

class RegisterUserDBForm(DynamicForm):
    username = StringField(
        lazy_gettext("User Name"),
        validators=[DataRequired()],
        widget=BS3TextFieldWidget(),
    )
    first_name = StringField(
        lazy_gettext("First Name"),
        #validators=[DataRequired()],
        widget=BS3TextFieldWidget(),
    )
    last_name = StringField(
        lazy_gettext("Last Name"),
        #validators=[DataRequired()],
        widget=BS3TextFieldWidget(),
    )
    email = StringField(
        lazy_gettext("Email"),
        validators=[DataRequired(), Email()],
        widget=BS3TextFieldWidget(),
    )
    password = PasswordField(
        lazy_gettext("Password"),
        description=lazy_gettext(
            "Please use a good password policy,"
            " this application does not check this for you"
        ),
        validators=[DataRequired()],
        widget=BS3PasswordFieldWidget(),
    )
    conf_password = PasswordField(
        lazy_gettext("Confirm Password"),
        description=lazy_gettext("Please rewrite the password to confirm"),
        validators=[DataRequired(),EqualTo("password", message=lazy_gettext("Passwords must match"))],
        widget=BS3PasswordFieldWidget(),
    )

class MyRegisterUserDBView(BaseRegisterUser):
    form = RegisterUserDBForm
    def add_registration(self, username, first_name, last_name ,email, password=""):
        from . import app
        register_user = self.appbuilder.sm.add_register_user(
            username, first_name, last_name, email, password
        )
        #if register_user:
        #    flash(as_unicode(self.message), "info")
        #    return register_user
        #else:
        #    flash(as_unicode(self.error_message), "danger")
        #    self.appbuilder.sm.del_register_user(register_user)
        #    return None
        reg = register_user
        flag = 1
        u = []
        if os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"],app.config["INSTRUCTOR"])):
            u = pd.read_csv(os.path.join(app.config["UPLOAD_FOLDER"],app.config["INSTRUCTOR"]))
        if reg.email==ADMIN:
            r = self.appbuilder.sm.auth_role_admin
        elif reg.email in u.email.values:# or reg.name in u.name.values: 
            r = self.appbuilder.sm.auth_user_registration_role
        else:
            flag = 0
        if flag==0 or not self.appbuilder.sm.add_user(
            username=reg.username,
            email=reg.email,
            first_name=reg.first_name,
            last_name=reg.last_name,
            role=self.appbuilder.sm.find_role(r),
            hashed_password=reg.password,
            ):
            if flag==0:
                flash(as_unicode("Your email is not in the list of valid users"), "danger")
            else:
                flash(as_unicode(self.error_message), "danger")
            self.appbuilder.sm.del_register_user(reg)
            return redirect(self.appbuilder.get_url_for_index)
        else:
            self.appbuilder.sm.del_register_user(reg)
            flash(as_unicode(self.message), "info")
            print("XXXXXXXXXXXXXXXX"+self.message)
            return self.render_template(
                self.activation_template,
                username=reg.username,
                first_name=reg.first_name,
                last_name=reg.last_name,
                appbuilder=self.appbuilder,
            )

    def form_get(self, form):
        self.add_form_unique_validations(form)

    def form_post(self, form):
        self.add_form_unique_validations(form)
        self.add_registration(
            username=form.username.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            password=form.password.data,
        )

class MySecurityManager(SecurityManager):
    registeruserdbview = MyRegisterUserDBView

