from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.safari.service import Service
from selenium.webdriver.safari.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from signal import signal, alarm, SIGALRM
from time import sleep
from prettytable import PrettyTable
import os
import pwd
import subprocess
import linecache
import re
import logging
import sys

s = Service('/usr/bin/safaridriver')    #All those Options with the .addargument stuff have done nothing so far to help keep the login session open. Is it even needed?
options = Options()
#options.add_argument('--no-sandbox')
#options.add_argument('--profile')
#options.add_argument(os.path.join(os.environ['PWD'], 'profile'))
#options.add_argument(
#    'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.1 Safari/605.1.15')
driver = webdriver.Safari(service=s, options=options)
wait = WebDriverWait(driver, 30)
clickable = ec.element_to_be_clickable
Login_URL = 'https://gsx2.apple.com'

def login():  # Logs into GSX automatically.
    logging.info("Attempting to login to GSX")
    driver.get(Login_URL)
    username = linecache.getline('/Users/'+pwd.getpwuid(os.getuid())[0]+'/Desktop/Login-Info.txt', 1)  # Gets AppleID email from lical file
    password = linecache.getline('/Users/'+pwd.getpwuid(os.getuid())[0]+'/Desktop/Login-Info.txt', 2)   # Gets AppleID Pass from same file
    sleep(2)#Animation buffer
    wait.until(ec.frame_to_be_available_and_switch_to_it((By.ID, "aid-auth-widget-iFrame")))  # wait for animations in iframe
    sleep(1)#Animation buffer
    wait.until(clickable((By.ID, "account_name_text_field"))).send_keys(username, Keys.RETURN)  #Enters the appleID pilled from file    
    sleep(1)#Animation buffer
    wait.until(clickable((By.ID, "password_text_field"))).send_keys(password, Keys.RETURN)  #enters appleID's password pulled from file
    sleep(2)    #Animation buffer
    two_factor_auto()   #Initiates the automated 2FA stuff. if no 2FA is needed itll skip from within this function. 


def two_factor_auto():  # 2FA defeating method for Trusted Device
    if len(driver.find_elements(By.ID, 'char0')) > 0:   # Checks to see if the login screen has the 2FA digit boxes. Runs the AppleSCript code to grab them if it does
        logging.info("Found Trusted Device Code input box! Automated 2FA process started!")
        #the AppleSCript nonsesnse needed to detect and get the 6 special numbers from the 2FA popup box. maybe eventually can be substituted with Yubikey integration?
        as_script = '''tell application "System Events" to tell the process "FollowUpUI"    
                                     click button "Allow" of window 1
                                     delay 1
                                     set Code to (get value of static text 1 of group 1 of window 1)
                                     delay 1
                                     click button "Done" of window 1
                                     Code
                                 end tell'''
        try:
            twofa = subprocess.check_output(['osascript', '-e', as_script]).decode("utf-8").replace(" ", "").replace("\n", "")
            #Gets the 6 digit code outout from osascript and also cleans it up by decoding it and getting rid of extra blank spaces
            sleep(1)
            try:
                for index, number in enumerate(twofa):  #This code is not from me, was pulled from someone else. not 100% sure how it works but it somehow sends each number individually
                    driver.find_element(By.CSS_SELECTOR, "input[data-index='{}']".format(index)).send_keys(number)
                    alarm(0)
            except:
                pass
        except subprocess.CalledProcessError:   #If automated 2FA process fauils for some reasin, it falls back to the SMS based one
            two_factor_manual()
        except AttributeError:
            two_factor_manual()
        sleep(2)    #time buffer so the silly animations dont break script
        if len(driver.find_elements(By.XPATH, '//*[starts-with(@id, "trust-browser-")]')) > 0:  #If a trust browser button is found, clicks it. Totally useless so far, maybe it works one day
            driver.find_element(By.XPATH, '//*[starts-with(@id, "trust-browser-")]').send_keys(Keys.SPACE)
    else:
        print("Skipping 2FA, not needed this time") #For the rare time that it actually saves login session for webdriver for once


