# Project Name
Put here a short paragraph describing your project. 
Adding an screenshot or a mockup of your application in action would be nice.  

![This is a screenshot.](images.png)
# How to run
Provide here instructions on how to use your application.   
- Download the latest binary from the Release section on the right on GitHub.  
- On the command line uncompress using
```
tar -xzf  
```
- On the command line run with
```
./hello
```
- You will see Hello World! on your terminal. 

# How to contribute
Follow this project board to know the latest status of the project: [http://...]([http://...])  

### How to build
- Install Python. Building the project requires at least Python 3.7.
- Install `pipenv` using `pip install -U pipenv`.
- Run `pipenv update` in the working directory to synchronize the dependencies in the Pipfile.
- Run `pipenv shell` in the working directory to create a subshell in the project's virtualenv.
- Run `pyinstaller -F main.py` in the subshell. This will create an executable binary file at `dist/main.exe`
