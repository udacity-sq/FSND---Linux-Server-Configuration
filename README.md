# Launching the Catalog Application using Amazon Lightsail
This final project for the FSND requires configuring an instance of Linux Server using the Amazon AWS Platform Lightsail. There are two major steps
to perform to successfully launcing the applicaiton.

* Creating and Setting up a Linux Server Instance
* Installing and configuring the necessary tools/libraries - python, postgresql, etc.


# Creating and Setting up a linux Server Instance:

## Get your Server:
The first step is to create an account with Amazon and get an instance of lightsail running. Follow instructions provided [here](https://classroom.udacity.com/nanodegrees/nd004/parts/ab002e9a-b26c-43a4-8460-dc4c4b11c379/modules/357367901175462/lessons/3573679011239847/concepts/c4cbd3f2-9adb-45d4-8eaf-b5fc89cc606e)

The Public IP for the account is: 18.219.168.254  

Public URL: http://18.219.168.254.xip.io  

## Connect to your server and secure it:

Download the .pem file from lightsail account and place it in the .ssh directory of your local machine.  
From your local machine open a terminal and enter the command:  
```ssh -i ~/.ssh/AWSKey.pem ubuntu@18.219.168.254```  
Once connected type ```sudu su -``` to login as root user.  

Update all currently install packages:
* ```sudo apt-get update```  
* ```sudo apt-get upgrade```  

## Create a new user named grader and setup permissions
Type the following commands:  
* ```sudo adduser grader``` - creates a new user named grader  
* ```sudo nano /etc/sudoers.d/grader``` - create a new file to add permissions for grader  
* ```grader ALL=(ALL:ALL) ALL``` -grants grader sudo permissions  

In order to login as grader key-pair encryption needs to be setup:  
On the local machine open a new terminal and type: ```ssh-keygen -f ~/.ssh/udacity_key.rsa```. Add a password and save.  
Now type: ```cat ~/.ssh/udacity_key.rsa.pub``` to read the public key. This key will need to copy/pasted over on the grader account.  

In the AWS lightsails instance terminal type the following:  
* ```cd /home/grader``` - move to the grader directory  
* ```mkdir .ssh``` - create a new directory to store the public key  
* ```touch .ssh/authorized_keys``` - create an empty file  
* ```nano .ssh/authorized_keys``` - opens the empty file. Now paste the contents of the public key here and save/close.  
* ```sudo chmod 700 /home/grader/.ssh``` - change the permissions for grader  
* ```sudo chmod 644 /home/grader/.ssh/authorized_keys```  
* ```sudo chown -R grader:grader /home/grader/.ssh``` - change the owner from root to grader  
* ```sudo service ssh restart``` - since the changes have been made restart the ssh service   
disconnect from Lightsails server & log back in using the grader account:  
* ```ssh -i ~/.ssh/udacity_key.rsa grader@18.219.168.254```  
Follow the next few steps to secure the server:  
* ```sudo nano /etc/ssh/sshd_config```  
Update the following lines:  
* PasswordAuthentication ```no```  
* port ```2200``` - update port with new value  
* PermitRootLogin ```no```  
* ```sudo service ssh restart```   

Finally we need to configure Firewall:  
* ```sudo ufw allow 2200/tcp```  
* ```sudo ufw allow 80/tcp```  
* ```sudo ufw allow 123/udp```  
* ```sudo ufw enable```  

Change the timezone to UTC
* ```sudo dpkg-reconfigure tzdata```   

The steps above conclude setting up the linux server instance with grader account setup.

## Install, Configure & Launch the Application

### Install and configure Apache:
* ```sudo apt-get install apache2```  
We can test to ensure that Apache has been installed correctly by going to public ip page and seeing the Apache2 Ubuntu page

Since the Catalog Application was built using python3 we need to install the Python 3 mod_wsgi package
* ```sudo apt-get install libapache2-mod-wsgi-py3```
* ```sudo en2smod wsgi``` - Enables wsgi  
We also need to disable the default Apache page ```sudo a2dissite 000-default``` ```sudo service apache2 reload```

### Install git and clone the Catalog App

* ```sudo apt-get install git``` - install git
* ```cd /var/www```
* ```sudo mkdir catalog``` - this creates the file structure similar to Digital Ocean Tutorial (see resources).
* ```sudo chown -R grader:grader catalog``` - changes owner to grader for the catalog folder
* ```cd /catalog```
* Clone the github repository ```git clone https://github.com/udacity-sq/Catalog-Application.git catalog```
Now we need to make some changes to the cloned catalog files:
* ```cd catalog``` to enter /var/www/catalog/catalog
* Rename the Application.py file to __init__.py ```sudo mv Application.py __init__.py```
* quite a few lines had to be modified in __init__.py file and they can be viewed from the included modified __init__.py file. Comments are added
for clarity where changes were required. 

### Install and configure the Virtual Environment
* ```sudo apt-get install python3-pip``` - Installs pip
* ```sudo apt-get install python-virtualenv```
* ```cd /var/www/catalog/catalog```
* ```sudo virtualenv -p python3 venv3```
* ```sudo chown -R grader:grader venv3```
Now activate the virtual environment
* ```. venv3/bin/activate```
Time to install project dependencies:
* ```pip intsall flask``` ```pip install sqlalchemy``` ```pip install requests``` ```pip install --upgrade oauth2client```  
```sudo apt-get install libpq-dev``` ```pip install psycopg2``` and the rest. 
Once the dependencies are installed check to ensure that the __init__.py file works without any issues:
* ```python3 __init__.py``` - fix any issues in the code till file works
Close out the virtual environment
* ```deactivate```

### Setup the Flask Application
* First we need to create catalog.wsgi file ```sudo nano /var/www/catalog/catalog.wsgi```
```
#!/usr/bin/python

activate_this = '/var/www/catalog/catalog/venv3/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/var/www/catalog/")

from catalog import app as application
application.secret_key = "super_secret_key"
``` 
* Finally restart Apache ```sudo service apache2 restart```

For the section below credit is due to user: fokaskostas(see resrouces section below). I couldn't find a way to better explain this section. 
### Setting up and enabling the virtual host
* Add the following line in /etc/apache2/mods-enabled/wsgi.conf file to use Python 3: ```#WSGIPythonPath directory|directory-1:directory-2:...```
```WSGIPythonPath /var/www/catalog/catalog/venv3/lib/python3.5/site-packages```
* Create /etc/apache2/sites-available/catalog.conf and add the following lines to configure the virtual host:
```
<VirtualHost *:80>
                ServerName mywebsite.com
                ServerAdmin admin@mywebsite.com
                #location of the catalog.wsgi file
                WSGIScriptAlias / /var/www/catalog/catalog.wsgi
                #Allow Apache to serve the WSGI app from our catalog directory
                <Directory /var/www/catalog/catalog/>
                        Order allow,deny
                        Allow from all
                #Allow Apache to deploy static content
                </Directory>
                Alias /static /var/www/catalog/catalog/static
                <Directory /var/www/catalog/catalog/static/>
                        Order allow,deny
                        Allow from all
                </Directory>
                ErrorLog ${APACHE_LOG_DIR}/error.log
                LogLevel warn
                CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```
* Now to enable the catalog application ```sudo a2ensite catalog```
* Finally restart Apache ```sudo service restart apache2 reload```

### Install and configure PostgreSQL
The database used for the Catalog project is PostgreSQL DB. We now need to install & configure the database.
* ```sudo apt-get install postgresql``` 
* ```sudo su - postgres``` - login as user postgres  
* ```psql```  
* ```CREATE USER catalog WITH PASSWORD 'catalog';```  
* ```ALTER USER catalog CREATEDB;```  
* ```CREATE DATABASE catalog WITH OWNER catalog;```
* ```\c catalog``` - connect to database catalog
* ```REVOKE ALL ON SCHEMA public FROM public;```
* ```GRANT ALL ON SCHEMA public TO catalog;```
* ```\q``` - exit catalog database
* ```exit```
Now we need to update the __init__.py, database_setup.py and createDbCatalog.py files with the following line:
```create_engine('postgresql://catalog:catalog@localhost/catalog')```
In order to create and populate the Catalog database run the following commands:
* ```cd /var/www/catalog/catalog```
* ```.venv3/bin/activate```
* ```python database_setup.py```
* ```python createDbCatalog.py```. A message should display that the database has been popluated.
* ```deactivate``` - closes the virutal environment

### Last step is to configure Google Login and Authentication
* Login to the [Google Cloud Platform](https://console.cloud.google.com/)
* Find the APIs->Credentials page and edit the Catalog App
* Under Authorized Javascript Origins, redirect URIs add ```http://18.219.168.254.xip.io```
* Also under Authroized redirect URIs add ```http://18.219.168.254.xip.io/gconnect``` ```http://18.219.168.254.xip.io/login``` ```http://18.219.168.254.xip.io/disconnect```
Now download a copy of the client_secrets.json and copy contents. Then paste the contents in the ```cd /var/www/catalog/catalog/client_secrts.json```. 
* ```sudo service apache2 restart```
* The site is now live at [http://18.219.168.254.xip.io](http://18.219.168.254.xip.io)

### General Debugging Tips:
There were plenty of things that can go wrong and did go wrong for me. Ensure the following:
* Install the same version of python as your codebase. 
* Check to see that the code runs fine in the virtual evnironment.
* The following command is your best friend ```sudo tail /var/log/apache2/error.log```. The apache2 error log really helps to debug.
* Persistance pays dividends! Look for similar issues other users have faced. Review the Udacity forums and don't forget to reach out to your mentor.


# Resources:
* Digital Oceans - [How to Deploy A Flask Application on an Ubuntu VPS](https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps)
* Udacity Forums - [Discussion Forum](https://discussions.udacity.com/)
* Git Repository - [callforsky/udacity-linux-configuration](https://github.com/callforsky/udacity-linux-configuration/blob/master/README.md)
* Git Repository - [rrjoson/udacity-linux-server-configuration](https://github.com/rrjoson/udacity-linux-server-configuration/blob/master/README.md)
* Git Repository - [fokaskostas/Linux-Server-Configuration](https://github.com/fokaskostas/Linux-Server-Configuration)
* Git Repository - [boisalai/udacity-linux-server-configuration](https://github.com/boisalai/udacity-linux-server-configuration)
* Stackoverflow  - [Flask ImportErrorL No Module Named Flask](https://stackoverflow.com/questions/31252791/flask-importerror-no-module-named-flask/44690276)
* Askubuntu.com - [Apache not able to restart](https://askubuntu.com/questions/629995/apache-not-able-to-restart)
* 1&1 Interner Inc. - [How to fix 500 internal server error](https://www.1and1.com/cloud-community/learn/web-server/server-management/how-to-fix-http-error-code-500-internal-server-error/)
