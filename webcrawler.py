
from time import sleep, strftime
import numpy as np
from random import randint
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import smtplib
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
#Access Denied You don't have permission to access "site" on this server
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import datetime

def awardScrape(startDate,endDate,startLocation,endLocation):
    # OPEN KLM
    
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
    driver.delete_all_cookies()
    delta = datetime.timedelta(days=1)
    df_flights = pd.DataFrame()
     # START SCRAPING KLM 
    url = 'https://www.klm.com/search/offers?bookingFlow=REWARD&pax=1:0:0:0:0:0:0:0&cabinClass=ECONOMY&activeConnection=0&connections={startLocation}:C:{date}%3E{endLocation}:A'.format(
        startLocation= startLocation,date = startDate.strftime("%Y%m%d"),endLocation = endLocation)
    
    driver.get(url)
    sleep(5)    
   
    while (startDate <= endDate):
        print('starting',startDate)
        try:
            xp_popup_close = '//button[contains(@class,"cookie-banner")]'
            driver.find_elements(By.XPATH, xp_popup_close)[1].click()
            print('closing popup')
        except Exception as e:
            print('no popup')
            pass
        sleep(randint(20,25))
        #Click through classes
        class_xp = "//div[contains(@class,'select-arrow-wrapper')]"
        classButton = driver.find_element(By.XPATH,class_xp)
        classButton.click()
        sleep(10)
        classList_xp = "//mat-option[contains(@role,'listitem')]"
        classList = driver.find_elements(By.XPATH,classList_xp)
        tries = 1
        for a,e in enumerate(classList):
            
            tempList = driver.find_elements(By.XPATH,classList_xp)
            tempClassName = tempList[a].text
            print('starting',tempList[a].text)
            try:
                tempList[a].click()
                sleep(randint(15,20))   
                # Scrape Page
                print('scraping page')

                xp_flight_container = '//div[contains(@class, "itinerary-row__header")]'
                flight_containers = driver.find_elements(By.XPATH, xp_flight_container)

                for i, elements in enumerate(flight_containers):
                    #print(elements.text)
                    temp_dict = {
                        'Date': startDate.strftime("%Y%m%d"),
                        'Starting_location': startLocation,
                        'End_Location': endLocation,
                        'FlightType': tempClassName, #CHANGE!!!!
                        'Flight_Time': elements.find_elements(By.XPATH, ".//*[contains(name(),'flight-times')]")[0].text,       
                        'Flight_Details': elements.find_elements(By.XPATH, ".//*[contains(name(),'flight-operators')]")[0].text,
                        'Trip_Duration': elements.find_elements(By.XPATH, ".//*[contains(name(),'flight-duration')]")[0].text,
                        'Flight_Info': elements.find_elements(By.XPATH, ".//*[contains(name(),'flight-location')]")[0].text,
                        'Miles' : elements.find_element(By.XPATH, ".//*[contains(name(),'price')]").find_elements(By.XPATH,".//span")[0].text,
                        'Taxes_Fees' : elements.find_element(By.XPATH, ".//*[contains(name(),'price')]").find_elements(By.XPATH,".//span")[1].text,
                        'Seats_Left': elements.find_elements(By.XPATH, ".//*[contains(name(),'seats-left')]")[0].text,
                        'URL': url
                    }
                    df_temp = pd.DataFrame([temp_dict],columns = temp_dict.keys())

                    df_flights = pd.concat([df_flights,df_temp],ignore_index=True)
                print('finished',tempClassName)
                if a < len(classList)-1:
                    tempClassButton = driver.find_element(By.XPATH,class_xp)
                    tempClassButton.click()
                    sleep(10)
            except NoSuchElementException as exc:
                print(exc,'waiting....',tries)
                if tries < 4:
                    sleep(60*tries)
                    tries +=1
                    continue                    
                else:
                    return df_flights
                    raise
                
        print('finished',startDate)  
        startDate += delta
        print('changed date to',startDate)
        if startDate <= endDate:
            nextDay_xpath = "//div[contains(@class,'carousel-item') and contains(text(),{})]".format("'"+startDate.strftime("%b %d").replace(' 0',' ')+"'")
            carousel = driver.find_element(By.XPATH,nextDay_xpath)
            print(carousel.text)
            carousel.click()
            sleep(randint(20,40))
    df_flights['Trip_Duration'] = pd.to_timedelta(df_flights['Trip_Duration'].str.split(':\n').str[1].apply(lambda x: x.replace("h", ":")+':00'))
    df_flights['Miles'] = df_flights['Miles'].str.replace(' Miles','').str.replace(',','').astype('int')
    df_flights['Transfer'] = pd.np.where(df_flights['Flight_Info'].str.contains('transfer'),True,False)
    df_flights['Airport'] = pd.np.where(df_flights['Flight_Info'].str.contains('Airport change'),True,False)
    return df_flights


