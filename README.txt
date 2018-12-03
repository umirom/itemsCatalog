Project description

This project realizes a CURD database application to let users access a collection of cooking recipes online. 
Anyone can browse through recipes that have been added by other users. 
If a user logs in with their Google+ account, they can add recipes to their collection. 
Logged-in users can edit and delete recipes that they have added, but only view recipes added by others.

The application is implemented with the Python framework "Flask". 
The implementation of Google+ OAuth enables secure web authentification.

----------------------------------------------------------------------------------

Instructions to run the project:

1. Install VirtualBox and Vagrant
2. Navigate to the directory where the Vagrant files are stored with git bash
3. Launch Vagrant VM with the commands "vagrant up", then "vagrant ssh" in git bash
4. When Vagrant VM is running, navigate to the directory "item-catalog"
5. Set up the database by running "python database_setup.py" in git bash
6. To populate the database with some dummy data, run "python justsomerecipes.py" in git bash
7. Launch the project by running "python recipes.py" in git bash
8. Navigate to http://localhost:5000 in your web browser to start the application
9. As an unauthorized user, you can browse the recipes in the database
10. If you log in to the application with a Google+ account, you can create new recipes and update and delete recipes that have been created by you.