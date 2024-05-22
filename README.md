# Twitch-Chat

### Requirements

*To run the code you will need to install Python.*
*Additionally, you will need to install the following python module using pip:* 

* python -m pip install keyboard


### How to use

Once Python is set up, simply change the "TWITCH_CHANNEL" in [TwitchChat_Settings.py](TwitchChat_Settings.py), and you'll be ready to go.

If you also want to get the User ID, change the "GetUserID" to 'True' and set up your Environmental Variables with your tokens.


To run the script, there are 2 variants:
* go into your terminal, go to the path you are in ("cd {location}") and run "python TwitchChat_Settings.py"
* Or if you have a Python runner extension in VSCode, just run TwitchChat_Settings.py.

Information for running:
* The Killswitch only works if you run the terminal as Administrator or use a Debugger.
+ If you use a Debugger, the colorization won't work due to how the Output in VSCode works.