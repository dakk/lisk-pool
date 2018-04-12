import requests
import json
import sys
import time
import argparse 

ENABLE_VERSION_1 = False

if sys.version_info[0] < 3:
	print ('python2 not supported, please use python3')
	sys.exit (0)

# Parse command line args
parser = argparse.ArgumentParser(description='DPOS delegate pool script')
parser.add_argument('-c', metavar='config.json', dest='cfile', action='store',
                   default='config.json',
                   help='set a config file (default: config.json)')
parser.add_argument('-y', dest='alwaysyes', action='store_const',
                   default=False, const=True,
                   help='automatic yes for log saving (default: no)')
parser.add_argument('--min-payout', type=float, dest='minpayout', action='store',
                   default=None,
                   help='override the minpayout value from config file')

args = parser.parse_args ()
	
# Load the config file
try:
	conf = json.load (open (args.cfile, 'r'))
except:
	print ('Unable to load config file.')
	sys.exit ()
	
if 'logfile' in conf:
	LOGFILE = conf['logfile']
else:
	LOGFILE = 'poollogs.json'

fees = 0.0
if 'feededuct' in conf and conf['feededuct']:
	fees = 0.1

# Override minpayout from command line arg
if args.minpayout != None:
	conf['minpayout'] = args.minpayout


# Fix the node address if it ends with a /
if conf['node'][-1] == '/':
	conf['node'] = conf['node'][:-1]

if conf['nodepay'][-1] == '/':
	conf['nodepay'] = conf['nodepay'][:-1]


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
	
def createPaymentLine (to, amount):
	data = { "secret": conf['secret'], "amount": int (amount * 100000000), "recipientId": to }
	if conf['secondsecret'] != None:
		data['secondSecret'] = conf['secondsecret']

	nodepay = conf['nodepay']
	if ENABLE_VERSION_1:
		nodepay = 'http://localhost:6990'

	return 'curl -k -H  "Content-Type: application/json" -X PUT -d \'' + json.dumps (data) + '\' ' + nodepay + "/api/transactions\n\nsleep 1\n"
			

def estimatePayouts (log):
	if conf['coin'].lower () == 'ark' or conf['coin'].lower () == 'kapu' :
		uri = conf['node'] + '/api/delegates/forging/getForgedByAccount?generatorPublicKey=' + conf['pubkey']
		d = requests.get (uri)
		lf = log['lastforged']
		rew = int (d.json ()['rewards']) 
		log['lastforged'] = rew 
		rew = rew - lf
	else:
		uri = conf['node'] + '/api/delegates/forging/getForgedByAccount?generatorPublicKey=' + conf['pubkey'] + '&start=' + str (log['lastpayout']) + '&end=' + str (int (time.time ()))
		d = requests.get (uri)
		rew = d.json ()['rewards']

	forged = (int (rew) / 100000000) * conf['percentage'] / 100
	print ('To distribute: %f %s' % (forged, conf['coin']))
	
	if forged < 0.1:
		return ([], log, 0.0)
		
	d = requests.get (conf['node'] + '/api/delegates/voters?publicKey=' + conf['pubkey']).json ()
	
	weight = 0.0
	payouts = []
	
	for x in d['accounts']:
		if x['balance'] == '0' or x['address'] in conf['skip']:
			continue

		if conf['private'] and not (x['address'] in conf['whitelist']):
			continue
			
		weight += float (x['balance']) / 100000000
		
	print ('Total weight is: %f' % weight)
	
	for x in d['accounts']:
		if int (x['balance']) == 0 or x['address'] in conf['skip']:
			continue
			
		if conf['private'] and not (x['address'] in conf['whitelist']):
			continue

		payouts.append ({ "address": x['address'], "balance": (float (x['balance']) / 100000000 * forged) / weight})
		#print (float (x['balance']) / 100000000, payouts [x['address']], x['address'])
		
	return (payouts, log, forged)
	
	
def pool ():
	log = loadLog ()
	
	(topay, log, forged) = estimatePayouts (log)
		
	f = open ('payments.sh', 'w')

	if ENABLE_VERSION_1:
		f.write ("echo Starting dpos-api-fallback\n")
		f.write ("node dpos-api-fallback/dist/index.js start -n " + conf['nodepay'] + " -s " + conf['coin'][0] + "&\n")
		f.write ("DPOSFALLBACK_PID=$!\n")
		f.write ("sleep 4\n")

	for x in topay:
		# Create the row if not present
		if not (x['address'] in log['accounts']) and x['balance'] != 0.0:
			log['accounts'][x['address']] = { 'pending': 0.0, 'received': 0.0 }

		# Check if the voter has a pending balance
		pending = 0
		if x['address'] in log['accounts']:
			pending = log['accounts'][x['address']]['pending']
			
		# If below minpayout, put in the accoutns pending and skip
		if (x['balance'] + pending - fees) < conf['minpayout'] and x['balance'] > 0.0:
			log['accounts'][x['address']]['pending'] += x['balance']
			continue
			
		# If above, update the received balance and write the payout line
		log['accounts'][x['address']]['received'] += (x['balance'] + pending)
		if pending > 0:
			log['accounts'][x['address']]['pending'] = 0
		

		f.write ('echo Sending ' + str (x['balance'] - fees) + ' \(+' + str (pending) + ' pending\) to ' + x['address'] + '\n')
		f.write (createPaymentLine (x['address'], x['balance'] + pending - fees))

			
	# Handle pending balances
	for y in log['accounts']:
		# If the pending is above the minpayout, create the payout line
		if log['accounts'][y]['pending'] - fees > conf['minpayout']:
			f.write ('echo Sending pending ' + str (log['accounts'][y]['pending']) + ' to ' + y + '\n')
			f.write (createPaymentLine (y, log['accounts'][y]['pending'] - fees))
			
			log['accounts'][y]['received'] += log['accounts'][y]['pending']
			log['accounts'][y]['pending'] = 0.0
			
			
	# Donations
	if 'donations' in conf:
		for y in conf['donations']:
			f.write ('echo Sending donation ' + str (conf['donations'][y]) + ' to ' + y + '\n')
			f.write (createPaymentLine (y, conf['donations'][y]))


	# Donation percentage
	if 'donationspercentage' in conf:
		for y in conf['donationspercentage']:
			am = (forged * conf['donationspercentage'][y]) / 100
			
			f.write ('echo Sending donation ' + str (conf['donationspercentage'][y]) + '% \(' + str (am) + 'LSK\) to ' + y + '\n')	
			f.write (createPaymentLine (y, am))

	if ENABLE_VERSION_1:
		f.write ("kill $DPOSFALLBACK_PID\n")
	f.close ()
	
	# Update last payout
	log['lastpayout'] = int (time.time ())
	
	for acc in log['accounts']:
		print (acc, '\tPending:', log['accounts'][acc]['pending'], '\tReceived:', log['accounts'][acc]['received'])
	
	if args.alwaysyes:
		print ('Saving...')
		saveLog (log)
	else:
		yes = input ('save? y/n: ')
		if yes == 'y':
			saveLog (log)
			
			

if __name__ == "__main__":
	pool ()
