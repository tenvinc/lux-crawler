# Lux Crawler
## Installation instructions
This version of Lux Crawler uses Firefox as its WebDriver so the corresponding driver needs to be installed. Feel free to change this webdriver to any driver (Chrome, Edge, Safari) if you so wish to. 
**Note that the instructions are meant for Ubuntu 18.04 LTS.**

Below lists the steps needed to setup the environment for Lux Crawler to work:
1. Install driver for Firefox ([Geckodriver](https://github.com/mozilla/geckodriver/releases))
2. Setup virtual environment for python
```
virtualenv -p python3.6 lc_venv
```  
3. Install relevant packages found in requirements.txt
```
source lc_venv/bin/activate
pip install -r requirements.txt
```
4. Run the crawler python file
```
sudo chmod +x crawler.py
python3 crawler.py
```