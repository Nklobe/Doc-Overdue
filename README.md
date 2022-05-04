<img src="LOGOWT.png">

# Doc-Overdue

A Bachelor Degree thesis project:
Doc-Overdue scans your server and compiles a report of what is installed, what configuration files have been modified and what those modifications are. 
The script is tested and built for Ubuntu 20.04 ATM

## Features

The best summary of the project is the research question:

"To which extent can changes made to system-wide configuration files in Linux systems since their initial installation identified and extracted for further processing by human system administrators or automated configuration management tools?"

TL:DR it finds all configuration files and checks if they have been changed.
This will give an overview of the system.

## Motivation

To help administrators find changes made to a system as soon as possible

## Requirements

Requirements for the script to work:

+ A moderatly modern Debian system aka Debian/Ubuntu/Mint/etc with Python 3.x

+ [Python3](https://facebook.github.io/react/)

+ [Sphinx](https://facebook.github.io/react/)

+ An internet connection



## Installation or Getting Started

**Download and install Sphinx with**

    sudo apt install python3-sphinx

**Clone the repository and start Doc-Overdue**

	git clone https://github.com/Nklobe/Doc-Overdue
    cd Doc-Overdue
    Python3 DocOverdue.py

**Configuration**

There are a few configuration alternatives available inside the script itself:

    debugging = False
    If debugging is set to true, it will show more of the output helping in debugging the application


    shortrun = False  # only scan 100 files as a small test
    Shortrun is another debugging alternative that only scans the first 50 files in /etc making a much shorter 
    test. This is only useful if you need to debug and save time on running the script.


## Usage

Once the script is run it produces a website built in Sphinx  
The website is available under /Doc-Overdue/build/html/index.html  

If you want to, you can run a small built in debug webserver in python exposing the site  
by executing this command  

         python3 -m http.server  

Access the website with [Computers IP]:8000/build/html/index.html  
  
OBS! The webserver MUST be started in the root of the project AKA the Doc-Overdue folder  
This to garantuee that all needed files are included! OBS!  
  
There is a compressed version of the report "/Doc-Overdue/build/html/Doc-Overdue-Html.tar.gz"    
This can be moved incase you cant view the site or if you want it for documentation.     
This file is also downloadable under the section "Downloadable version" on the Sphinx generated site


## Reference

[Ref to article]

## License

A short snippet describing the license ([MIT](http://opensource.org/licenses/mit-license.php), [Apache](http://opensource.org/licenses/Apache-2.0), etc.)
