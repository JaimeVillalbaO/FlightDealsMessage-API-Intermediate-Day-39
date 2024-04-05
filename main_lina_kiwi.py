from pprint import pprint
import requests
from datetime import datetime, timedelta
from twilio.rest import Client
import smtplib
import os

sheet_endpoint = 'https://api.sheety.co/ef48affbf9bd70ec9ed14b75b25b59c8/vuelosLina/prices'

'''obtener la info de la hoja de excel '''
response = requests.get(url=sheet_endpoint)
# print((response.text))
sheet_data = response.json()['prices']
print(sheet_data)


'''añadirle 'testing' a cada iata code que estaba en blanco inicialmente'''
# for i in sheet_data:
#     i['iataCode'] = 'TESTiNG'


'''hacer una lista de las ciudades '''
citys = [i['city'] for i in sheet_data]
# print(citys)

'''probar para modificar en la hoja de excel eliminando el testing'''
# n=2
# for i in sheet_data:    
#     sheet_response = requests.put(url=f'{sheet_endpoint}/{n}', json={'price':{'iataCode' : ''}})
#     n+=1
#     # print(sheet_response.text)
 

'''conectar con kiwi'''    
tequila_endpoint = 'https://tequila-api.kiwi.com'
API_KEY = os.environ.get('KIWI_KEY')
headers = {'apikey': API_KEY}


'''solicitar info de los codigos de las ciudad en kiwi'''
location_endpoint = f'{tequila_endpoint}/locations/query'
code_citys = []
for city in citys:
    query = {
        'term' : city, 
        'location_types' : 'city'
    }
    response = requests.get(url=location_endpoint, params=query, headers=headers)
    data = response.json()['locations']
    code_citys.append(data[0]['code'])
 
    
# '''para colocar los codigigos de las ciudades en el excel'''    
n=2
c=0
for i in sheet_data:        
    iata_code = code_citys[c]
    sheet_response = requests.put(url=f'{sheet_endpoint}/{n}', json={'price':{'iataCode' : iata_code}})
    n+=1
    c+=1
    # print(sheet_response.text)
        
        
'''buscar los vuelos en kiwi'''    
flights_endpoint = f'{tequila_endpoint}/v2/search'

today = datetime(2024,6,8)
# range_dates = today + timedelta(days=7)

today_formate = today.strftime('%d/%m/%Y')
# range_dates_formate = range_dates.strftime('%d/%m/%Y')


'''crear las listas donde va la info del mensaje de texto'''
price_updated = []
airport_from = []
airport_to = []
date_from = []
date_to = []
city_step_from = []
city_step_to = []

    
for i in range(len(code_citys)):
    
    max_stopovers = 0

    query = {
        'fly_from' : 'MDE',
        'fly_to' : code_citys[i], 
        'date_from' : today_formate, 
        'date_to' : today_formate, 
        'nights_in_dst_from' : 6, 
        'nights_in_dst_to' : 6,
        "one_for_city": 1,
        'curr' : 'COP', 
        "max_stopovers": max_stopovers,        
    }
    
    try:
        response = requests.get(url=flights_endpoint, params=query, headers=headers)
        # print(response.text)
        one_step = 'no'
        price_updated.append(response.json()['data'][0]['conversion']['COP'])
        airport_from.append(response.json()['data'][0]['flyFrom'])
        airport_to.append(response.json()['data'][0]['flyTo'])
        date_from.append(response.json()['data'][0]['local_departure'].split("T")[0])
        date_to.append(response.json()['data'][0]['route'][1]['local_departure'].split("T")[0])
        city_step_from.append('None')
        city_step_to.append('None')
        
        
        
        
        
    except :
        max_stopovers = 2
        
        query = {
            'fly_from' : 'MDE',
            'fly_to' : code_citys[i], 
            'date_from' : today_formate, 
            'date_to' : today_formate, 
            'nights_in_dst_from' : 6, 
            'nights_in_dst_to' : 6,
            "one_for_city": 1,
            'curr' : 'COP', 
            "max_stopovers": max_stopovers, 
        }
        response = requests.get(url=flights_endpoint, params=query, headers=headers)
        print(response.text)
        price_updated.append(response.json()['data'][0]['conversion']['COP'])
        airport_from.append(response.json()['data'][0]['flyFrom'])
        airport_to.append(response.json()['data'][0]['flyTo'])
        date_from.append(response.json()['data'][0]['local_departure'].split("T")[0])
        date_to.append(response.json()['data'][0]['route'][2]['local_departure'].split("T")[0])
        city_step_from.append(response.json()['data'][0]['route'][0]['cityTo'])
        city_step_to.append(response.json()['data'][0]['route'][2]['cityTo'])
        
        one_step = 'yes'
        
       
    

