import requests
import json
import time

NODE = "https://wallet.lisknode.io"
NODEPAY = "http://localhost:8000"
PUBKEY = "120d1c3847bd272237ee712ae83de59bbeae127263196fc0f16934bcfa82d8a4"
LOGFILE = 'poollogs.json'
PERCENTAGE = 15
SECRET = "SECRET"
SECONDSECRET = None

def loadLog ():
	try:
		data = json.load (open (LOGFILE, 'r'))
	except:
		data = {
			"lastpayout": 0, 
			"accounts": {},
			"skip": []
		}
	return data
	
	
def saveLog (log):
	json.dump (log, open (LOGFILE, 'w'), indent=4, separators=(',', ': '))
	


def estimatePayouts (log):
	uri = NODE + '/api/delegates/forging/getForgedByAccount?generatorPublicKey=' + PUBKEY + '&start=' + str (log['lastpayout']) + '&end=' + str (int (time.time ()))
	d = requests.get (uri)
	rew = d.json ()['rewards']
	forged = (int (rew) / 100000000) * PERCENTAGE / 100
	print ('To distribute: %f LSK' % forged)
	
	d = requests.get (NODE + '/api/delegates/voters?publicKey=' + PUBKEY).json ()
	
	weight = 0.0
	payouts = []
	
	for x in d['accounts']:
		if x['balance'] == '0' or x['address'] in log['skip']:
			continue
			
		weight += float (x['balance']) / 100000000
		
	print ('Total weight is: %f' % weight)
	
	for x in d['accounts']:
		if int (x['balance']) == 0 or x['address'] in log['skip']:
			continue
			
		payouts.append ({ "address": x['address'], "balance": (float (x['balance']) / 100000000 * forged) / weight})
		#print (float (x['balance']) / 100000000, payouts [x['address']], x['address'])
		
	return payouts
	
	

if __name__ == "__main__":
	log = loadLog ()
	
	topay = estimatePayouts(log)
	
	f = open ('payments.sh', 'w')
	for x in topay:
		if not (x['address'] in log['accounts']) and x['balance'] != 0.0:
			log['accounts'][x['address']] = { 'pending': 0.0, 'received': 0.0 }
			
		if x['balance'] < 0.1:
			log['accounts'][x['address']]['pending'] += x['balance']
			continue
			
		log['accounts'][x['address']]['received'] += x['balance']	
		
		f.write ('echo Sending ' + str (x['balance']) + ' to ' + x['address'] + '\n')
		
		data = { "secret": SECRET, "amount": str (int (x['balance'] * 100000000)), "recipientId": x['address'] }
		if SECONDSECRET != None:
			data['secondSecret'] = SECONDSECRET
		
		f.write ('curl -k -H  "Content-Type: application/json" -X PUT -d \'' + json.dumps (data) + '\' ' + NODEPAY + "/api/transactions\n\n")
		f.write ('sleep 10\n')
			
	for y in log['accounts']:
		if log['accounts'][y]['pending'] > 0.1:
			f.write ('echo Sending pending ' + str (log['accounts'][y]['pending']) + ' to ' + y + '\n')
			
			
			data = { "secret": SECRET, "amount": str (int (log['accounts'][y]['pending'] * 100000000)), "recipientId": y }
			if SECONDSECRET != None:
				data['secondSecret'] = SECONDSECRET
			
			f.write ('curl -k -H  "Content-Type: application/json" -X PUT -d \'' + json.dumps (data) + '\' ' + NODEPAY + "/api/transactions\n\n")
			log['accounts'][y]['received'] += log['accounts'][y]['pending']
			log['accounts'][y]['pending'] = 0.0
			f.write ('sleep 10\n')
			
		
	f.close ()
	
	log['lastpayout'] = int (time.time ())
	
	print (json.dumps (log, indent=4, separators=(',', ': ')))
	
	yes = input ('save? y/n: ')
	if yes == 'y':
		saveLog (log)
