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
import os
import pwd
import subprocess
import linecache
import re
import logging
import sys

s = Service('/usr/bin/safaridriver')
options = Options()
driver = webdriver.Safari(service=s, options=options)
wait = WebDriverWait(driver, 15)
clickable = ec.element_to_be_clickable
Login_URL = 'https://gsx2.apple.com'

def login():  # Logs into GSX automatically.
    logging.info("Attempting to login to GSX")
    if os.path.isfile('/Users/'+user+'/Desktop/Login-Info.txt'): 
        username = linecache.getline('/Users/'+user+'/Desktop/Login-Info.txt', 1)  # Gets AppleID email from local file
        password = linecache.getline('/Users/'+user+'/Desktop/Login-Info.txt', 2)   # Gets AppleID Pass from same file
    else:
        logging.warning('NO LOGIN FILE FOUND. ENTER CREDENTIALS TO CREATE ONE')
        with open('/Users/'+user+'/Desktop/Login-Info.txt', 'a') as f:
            f.write(str(input('GSX Username ---> '))+"\n")
            f.write(str(input('GSX Password ---> ')))
            username = linecache.getline('/Users/'+user+'/Desktop/Login-Info.txt', 1)  # Gets AppleID email from local file
            password = linecache.getline('/Users/'+user+'/Desktop/Login-Info.txt', 2)   # Gets AppleID Pass from same file

            # THIS PRICESS FAILS FOR NOW, clicking on terminal will de-select the AppleID field in Safari and process fails. Work on this later. 

    driver.get(Login_URL)
    sleep(2)    #Animation buffer
    wait.until(ec.frame_to_be_available_and_switch_to_it((By.ID, "aid-auth-widget-iFrame")))  # wait for animations in iframe
    sleep(1)    #Animation buffer
    wait.until(clickable((By.ID, "account_name_text_field"))).send_keys(username, Keys.RETURN)  #Enters the appleID pilled from file    
    sleep(1)    #Animation buffer
    wait.until(clickable((By.ID, "password_text_field"))).send_keys(password, Keys.RETURN)  #enters appleID's password pulled from file
    sleep(2)    #Animation buffer
    two_factor_auto()   #Initiates the automated 2FA stuff. if no 2FA is needed itll skip from within this function. 


def two_factor_auto():  # 2FA defeating method for Trusted Device
    if len(driver.find_elements(By.ID, 'char0')) > 0:   # Checks to see if the login screen has the 2FA digit boxes. Runs the AppleSCript code to grab them if it does
        logging.info("Found Trusted Device Code input box! Automated 2FA process started!")
        #the AppleSCript nonsesnse needed to detect and get the 6 special numbers from the 2FA popup box. maybe eventually can be substituted with Yubikey integration?
        as_script = '''tell application "System Events" to tell the process "FollowUpUI"    
                                     click button "Allow" of window 1
                                     delay 2
                                     set Code to (get value of static text 1 of group 1 of window 1)
                                     delay 1
                                     click button "Done" of window 1
                                     Code
                                 end tell'''
        try:
            twofa = subprocess.check_output(['osascript', '-e', as_script]).decode("utf-8").replace(" ", "").replace("\n", "")
            #Gets the 6 digit code outout from osascript and also cleans it up by decoding it and getting rid of extra blank spaces
            sleep(2)
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
    pwd=os.getcwd()
    user=os.getlogin()
    args = sys.argv
    if len(sys.argv) > 1 and sys.argv[1] == "debug":     #Opens the appropriately named list of parts. Tests if file exits first to not waste time with login
        if os.path.isfile(pwd+"/Part-List-Debug.txt"): 
            part_list = open(pwd+"/Part-List-Debug.txt", "r")
        else:
            logging.warning('PART LIST FINE NOT FOUND')
            exit()
    elif len(sys.argv) > 1 and sys.argv[1] == "dev":
        if os.path.isfile(pwd+"/Part-List-Dev.txt"): 
            part_list = open(pwd+"/Part-List-Dev.txt", "r")
        else:
            logging.warning('PART LIST FINE NOT FOUND')
            exit()
    elif len(sys.argv) < 2:
        if os.path.isfile(pwd+"/Part-List-Full.txt"): 
            part_list = open(pwd+"/Part-List-Full.txt", "r")
        else:
            logging.warning('PART LIST FINE NOT FOUND')
            exit()

    login()     #initiates login process
    logging.info("Successfully logged in")
    sleep(5)    # Sleep to account for GSX being slow sometimes

    skip_list = re.compile(r"EEE|Type|Required")  # This list is what script uses to decide what pieces of into to Skip, since some of it is useless for our purposes
    index = 0 #Sets the index count variable

    for part in part_list:     #loops through every line in the parts file
        if re.match('^# ', part): #Checks for lines starting with a pound and space, since I use that to denote Header titles. Adds it as a line to table to make it more readable
            continue
        elif re.match('^##', part):   #Skips Double pound with space lines because those are used as just sorting category titles as well as parts that script should ignore. 
            continue
        else:
            index += 1
            driver.get(Login_URL + "/part/" + part)    #Loads the URL for that specific part in GSX
            sleep(2)
            try:
                driver.find_element(By.XPATH, '//*[@class="static-row-content"]')
            except NoSuchElementException:    #if the element with part info doesnt pop up, either due to GSX being bad or due to part not existing, catches the exception, updates table with new line, moves on
                    logging.warning('-------- ' + part.replace('\n','') + ' INVALID PART! IS IT AVAILABLE? CHECK MANUALLY, SKIPPING ITEM --------')
                    continue
            else:
                for el in driver.find_elements(By.XPATH, '//*[@class="static-row"]'):    #Loops through each elements line of the part info page 
                        part_values = {}
                        part_values[str(el.find_element(By.XPATH, './child::*').text).strip().rstrip('\n')] = str(el.find_element(By.XPATH, './div/child::*').text).strip().replace('CAD ','')

#formatting = pull.split(')')    #allows the list of applicale machines to actually be a list and not one continuous string. Splits at ) and joins with newline for prettytable to parse
#where_used = ")\n".join(formatting).rstrip()
    print(part_values)
    driver.get(Login_URL + "/signoutall")   #signoutall to help combat unnecessary Multiple Session complaints if this ever crashes or signed in too many times on other systems
    driver.quit()   #Graceful shitdown of safari webdriver
    exit()

# https://gsx2.apple.com/apperror?traceId=POOPY Application Exception, Sign-in Button
# Multiple Sessions = //*[@id="copy-clip-btn"] for End All Sessions button
# Invalid parts selected =  //*[@id="mainView"]/div[1]  = <div class="serviceMessage">Invalid parts selected</div>
# Invalid JSON = //*[@id="mainView"]/div[1]
                    
