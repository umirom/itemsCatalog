# 1. Configuration code

# imports

import sys
    #functions and variables to manipulate the runtime environment
    
from sqlalchemy import Column, ForeignKey, Integer, String
    #needed to write mapping code
    
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship
    #to create foreign-key-relations
    
from sqlalchemy import create_engine
    #will be used inside config code at the end of file
    
# Create instance of declarative base

Base = declarative_base()
#Declarative base lets SQLAlchemy know that our SQL-classes correspond to DB tables

#####more config code at end of file######

# 2./3./4. Classes / Tables / Mappers
# One class for each DB table - contains table representation
# all classes inherit from Base
# 5. Serialize function to send JSON objects in serializable format

class User(Base):
    
    # table definition:
    __tablename__ = 'user'
    
    # mappers for 'user':
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    
class Category(Base):
    
    #table definition:
    __tablename__ = 'category'
    
    #mappers for 'category':
    name = Column(String(100), nullable=False)
    description = Column(String(400))
    id = Column(Integer, primary_key=True)
    
    @property
    def serialize(self):

        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
        }

class Recipe(Base):
    
    #table definition:
    __tablename__ = 'recipe'

    #mappers for 'recipe'
    name = Column(String(100), nullable=False)
    description = Column(String(400))
    instruction = Column(String(2000), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    #created_on = Column(String(50))
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    
    @property
    def serialize(self):

        return {
            'name': self.name,
            'description': self.description,
            'instruction':self.instruction,
            'user_id': self.user_id,
            'id': self.id,
            'category_id': self.category_id
        }
    
# 6. Configuration code at end of file

engine = create_engine('sqlite:///recipedatabasewithusers.db')
Base.metadata.create_all(engine)
    #adds classes to the database