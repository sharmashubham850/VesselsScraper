import requests
from random import randint, uniform
from time import sleep
from winsound import Beep
import pandas as pd
from twilio.rest import Client
from bs4 import BeautifulSoup
from collections import defaultdict


vessels_url = 'https://www.vesseltracker.com/en/vessels.html'
marine_traffic_url = 'https://www.marinetraffic.com/en/ais/details/ships/imo:'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'
}


# All vessels data will be stored here
ships_details = defaultdict(list)


valid_keys = ('Name', 'IMO No.', 'Type', 'Flag', 'MMSI', 'Call Sign', 'Length x Breadth(m)',
              'Deadweight', 'Year Built', 'Status', 'Draught', 'Speed recorded (Max / Average)')

# Scraps data from 'https://www.vesseltracker.com/en/vessels.html'
def vessel_tracker(page, search):
    global ships_details

    vessels = requests.get(vessels_url, params={
                           'page': page, 'search': search})
    soup = BeautifulSoup(vessels.text, 'lxml')

    results_table = soup.find(class_='results-table')
    local_IMO = []
    for row in results_table.find_all('div', class_='row'):
        vessel_div = row.find('div', class_='name-type')
        ships_details['Name'].append(vessel_div.a.text.upper())
        IMO = row.find('div', class_='imo').span.text
        ships_details['IMO No.'].append(IMO)
        local_IMO.append(IMO)
        ships_details['Type'].append(vessel_div.span.text)
        ships_details['Flag'].append(
            row.find('div', class_='flag').div.get('title'))
        ships_details['MMSI'].append(row.find('div', class_='mmsi').span.text)
        ships_details['Call Sign'].append(
            row.find('div', class_='callsign').span.text)
        ships_details['Length x Breadth(m)'].append(
            row.find('div', class_='sizes').span.text)
    
    return local_IMO


# Scraps data from 'https://www.marinetraffic.com/en/ais/details/ships/'
def marine_traffic(IMOs, headers=headers):
    global ships_details

    for IMO in IMOs:
        print('Current IMO:', IMO, end= '--')
        source = requests.get(
            marine_traffic_url + IMO, headers=headers)
        
        valid_keys1 = ('Deadweight', 'Year Built', 'Status')
        valid_keys2 = ('Draught', 'Speed recorded (Max / Average)')
        
        if not source.ok:
            code = source.status_code
            print('-Error', code, end='')
            
            for key in valid_keys1 + valid_keys2:
                ships_details[key].append('-')
                
            print('--Skipped All keys')
            continue
                
                
                
            
        soup2 = BeautifulSoup(source.text, 'lxml')

        div1 = soup2.find('div', class_='equal-height')
        div2 = soup2.find_all('table', class_='table-aftesnippet-primary')

        
        
        if not div1:
            for key in valid_keys1:
                ships_details[key].append('-')
            print('--Empty div1')
            continue
            
        else:
            got_keys1 = []
            for div in div1.find_all('div', class_='group-ib'):
                key = div.span.text.replace(': ', '')
                value = div.b.text

                if key in valid_keys1:
                    ships_details[key].append(value)
                    got_keys1.append(key)
            
            # Check for empty keys
            if len(got_keys1) < len(valid_keys1):
                for key in valid_keys1:
                    if key not in got_keys1:
                        ships_details[key].append('-')
                        print('--Empty field:', key, end='-')
        
        
        if not div2:
            for key in valid_keys2:
                ships_details[key].append('-')
            print('--Empty div2')
            continue

            
        else:
            div2 = soup2.find_all('table', class_='table-aftesnippet-primary')[-1]
            
            # Additional check if required table is not found
            if 'no-margin' in div2['class']:
                for key in valid_keys2:
                    ships_details[key].append('-')
                print('--Wrong Table(Empty keys2)')
                continue
            
            
            got_keys2 = []
            for tr in div2.find_all('tr'):
                key = tr.td.find(text=True, recursive=False)
                value = tr.b.text

                if key in valid_keys2:
                    ships_details[key].append(value)
                    got_keys2.append(key)

            # Check for empty keys
            if len(got_keys2) < len(valid_keys2):
                for key in valid_keys2:
                    if key not in got_keys2:
                        ships_details[key].append('-')
                        print('--Empty field:', key, end='-')
                        
        print('(Done)')


# Saves vessels data to Excel file using pandas dataframe
def save_data(filename):
    global ships_details
    rows = len(ships_details['IMO No.'])
    for value in ships_details.values():
        if len(value) != rows:
            Beep(500, 1200)
##            send_message(body=f'Vessel Project Update(Page {search}) - Error..Rows not equal')
            return 'Rows not Equal'
        

    try:
        df = pd.DataFrame(ships_details)
        df = df.reindex(sorted(df.columns, key=lambda x: list(ships_details.keys()).index(x)), axis=1)
        df.to_excel(filename, index=None)
        print(df.tail(10))
    except:
        Beep(500, 1200)
##        send_message(body=f"Vessel Project Update(Page {search})- Error..Inconsistent data (Pandas Error)")
        return 'Inconsistent data (Pandas Error)'

    Beep(2000, 600)
##    send_message(body=f"Vessel Project Update(Page {search})- Hurray... Data successfully exported!")
    print(f'\nData successfully saved to {filename}!')
    return



if __name__ == '__main__':
    search = input('Search Page(Alphabet): ')
    start = int(input('Start Page: '))
    end = int(input('End Page: '))
    filename = input('Excel Filename: ')

    print(f'-------------------------Starting {search}: Page ({start}-{end})-----------------------------')

    p = start
    e_count = 0
    while p <= end:

        try:
            local_IMO = vessel_tracker(page=p, search=search)
    ##        sleep(randint(1,3))
            
            marine_traffic(IMOs=local_IMO)
            
        ##    if end >= 60:
        ##        if p % 35 == 0:
        ##            send_message(body=f"Vessel Project Update(Page {search})- {p} pages done (Total {end})")
            
            
            print('\nDone with page', p)
            print()
            p += 1

        except Exception as E:
            e_count += 1
            
            print('Error:', E)
            index = (p-1) * 20
            for key in valid_keys:
                ships_details[key] = ships_details[key][:index]

            print(f"Page {p} data Rolled back")
            print(f"Retrying with page {p}")
            
            if e_count > 10:
                break
            
            sleep(6)
            
            
    print('Done with all the pages\n')

    save_data(filename=filename)
        
        
