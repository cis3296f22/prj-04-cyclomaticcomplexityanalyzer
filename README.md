# Cyclomatic Complexity Analyzer

Cyclomatic Complexity is a software metric that is used to indicate the complexity of the program.

Through this project, we will gather information through analyzing various public projects on Github,
and identify part of the code that impacts the Cyclomatic Complexity Number the most through Machine Learning.



<img width="766" alt="Screen_Shot_2022-10-20_at_2 56 29_PM" src="https://user-images.githubusercontent.com/97626684/197665715-34e22a16-06f4-40e3-81c0-12e7fc5a079b.png">

# Setup

- Fully working Database is Required to store data. We will be using MariaDB powered by AWS
- There are several Python that will be required to run and build the program successfully.
- Use of Jupyter Notebook is recommended (https://jupyter.org/)
- Full PIP requirements found [here](requirements.txt)

These are the essential python libraries that will be needed for the program. 
- [Lizard](https://github.com/terryyin/lizard/): Python Library that calculates the Cyclomatic Complexity Number for the Code.
- [Flask](https://github.com/pallets/flask): Python Framework that will be used to build API to connect with the actor and with the analyzer
- ast : Parser that will be used to parse the code
- [Pandas](https://github.com/pandas-dev/pandas) : Python Library that lets you create dataframes to store data
- [pymysql](https://github.com/PyMySQL/PyMySQL) : Python Libaray that allows you to directly send your pandas dataframe to the database. 

# How to contribute
Follow this project board to know the latest status of the project

# Road Map
- Build an API to connect with the Actor [In Progress]
- Build an API to connect between scraper & analyzer [In Progress]
- Create new code statistics 
- Analyze Code and store data into the DB
- Get efficient amount of data for the ML process
