## Overview
This repository contains the backend of a website for an imaginary company called **Toronto Fitness Club**. The backend was implemented in Django and uses the Django REST framework. API documentation can be found in **docs.pdf**.

## How to Run Server
To run the server, you can install Django and the required packages manually, or you can use the provided shell scripts. These scripts require you to have **virtualenv** installed. Steps for running these scripts are as follows:
  - In the directory containing all the repo files, run ```source startup.sh```. This should create and activate a virtual environment. 
  - Run ```./run.sh```
  
 Note that using the provided scripts automatically creates a superuser with email ```admin@gmail.com``` and password ``password```.
