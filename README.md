<img src="LOGOWT.png">

# Doc-Overdue

A Bachelor Degree thesis project:
Doc-Overdue scans your server and compiles a report of what is installed, what configuration files have been modified,  and what those modifications are. 


## Features

The best summary of the project is the research question:

"To what extent can changes made to system-wide configuration files in Linux systems since their initial installation be identified and extracted for further processing by human system administrators or automated configuration management tools?"

TL:DR it finds all configuration files and checks if they have been changed.
This will give an overview of the system.

The script checks for a reference file in the APT repository and if found the file is compared to the local file.  
If a change if found a diff-document is produced and is available via the report site created.  
The files that lack a reference file is run through a collection of tests to help determine if the file is of relevance.  
These tests are:  
* In DPKG info: Searches through all files under /var/lib/dpkg/info/ for mention of the file  
* In Standard Files: Uses the files under 'StandardFiles' that contains files that exist on newly installed debian/ubuntu systems,  
    if the file exists in a list, the name of that list will be printed  
* Owned by root:root : Sees if the file is owned by root, this is the standard for most auto created config files  
* Created on installation date: Check if the file was created on the same day as the system was installed  
* Unmodified since installation: Checks if the file has been modified since its creation  

## Motivation

To help administrators find changes made to a unknown system as fast as possible

## Requirements

Requirements for the script to work:

+ A moderately modern Debian based system aka Debian/Ubuntu/Mint/etc with Python 3.x

+ Python3

+ An internet connection

Compatiblity  
To find the birthdate for files a newer Linux kernel is required.   
the script still works but the creation date tests wont work.  

| Distro       | Tested             | Birthdate check    |
|--------------|--------------------|--------------------|
| Debian 9     | :heavy_check_mark: | :x:                |
| Debian 10    | :heavy_check_mark: | :x:                |
| Debian 11    | :heavy_check_mark: | :heavy_check_mark: |
| Ubuntu 16.04 | :heavy_check_mark: | :x:                |
| Ubuntu 18.04 | :heavy_check_mark: | :x:                |
| Ubuntu 20.04 | :heavy_check_mark: | :heavy_check_mark: |


## Installation or Getting Started

**Clone the repository and start Doc-Overdue**

    git clone https://github.com/Nklobe/Doc-Overdue
    cd Doc-Overdue
    python3 DocOverdue.py
    (Run as Root!)
    
    
**Configuration**

There are a few configuration alternatives available inside the script itself:

    debugging = False
    If debugging is set to true, it will show more of the output helping in debugging the application


    shortrun = False  # only scan 100 files as a small test
    Shortrun is another debugging alternative that only scans the first 50 files in /etc making a much shorter 
    test. This is only useful if you need to debug and save time on running the script.


## Usage

Once the script is run it produces a report in the form of a wewbsite
The website is available under /Doc-Overdue/html/index.html  

If you want to, you can run a small built-in debug webserver in python exposing the site  
by executing this command  

         python3 -m http.server  

Access the website with [Computers IP]:8000/html/index.html  
  
OBS! The web server MUST be started in the root of the project AKA the Doc-Overdue folder  
This is to guarantee that all needed files are included! OBS!  
  

## Reference
[Doc-Overdue Article](http://www.diva-portal.org/smash/record.jsf?dswid=-5547&pid=diva2%3A1703535&c=1&searchType=SIMPLE&language=en&query=tobias+bj%C3%B6rkdahl&af=%5B%5D&aq=%5B%5B%5D%5D&aq2=%5B%5B%5D%5D&aqe=%5B%5D&noOfRows=50&sortOrder=author_sort_asc&sortOrder2=title_sort_asc&onlyFullText=false&sf=all)
