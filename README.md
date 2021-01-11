# CourseAllocation
A system for course allocation

## Environment Create
Conda should be installed first

`conda env create -f environment.yml`

## Activate the environment
`conda activate cl`

## Create DB
If you wanna reinitialize the app, you can delete the previous database, and create a new one by `flask fab create-db`

## Start
Use `python app.py` to start, and you can edit it by deleting `debug=True` to implement it officially.

#Setting
In `config.py`, you can change some setting, like the admin user and style of the system.
