from pprint import pprint
import requests
from datetime import datetime, timedelta
from twilio.rest import Client
import smtplib
import time
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
# n=2
# c=0
# for i in sheet_data:
#     iata_code = code_citys[c]
#     sheet_response = requests.put(url=f'{sheet_endpoint}/{n}', json={'price':{'iataCode' : iata_code}})
#     n+=1
#     c+=1
#     # print(sheet_response.text)


'''conectar con google'''
google_endpoint = 'https://serpapi.com/search?engine=google_flights'
API_KEY = os.environ.get('API_KEY_GOOGLE')
headers = {'apikey': API_KEY}

intervalo = 8 * 60 * 60
while True :


    '''buscar los vuelos en google'''
    flights_endpoint = f'{google_endpoint}'

    today = datetime(2024,6,8)
    range_dates = today + timedelta(days=7)

    today_formate = today.strftime('%Y-%m-%d')
    range_dates_formate = range_dates.strftime('%Y-%m-%d')


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

        params = {
            'engine': "google_flights",
            'departure_id' : "MDE",
            'arrival_id': code_citys[i],
            'outbound_date': today_formate,
            'return_date': range_dates_formate,
            'stops' : 2,
            'currency': "COP",
            'hl': "es",
            'type' : 1,
            'api_key': API_KEY,
            'departure_token' : 'WyJDalJJZEV0clUydHJibmgyUW10QlVVVkJWMUZDUnkwdExTMHRMUzB0TFhsc2EzSXhNVUZCUVVGQlIxaExZWG93U2pOVVRYTkJFZzVCVmprek56VjhRVll5TXprak1Sb0xDTDd3ZXhBQUdnTkRUMUE0SEhENmxBTT0iLFtbIk1ERSIsIjIwMjQtMDYtMDgiLCJCT0ciLG51bGwsIkFWIiwiOTM3NSJdLFsiQk9HIiwiMjAyNC0wNi0wOCIsIkxQQiIsbnVsbCwiQVYiLCIyMzkiXV1d'
        }

    
        response = requests.get(url=flights_endpoint, params=params)
        print(response.text)
    
        price_updated.append(response.json()['other_flights'][0]['price'])
        # print(price_updated)
        airport_from.append(response.json()['search_parameters']['departure_id'])
        airport_to.append(response.json()['search_parameters']['arrival_id'])
        date_from.append(response.json()['search_parameters']['outbound_date'])
        date_to.append(response.json()['search_parameters']['return_date'])
        city_step_from.append(response.json()['other_flights'][0]['flights'][0]['arrival_airport']['id'])
        city_step_to.append(response.json()['other_flights'][0]['flights'][0]['arrival_airport']['id'])       
        
    
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
        if price_updated[p] < price[p]:
            '''enviar el mensaje'''
            response = requests.put(url=f'{sheet_endpoint}/{n}', json={'price':{'lowestPrice' : price_updated[p]}} )        
            
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
                                    to_addrs='linavillalbaoyola@gmail.com',
                                    msg= (f'Subject: Vuelos Lina \n\n {body}').encode("utf-8"),
                                    )

        n+=1
        p+=1
    time.sleep(intervalo)


