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
import csv

s = Service('/usr/bin/safaridriver')
options = Options()
driver = webdriver.Safari(service=s, options=options)
wait = WebDriverWait(driver, 15)
clickable = ec.element_to_be_clickable
Login_URL = 'https://gsx2.apple.com'

def login():
## This function initiatse the actual attempt to login to GSX. It first checks if a text file with login credentials is present.
## If it is, it will input username and password line by line. If it is not, then it will create one by asking user to enter it into terminal.
## It will then forward that to the username ang login fields, and then start the process for dealing with 2factor code retrieval. 
## Very rudimentary but given that this is meant to run locally, its plenty for now. In the future, incorporating far better credential
## management would be nice.

    logging.info("Attempting to login to GSX")
    if os.path.isfile('/Users/'+user+'/Desktop/Login-Info.txt'): 
        username = linecache.getline('/Users/'+user+'/Desktop/Login-Info.txt', 1) 
        password = linecache.getline('/Users/'+user+'/Desktop/Login-Info.txt', 2)
    else:
        logging.warning('NO LOGIN FILE FOUND. ENTER CREDENTIALS TO CREATE ONE')
        with open('/Users/'+user+'/Desktop/Login-Info.txt', 'a') as f:
            f.write(str(input('GSX Username ---> '))+"\n")
            f.write(str(input('GSX Password ---> ')))
            username = linecache.getline('/Users/'+user+'/Desktop/Login-Info.txt', 1)
            password = linecache.getline('/Users/'+user+'/Desktop/Login-Info.txt', 2)

            # THIS PROCESS FAILS FOR NOW, clicking on terminal will de-select the AppleID field in Safari and process fails. Work on this later. 

    driver.get(Login_URL)
    sleep(2)    
    wait.until(ec.frame_to_be_available_and_switch_to_it((By.ID, "aid-auth-widget-iFrame")))  # wait for animations in iframe
    sleep(1) 
    wait.until(clickable((By.ID, "account_name_text_field"))).send_keys(username, Keys.RETURN)
    sleep(1)
    wait.until(clickable((By.ID, "password_text_field"))).send_keys(password, Keys.RETURN)
    sleep(2)
    two_factor_auto()   #Initiates the automated 2FA stuff. if no 2FA is needed itll skip from within this function. 


def two_factor_auto():  
    if len(driver.find_elements(By.ID, 'char0')) > 0:
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
        sleep(2) 
        if len(driver.find_elements(By.XPATH, '//*[starts-with(@id, "trust-browser-")]')) > 0:  #If a trust browser button is found, clicks it. Totally useless so far, maybe it works one day
            driver.find_element(By.XPATH, '//*[starts-with(@id, "trust-browser-")]').send_keys(Keys.SPACE)
    else:
        print("Skipping 2FA, not needed this time") #For the rare time that it actually saves login session for webdriver for once


def two_factor_manual():
    signal(SIGALRM, lambda a, b: 1 / 0) #Not 100% sure how this works but it creates a thing to trigger some error
    try:
        alarm(300)
        logging.warning("Automated Trusted Device Code failed. Sending SMS instead. 5 minute timer started!")
        wait.until(clickable((By.ID, 'no-trstd-device-pop'))).send_keys(Keys.RETURN)
        sleep(1) 
        wait.until(clickable((By.ID, 'use-phone-link'))).send_keys(Keys.RETURN) 
        twofa = two_factor_input()
        for index, number in enumerate(twofa):
            driver.find_element(By.CSS_SELECTOR, "input[data-index='{}']".format(index)).send_keys(number)  #once again, no clue how it works ,not my code. 
        alarm(0)    #Resets alarm trigger so it doesnt go off later on
    except ZeroDivisionError:
        logging.critical(" 5min timer for SMS 2FA expired. Exiting application")
        exit()


def two_factor_input():   
## This function just takes the 6 digit 2FA code entered into terminal and forwards it. Has basic error checking for long/short digits and non-digits

    good2_fa = 0
    while good2_fa != 1:
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


def remember_me():     
## Clicks Remember Me button on login screen. hasnt really been useful so far but codes here for future use i guess

    checked = driver.find_element(By.XPATH, '//*[@id="remember-me"]').get_property("checked")
    if checked != 'True':
        wait.until(ec.element_to_be_clickable((By.ID, "remember-me"))).send_keys(Keys.SPACE)
        sleep(1)