'''comparar los precios de kiwi con los del excel'''
price = [i['lowestPrice'] for i in sheet_data]
print(price)
print(price_updated)
account_sid = os.environ.get('ACCOUNT_ID')
auth_token = os.environ.get('AUTH_TOK')
recovery_code = os.environ.get('RECOVERY_CODE')
my_email = 'jaimevillalbaoyola@gmail.com'
password = os.environ.get('PASSWORD_EMAIL')

n=2
p=0
for i in price_updated:
    if type(price_updated[p]) != int:
        print('yes')
        continue
    elif price_updated[p] < price[p]:
        '''enviar el mensaje'''
        response = requests.put(url=f'{sheet_endpoint}/{n}', json={'price':{'lowestPrice' : price_updated[p]}} )
        
        

        if one_step == 'no':
            '''Enviar mensaje de texto por celular'''
            # client = Client(account_sid, auth_token)
            # message = client.messages\
            #     .create(
            #     body=f'Lowest Price Alert! 🚨 Only {price_updated[p]} to fly from London-{airport_from[p]} to '
            #         f'{citys[p]}-{airport_to[p]} from {date_from[p]} to {date_to[p]}.',         
            #     from_='+16592765022',
            #     to='+573215696357',
            # )
            # print(message.status)

            '''Enviar mensaje via Email'''
            with smtplib.SMTP('smtp.gmail.com', 587) as connection:
                connection.starttls() #make the conection secure
                connection.login(user=my_email, password=password)
                connection.sendmail(from_addr=my_email, 
                                    to_addrs='cryptobluewolf@gmail.com', 
                                    msg=(f'Lowest Price Alert! 🚨 Only {"{:,}".format(price_updated[p]).replace(",", ".")} £ to fly from London-{airport_from[p]} to '
                                        f'{citys[p]}-{airport_to[p]} from {(date_from[p]).strftime("%d/%m/%Y")} to {(date_to[p]).strftime("%d/%m/%Y")}.').encode('utf-8'),
                                    )

        elif one_step == 'yes': 
            '''Enviar mensaje de texto por celular'''
            # client = Client(account_sid, auth_token)
            # message = client.messages\
            #     .create(
            #     body=f'Lowest Price Alert! 🚨 Only ${price_updated[p]} to fly from London-{airport_from[p]} to '
            #         f'{citys[p]}-{airport_to[p]} from {date_from[p]} to {date_to[p]}. Flight has 1 step over, \
            #             via London-{city_step_from[p]}-{citys[p]} and {citys[p]}-{city_step_to[p]}-London.',         
            #     from_='+16592765022',
            #     to='+573215696357',
            # )
            # print(message.status)

            '''Enviar mensaje via Email'''
            with smtplib.SMTP('smtp.gmail.com', 587) as connection:
                body = (f'Lowest Price Alert! 🚨 Only ${"{:,}".format(price_updated[p]).replace(",", ".")} COP to fly from Medellin-{airport_from[p]} to '
                f'{citys[p]}-{airport_to[p]} from {date_from[p]} to {date_to[p]}. Flight has 1 step over, '
                f'via Medellin-{city_step_from[p]}-{citys[p]} and {citys[p]}-{city_step_to[p]}-Medellin.')
                connection.starttls() #make the conection secure
                connection.login(user=my_email, password=password)
                connection.sendmail(from_addr=my_email, 
                                    to_addrs='jaimevillalbaoyola@gmail.com', 
                                    msg= (f'Subject: Vuelos Lina \n\n {body}').encode("utf-8"),
                                    )

    n+=1   
    p+=1 
