# Wall-Street

If you're not under Apple, an AASP, or something similar under Apples repair and warranty system, this will be useless for you, just FYI.  

This is an automated python-based web crawler script to loop through a given set of part lists, pull all relevant part info from GSX, and format them into a table for easy viewing.
It has some error-handling for GSX's stupidity (though not enough yet), it can detect substituted parts, or unavailable parts. 

THIS IS STILL VERY EARLY STAGES! use at your own risk! very incomplete, BUT works enough to run

TODO:
- Export pulled data to CSV
- Automatically install all necessary python modules and CLI tools at first run.
- Use a better system for storing login credentials locally (atm just a text file, eventually something more secure and robust)
- Ability to get output to either CSV or Terminal based on given args
- Automatically run it every morning and spit out any price updates from previous days CSV data (since GSX isnt smart enough to do that for some reason)
- Maybe allow user to specify automatic price update check rate?
- Ability to formulate graphs for price history based on some given timeframe (1d, 1w, 1m, 6m, 1y)
- Ability to automatically add new machines parts to the list
- Ability to get more specific with which lists to use (ex. only macbook airs, only fans, only for 2018 models, etc)
- Ability to sort CLI-based table by a vertain column
- Ability to calculate recommended part prices based on stores specified part margin %. Maybe per-category margins eventually?
- Potentially a local SQL database instead of bunch of CSV's?
- Potentially find a way to integrate with LightSpeed database to automatically update part costs and if a part is current? no clue if possible
