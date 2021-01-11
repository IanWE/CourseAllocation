from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from wtforms.validators import DataRequired, Email, EqualTo
"""

You can use the extra Flask-AppBuilder fields and Mixin's

AuditMixin will add automatic timestamp of created and modified by who

"""
class Instructor(Model):
    id = Column(Integer, primary_key=True)
    name =  Column(String(150), unique = True, nullable=False)
    email = Column(String(64), unique=True, nullable=False)
    poc1 = Column(String(64))#preference of course
    poc2 = Column(String(64))
    poc3 = Column(String(64))
    poc4 = Column(String(64))
    poc5 = Column(String(64))
    cnt1 = Column(String(64))#course not to teach
    cnt2 = Column(String(64))
    cnt3 = Column(String(64))
    ctp12 = Column(Integer)#courses taught in the past 12 months
    ctp24 = Column(Integer)
    def __repr__(self):
        return self.name