def two_factor_manual():  # 2FA Defeating for when Auto method fails for some reason
    signal(SIGALRM, lambda a, b: 1 / 0) #Not 100% sure how this works but it creates a thing to trigger some error
    try:
        alarm(300)  #Triggers the SIGALRM error if nothing happens within 300 seconds
        logging.warning("Automated Trusted Device Code failed. Sending SMS instead. 5 minute timer started!")
        wait.until(clickable((By.ID, 'no-trstd-device-pop'))).send_keys(Keys.RETURN)    #Clicks option for no trusted device
        sleep(1)    #Animation buffer   
        wait.until(clickable((By.ID, 'use-phone-link'))).send_keys(Keys.RETURN) #Clicks option to use SMS
        twofa = two_factor_input()  #Runs stuff neeeded to input manual 2FA code into python script
        for index, number in enumerate(twofa):
            driver.find_element(By.CSS_SELECTOR, "input[data-index='{}']".format(index)).send_keys(number)  #once again, no clue how it works ,not my code. 
        alarm(0)    #Resets alarm trigger so it doesnt go off later on
    except ZeroDivisionError:
        logging.critical(" 5min timer for SMS 2FA expired. Exiting application")
        exit()


def two_factor_input():     #2FA SMS imput stage with some basic 2FA input snitation and validation
    good2_fa = 0
    while good2_fa != 1:    #Creates a loop that constantly checks the 2FA code entered to make sure it is exactly  charactes with only numbers. Returns that code if its all good
        twofa = input('::::::: SMS 6-Digit Code ---> ')
        if len(twofa) <= 5 or len(twofa) >= 7:
            logging.error("Check your 2FA Code! Either too long or too short")
        else:
            try:
                int(twofa)
                good2_fa = 1
            except ValueError:
                logging.error("Not a number entered! Try again")
    return twofa


def remember_me():      #Clicks Remember Me button on login screen. hasnt really been useful so far but codes here for future use i guess
    checked = driver.find_element(By.XPATH, '//*[@id="remember-me"]').get_property("checked")
    if checked != 'True':
        wait.until(ec.element_to_be_clickable((By.ID, "remember-me"))).send_keys(Keys.SPACE)
        sleep(1)

################################################### MAIN SCRIPT ########################################################