################################################### MAIN SCRIPT ########################################################

if __name__ == '__main__':
## Main script will first check what args are provided to decide which part list to use. It then starts login process,
## followed by looping through every part# in the list, pulling all their info, and outputting that to a CSV. 
## There is checking for substituted parts, non-available/error parts, as well as basic management of GSX errors given how unreliable the site is. 
## This part needs a lot more error checking for GSX. SOme errors to deal with in the future are at the bottom of the script

    pwd=os.getcwd()
    user=os.getlogin()
    args = sys.argv
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        if os.path.isfile(pwd+"/Part-List-Debug.txt"): 
            text_partlist = open(pwd+"/Part-List-Debug.txt", "r")
        else:
            logging.warning('PART LIST FINE NOT FOUND')
            exit()
    elif len(sys.argv) > 1 and sys.argv[1] == "dev":
        if os.path.isfile(pwd+"/Part-List-Dev.txt"): 
            text_partlist = open(pwd+"/Part-List-Dev.txt", "r")
        else:
            logging.warning('PART LIST FINE NOT FOUND')
            exit()
    elif len(sys.argv) < 2:
        if os.path.isfile(pwd+"/Part-List-Full.txt"): 
            text_partlist = open(pwd+"/Part-List-Full.txt", "r")
        else:
            logging.warning('PART LIST FINE NOT FOUND')
            exit()

    login() 
    logging.info("Successfully logged in")
    sleep(5) 

    part_list = []
    # Maintaining this fields list is very important. the python csv module uses it to auto-place data in correct column!
    fields = ["Part",                    #0
              "Substituted To",          #1
              "Description",             #2
              "Stock Price",             #3
              "Exchange Price",          #4
              "Battery Only Price",      #5
              "Part Required for Repair",#6
              "Add On Price",            #7 
              'Damage Covered by AC+',   #8
              "Labor Tier",              #9
              "Where Used"               #10
            ]
    # These fields are skipped because theyre garbage, but can always be readded above if needed
    skip = ["EEE Code","Part Type"]

    for part in text_partlist: 
        if re.match('^# ', part):
            part_info = {fields[0]: part[2:]}
        elif re.match('^##', part):  
            continue
        else:
            driver.get(Login_URL + "/part/" + part)
            sleep(2)
            try:
                part_info = {}
                driver.find_element(By.XPATH, '//*[@class="static-row-content"]')
            except NoSuchElementException: 
                    logging.warning('-------- ' + part.replace('\n','') + ' INVALID PART! IS IT AVAILABLE? CHECK MANUALLY, SKIPPING ITEM --------')
                    part_info = {fields[0]: part, fields[2]: 'Invalid Part. Either part is no longer unavailable, or GSX shit itself.'}
            else:
                for el in driver.find_elements(By.XPATH, '//*[@class="static-row"]'):
                        if el.find_element(By.XPATH, './child::*').text in skip:
                            continue
                        part_info[str(el.find_element(By.XPATH, './child::*').text).strip().rstrip('\n')] = str(el.find_element(By.XPATH, './div/child::*').text).strip().replace('CAD ','')
                        if fields[10] in part_info:
                            format = str(part_info.get(fields[10])).split(')')
                            part_info[fields[10]] = ")\n".join(format)
        part_list.append(part_info)

            
    # ValueError: dict contains fields not in fieldnames: 

    with open('test.csv', 'a', newline='', encoding='utf-8') as csv_build:
        writer = csv.DictWriter(csv_build, fieldnames=fields)
        writer.writeheader()
        writer.writerows(part_list)

    driver.get(Login_URL + "/signoutall")   #signoutall to help combat unnecessary Multiple Session complaints if this ever crashes or signed in too many times on other systems
    driver.quit()
    exit()

# https://gsx2.apple.com/apperror?traceId=POOPY Application Exception, Sign-in Button
# Multiple Sessions = //*[@id="copy-clip-btn"] for End All Sessions button
# Invalid parts selected =  //*[@id="mainView"]/div[1]  = <div class="serviceMessage">Invalid parts selected</div>
# Invalid JSON = //*[@id="mainView"]/div[1]
                    
