import os
import json
import requests
import pandas as pd
from flask import Flask, request, Response

# constants
TOKEN = '5034162573:AAHDq4hsQDluNrkh8SK69vtezZ5yCYr-6J0'

# # Info about the Bot
# https://api.telegram.org/bot5034162573:AAHDq4hsQDluNrkh8SK69vtezZ5yCYr-6J0/getMe

# # get updates
# https://api.telegram.org/bot5034162573:AAHDq4hsQDluNrkh8SK69vtezZ5yCYr-6J0/getUpdates

# # Webhook - localhost
# https://api.telegram.org/bot5034162573:AAHDq4hsQDluNrkh8SK69vtezZ5yCYr-6J0/setWebhook?url=https://261b5c562482d9.lhr.life

# # Webhook - Heroku
# https://api.telegram.org/bot5034162573:AAHDq4hsQDluNrkh8SK69vtezZ5yCYr-6J0/setWebhook?url=https://rossmann-model-bot.herokuapp.com/

# # send message
# https://api.telegram.org/bot5034162573:AAHDq4hsQDluNrkh8SK69vtezZ5yCYr-6J0/sendMessage?chat_id=260932855&text=Hi Almir, I am doing good, tks!


def send_message( chat_id, text ):
	url = 'https://api.telegram.org/bot{}/'.format( TOKEN )
	url = url + 'sendMessage?chat_id={}'.format( chat_id )

	r = requests.post( url, json={'text': text} )
	print( 'Status Code {}'.format(r.status_code) )

	return None

def loading_dataset( store_id ):
	# loading test dataset
	df_test_raw = pd.read_csv( 'test.csv' )
	df_store_raw = pd.read_csv( 'store.csv' )

	# merge test dataset + store
	df_test = pd.merge( df_test_raw, df_store_raw, how='left',on='Store' )

	# choose store for prediction
	df_test = df_test[ df_test['Store'] == store_id ]

	if not df_test.empty:
		# removed closed days
		df_test = df_test[ df_test['Open'] != 0 ]
		df_test = df_test[ ~df_test['Open'].isnull() ]
		df_test = df_test.drop( 'Id', axis = 1 )

		# convert DataFrame to json
		data = json.dumps( df_test.to_dict( orient='records' ) )

	else:
		data = 'error'

	return data

def predict( data ):
	# API Call
	url = 'https://rossmann-model-app.herokuapp.com/rossmann/predict'
	header = {'Content-type': 'application/json'}
	data = data

	r = requests.post( url, data=data, headers=header )
	print( 'Status Code {}'.format( r.status_code ) )

	# convert json to dataframe
	d1 = pd.DataFrame( r.json(), columns=r.json()[0].keys() )

	return d1

def parse_message( message ):

	try:
		chat_id = message['message']['chat']['id']
	except:
		chat_id = message['edited_message']['chat']['id']

	try:
		store_id = message['message']['text']
	except:
		store_id = message['edited_message']['text']

	store_id = store_id.replace( '/','' )

	try:
		store_id = int(store_id)

	except ValueError:
		store_id = 'error'

	return chat_id, store_id


# API initialize
app = Flask( __name__ )

@app.route( '/', methods=['GET','POST'] )

def index():
    	if request.method == 'POST':
    		message = request.get_json()

    		chat_id, store_id = parse_message( message )

    		if store_id != 'error':
    			# loading data
    			data = loading_dataset( store_id )

    			if data != 'error':
					# prediction
    				d1 = predict(data)

    				# calculation
    				d2 = d1[['store','prediction']].groupby('store').sum().reset_index()

					# send message
    				msg = 'Store Number {} will sell R${:,.2f} in the next 6 weeks'.format( d2['store'].values[0], d2['prediction'].values[0] )

    				send_message( chat_id, msg )
    				return Response( 'Ok', status=200 )

    			else:
    				send_message( chat_id, 'Store Not Available' )
    				return Response( 'Ok', status=200 )
    		else:
    			send_message( chat_id, 'Store ID is Wrong' )
    			return Response( 'Ok', status=200 )

    	else:
    		return '<h1> Rossmann Telegram BOT </h1>'

if __name__ == '__main__':
	port = os.environ.get('PORT', 5000)
	app.run( host = '0.0.0.0', port=port)
