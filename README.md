# akamai-process-logs

Download and process Akamai logs from NetStorage.

## Installation

Create a Python virtual environment and install dependencies:

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

To download logs from Akamai, you'll need a set of NetStorage HTTP API
credentials.

```
./fetch.py \
    --netstorage-hostname=example.akamaihd.net \
    --netstorage-key=abcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcda \
    --netstorage-keyname=myusername
    --netstorage-directory=/123456/www.example.com/ \
    --from-date=2020-09-01 \
    --to-date=2020-09-30
```

To then process those logs to count status codes:

```
./process.py *.gz
```

or to process only a single log file:

```
./process.py example_123456.abcdacbd.202010010000-0100-0.gz
```

----

## Open source licensing info
1. [TERMS](TERMS.md)
2. [LICENSE](LICENSE)
3. [CFPB Source Code Policy](https://github.com/cfpb/source-code-policy/)
