from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, Recipe, User

engine = create_engine('sqlite:///recipedatabasewithusers.db')
#Bind engine to the metadata of the Base class 
#so that the declaratives can be accessed through a DBSession instance

#einkommentieren wenn db_setup steht
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()

session = DBSession()

#Some basic categories

category1 = Category(name='Salads')
session.add(category1)
session.commit()

category2 = Category(name='Pasta')
session.add(category2)
session.commit()

category3 = Category(name='Rice Dishes')
session.add(category3)
session.commit()

category4 = Category(name='Chicken and other Poultry')
session.add(category4)
session.commit()

category5 = Category(name='Beef')
session.add(category5)
session.commit

category6 = Category(name='Desserts')
session.add(category6)
session.commit()

category7 = Category(name='Soups')
session.add(category7)
session.commit()

recipe1 = Recipe(name='Pasta Bolognese', description="Classic Italian Bolognese, perfect with Spaghetti",
                instruction="Fry onions, bacon and carrots, add the meat, add tomatoes, red wine and herbs and spices and let cook for minimun 90 minutes. Serve with Pasta", user_id=1, category_id=2)
session.add(recipe1)
session.commit()

recipe2 = Recipe(name='Risotto', description="Basic risotto recipe - add mushrooms, vegetables, bacon or whatever you like", instruction="Heat the stock. Fry the onions, add the rice, then the wine and the stock. Add whatever you like and some parmesan before serving", user_id=1, category_id=3)

session.add(recipe2)
session.commit()

user1 = User(name='Testuser', email='testuser@testdomain.org')
session.add(user1)
session.commit()

print "Added sample data!"
