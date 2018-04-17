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
* PassowrdAuthentication ```no```  
* port ```2200``` - update port with new value  
* PermitRoolLogin ```no```  
* ```sudo service ssh restart```   

Finally we need to configure Firewall:  
* ```sudo ufw allow 2200/tcp```  
* ```sudo ufw allow 80/tcp```  
* ```sudo ufw allow 123/udp```  
* ```sudo ufw enable```  

Change the timezone to UTC
* ```sudo dpkg-reconfigure tzdata```   

The steps above conclude setting up the linux server instance with grader account setup.

## Install, configure & Launch the Application

### Install and configure Appahe:
* ```sudo apt-get install apache2```  
We can test to ensure that Apache has been installed correctly by going to public ip page and seeing the Apache2 Ubuntu page

Since the Catalog Application was built using python3 we need to install the Python 3 mod_wsgi package
* ```udo apt-get install libapache2-mod-wsgi-py3```
* ```sudo en2smod wsgi``` - Enables wsgi  

### Install git and clone the Catalog App

* 

### Install and configure PostgreSQL
The database used for the Catalog project is PostgreSQL DB. We now need to install & configure the database.
*```sudo apt-get install postgresql``` 
*```sudo su - postgres``` - login as user postgres  
*```psql```  
*```CREATE USER catalog WITH PASSWORD 'catalog';```  
*```ALTER USER catalog CREATEDB;```  
*```CREATE DATABASE catalog WITH OWNER catalog;```
*```\c catalog``` - connect to database catalog
*```REVOKE ALL ON SCHEMA public FROM public;```
*```GRANT ALL ON SCHEMA public TO catalog;```
*```\q``` - exit catalog database
*```exit```
Now we need to update the __init__.py, database_setup.py and createDbCatalog.py files with the following line:
```create_engine('postgresql://catalog:catalog@localhost/catalog')```
In order to create and populate the Catalog database run the following commands:
*```python /var/www/catalog/catalog/database_setup.py```
*```



# Resources:
* SQL Alchemy -[Documentation](https://www.sqlalchemy.org/)
* Full Stack Foundations Course - [here](https://classroom.udacity.com/nanodegrees/nd004/parts/8d3e23e1-9ab6-47eb-b4f3-d5dc7ef27bf0/modules/348776022975462/lessons/3487760229239847/concepts/36310386700923)
* Udacity - Authentication and Authorization Course [here](https://classroom.udacity.com/courses/ud330)
* Udacity Full Stack Developer Forum - [here](https://discussions.udacity.com/c/nd004-full-stack-broadcast)