if __name__ == '__main__':
    args = sys.argv
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        logging.basicConfig(level=logging.debug) 
        part_list = open("./Part-List-Debug", "r")
    elif len(sys.argv) > 1 and sys.argv[1] == "dev":
        #logging.basicConfig(level=10)
        part_list = open("./Part-List-Dev", "r")
    elif len(sys.argv) < 2:
        part_list = open("./Part-List-Full", "r")    #Opens the list of parts to cycle through

    login()     #initiates login process
    logging.info("Successfully logged in")
    sleep(5)    # Sleep to account for GSX being slow sometimes

    table = PrettyTable(field_names = ["Index", "Part Number", "Part Name", "Stock Price", "Exchange Price", "Battery-Only", "Compensation", "Where Used"], align = 'l') #Creates Table header
    skip_list = re.compile(r"EEE|Type|Required")  # This list is what script uses to decide what pieces of into to Skip, since some of it is useless for our purposes
    index = 0

    for part in part_list:     #loops through every line in the parts file
        if re.match('^# ', part): #Checks for lines starting with a pound and space, since I use that to denote Header titles. Adds it as a line to table to make it more readable
            table.add_row(["-----","------",part.replace("\n","---").replace("# ","---").strip(),"------","------","------","------","------"])
        elif re.match('^## ', part):   #Skips Double pound with space lines because those are used as just sorting category titles as well as parts that script should ignore. 
            continue
        else:
            index += 1
            driver.get(Login_URL + "/part/" + part)    #Loads the URL for that specific part in GSX
            try:
                wait.until(ec.visibility_of_any_elements_located((By.XPATH, '//*[@class="static-row-content"]')))   #Waits until the element with the part info pops up. 
            except TimeoutException:    #if the element with part info doesnt pop up, either due to GSX being bad or due to part not existing, catches the exception, updates table with new line, moves on
                    logging.warning('-------- ' + part.replace('\n','') + ' TIMED OUT! IS IT AVAILABLE? CHECK MANUALLY, SKIPPING ITEM --------')
                    table.add_row([index,part.replace('\n',''),"TIMED OUT! IS IT AVAILABLE? CHECK MANUALLY","","","","",""])
                    continue
            else:   #If no part info missing, attempts to pull info
                for element in driver.find_elements(By.XPATH, '//*[@class="static-row-content"]'):    #Loops through each elements line of the part info page 
                    pull = str(element.find_element(By.XPATH, './child::*').text).strip() #Gets only the pure text from each elements line of part info page
                    if re.search("Substituted", str(element.find_element(By.XPATH, 'preceding-sibling::*').text)):    #If it sees a Substitution notice, it will add that into table and skip to next part
                        logging.warning('-------- ' + part.replace('\n','') + ' SUBSTITUTED WITH ' + pull + '! UPDATE PARTS LIST! --------')
                        table.add_row([index,part.replace('\n',''),"SUBSTITUTED WITH " + pull,"","","","",""])
                        sub_skip = True #Sets the flag for loop to decide if it should skip this item
                        break
                    elif re.search(skip_list, str(element.find_element(By.XPATH, 'preceding-sibling::*').text)):  #If the element text it pulls is contained in the skip list, it will skip it
                        logging.debug("Element text matched with Skip List entry")
                        continue
                    else:
                        sub_skip = False    #Removes the skip flag for sub stitution parts
                        # Each line below will only pull the necessary info that is pulled from each part info element item its loopin trough. Ont want part price pulled for labor tier thing, ya know?
                        if re.search("Part", str(element.find_element(By.XPATH, 'preceding-sibling::*').text)):
                            part_num = str(pull).rstrip('\n')  
                            logging.debug(part_num)
                        elif re.search("Description", str(element.find_element(By.XPATH, 'preceding-sibling::*').text)):
                            part_name = str(pull).rstrip('\n')
                            logging.debug(part_name)
                        elif re.search("Stock", str(element.find_element(By.XPATH, 'preceding-sibling::*').text)):
                            stock_price = str(pull).replace('CAD ', '').rstrip('\n')
                            logging.debug(stock_price)
                        elif re.search("Exchange", str(element.find_element(By.XPATH, 'preceding-sibling::*').text)):
                            ex_price = str(pull).replace('CAD ', '').rstrip('\n')
                            logging.debug(ex_price)
                        elif re.search("Battery", str(element.find_element(By.XPATH, 'preceding-sibling::*').text)):
                            batt_price = str(pull).replace('CAD ', '').rstrip('\n')
                            logging.debug(batt_price)
                        elif re.search("Labor", str(element.find_element(By.XPATH, 'preceding-sibling::*').text)):
                            lab_tier = str(pull).rstrip('\n')
                            logging.debug(lab_tier)
                        elif re.search("Used", str(element.find_element(By.XPATH, 'preceding-sibling::*').text)): 
                            formatting = pull.split(')')    #allows the list of applicale machines to actually be a list and not one continuous string. Splits at ) and joins with newline for prettytable to parse
                            where_used = ")\n".join(formatting).rstrip()
                            logging.debug(where_used)
                if sub_skip:    # If the above loop detects a part is substituted, it moves on to next part
                    pass
                else:
                    logging.info("Adding Part Information for " + part.strip("\n") + " to Table")
                    table.add_row([index,part_num, part_name, stock_price, ex_price, batt_price, lab_tier, where_used])   #adds all the pulled and formatted part info details to the table as a line
                    part_num = part_name = stock_price = ex_price = batt_price = lab_tier = where_used = "" # Resets all the part info variables to be blank so it doesnt duplicate garbage data into empty spots
      
    print(table)    #Prints out the partty table to terminal so it can be admired   
    driver.get(Login_URL + "/signoutall")   #signoutall to help combat unnecessary Multiple Session complaints if this ever crashes or signed in too many times on other systems
    driver.quit()   #Graceful shitdown of safari webdriver
    exit()

# https://gsx2.apple.com/apperror?traceId=POOPY Application Exception, SIgn-in Button
# Multiple Sessions = //*[@id="copy-clip-btn"] for End All Sessions button
# Invalid parts selected =  //*[@id="mainView"]/div[1]  = <div class="serviceMessage">Invalid parts selected</div>
