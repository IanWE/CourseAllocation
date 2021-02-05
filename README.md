# CourseAllocation
A system for course allocation

# Install MiniConda
`wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh`
`./Miniconda3-latest-Linux-x86_64.sh`

## Environment Create
`conda env create -f environment.yml`

## Activate the environment
`conda activate cl`

## Create DB
If you wanna reinitialize the app, you can delete the previous database, and create a new one by `flask fab create-db`

If you wanna reset the dataset, delete the `app.db` directly, and create a new one.

## Start
Use `python app.py` to start, and you can edit it by deleting `debug=True` to implement it officially.

# Setting
In `config.py`, you can change some setting, like the admin user and style of the system.

# Core Files
`run.py #start script` 
`app.db #database of system configuration and registered users` 
`app/calculation.py # this file contains the calculation code` 
`app/view.py # UI relevent` 
`app/static/ #uploaded files` 

