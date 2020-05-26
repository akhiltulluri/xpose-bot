## Installation Insructions

### Pre-requisites
* Python v3.8.0+
* Git

### Installing Python3.8 (For Ubuntu 18.04)
Run the following as root/user with sudo access
* ```sudo apt update```
* ```sudo apt install software-properties-common```
Add the deadsnakes PPA to your system’s sources list:
* ```sudo add-apt-repository ppa:deadsnakes/ppa```
Once it's installed, install python3.8
* ```sudo apt install python3.8```

### Installing Python3.8 (For Ubuntu 20.04)
Ubuntu 20.04 is what we currently use to host the bot. 
* ```sudo apt update```
* ```sudo apt -y upgrade```
* ```python3 -v```
Returns 3.8.x (Ubuntu 20.04 gets python3.8 pre installed.)

### Installing pip
Run the following to install pip:
* ```sudo apt install python3-pip ```

### Basic Config
* Copy `config.py.example` and create a new file `config.py` and fill in all the  credentials

### Install Python Dependencies
* Navigate to the root directory
* Run `python3 -m pip install -r requirements.txt`

## Running the Bot
Start a tmux session using `tmux` and run the following:
* `python3 bot.py`

## Adding a new league Ban List
To add a ban list of any other league, the only file you would want to edit is `cogs/bancheck.py`. 
Check out the existing league's code to understand how to add a new one

### Authors
* Akhil