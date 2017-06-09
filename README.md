# Lisk pool distribution software
This software is created by lisk delegate "dakk", please consider a small donation if you
use this software: "2324852447570841050L" for lisk or "7725849364280821971S" for shift.


## Configuration
Fork this repo; edit liskpool.py and modify the first lines with your settings:

- PUBKEY: your delegate pubkey
- PERCENTAGE: percentage to distribute
- SECRET: your secret
- SECONDSECRET: your second secret or none if disabled
- NODE: the lisk node where you get forging info
- NODEPAY: the lisk node used for payments
- MINPAYOUT: the minimum amount for a payout

Now edit docs/index.html and customize the webpage.

Finally edit poollogs_example.json and put in lastpayout the unixtimestamp of your last payout or the
date of pool starting; move poollogs_example.json to poollogs.json.


## Running it

`python liskpool.py`

It produces a file "payments.sh" with all payments shell commands. Run this file with:

`bash payments.sh`

The payments will be broadcasted (every 10 seconds). At the end you can move your generated
poollogs.json to docs/poollogs.json and send the update to your git repo.

To display the pool frontend, enable docs-site on github repository settings.


## Batch mode

The script is also runnable by cron using the -y argument:

`python liskpool.py -y`

There is also a 'batch.sh' file which run liskpool, then payments.sh and copy the poollogs.json
in the docs folder.


## License
Copyright 2017 Davide Gessa

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

