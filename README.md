# Cyclomatic Complexity Analyzer

Cyclomatic Complexity is a software metric that is used to indicate the complexity of the program. 

It is important for a programmer to maintain low Cyclomatic Complexity Number for their projects, since having a higher CCN provides higher chances of the code to crash. This application will help programmers see where they are during the development process.

In this project, we have created a full stack applications targeting programmers. 

Users will be able to see the live evaluation of their code and the cyclomatic complexity of each individual functions that make up a file. 


# Class Diagram
![CCA_Class_Diagram (1)](https://user-images.githubusercontent.com/112198910/204877913-a3e0fb3a-920f-4786-8e61-adc321f90350.png)

  
  First, the user will encounter the GUI of our program, which prompts them to enter a GitHub URL to a repository that they wish to analyze, then we use the class scraper to “scrape”/clone by using GitHub API the project from GitHub. Then in the main, we read the files in the local repository that we just cloned. Next, we call the lizard API, to help us analyze the code’s cyclomatic complexity number. After that, we will delete the local file and then display the result in GUI. Things that we can expect from the GUI are CCN(cyclomatic complex number) and the number of function calls that a program uses. All statists of the program and its performance in a nice and easy way which calculate in a short amount of time.

# Sequence Diagram
<img width="577" alt="Screen Shot 2022-11-30 at 6 08 13 PM" src="https://user-images.githubusercontent.com/97626684/204927371-a701b043-eb9a-43f0-ab9b-f1db6e5dceb9.png">


# Setup
- Check out the dependencies that are required to run this application [here](/Pipfile)

### How to build
- Install `pipenv` using `pip install -U pipenv`.
- Run `pipenv update` in the working directory to synchronize the dependencies in the Pipfile.
- Run `pipenv run pyinstaller -F main.py`. This will create an executable binary file at `dist/main.exe`

# How to contribute
Follow this project board to know the latest status of the project

# Running Screen
<img width="595" alt="Screen Shot 2022-11-30 at 6 12 05 PM" src="https://user-images.githubusercontent.com/97626684/204927885-43858c9c-f545-4a53-a57f-403bedf061f2.png">

- initial screen when launched

<img width="597" alt="Screen Shot 2022-11-30 at 6 12 33 PM" src="https://user-images.githubusercontent.com/97626684/204927946-4095fb83-0e63-474e-8316-56ac6e595e75.png">
- insert the github repo, and click enter.
- Analysis process will start and the result will appear on the screen.

<img width="558" alt="Screen Shot 2022-11-30 at 6 14 13 PM" src="https://user-images.githubusercontent.com/97626684/204928153-2845b428-ad38-4c9e-ae99-8cd922f1d4b3.png">
- by clicking the 'save' button, it allows the users to download the results into a csv file.
