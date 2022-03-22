# Python Custom TBW Exporter

Custom TBW prometheus exporter API

## Install
### Prerequisites
- python3 and pip
- process Manager 2 (pm2)

### Install dependencies
`pip3 install -r requirements.txt`

### Run
`pm2 start package.json`

## Configuration
### Copy the example config
`cp src/config/config.example src/config/config`

## Metrics

Provided metrics :

__**TBW constant configuration parameters**__
- atomic
- payout interval
- payout voter share
- payout delegate share

__**TBW payout metrics**__
- pending voters payout
- pending delegate payout
- number of block before payout
- total distributed voters rewards
- total distributed delegate rewards

__**Blockchain metrics**__
- current block height
- number of active delegate
- height of last forged block
- delegate block round
- forged block round
- tbw forged block round

__**Delegate metrics**__
- number of voters
- delegate rank
- total forged token
- total forged block
- timestamp of last forged block

__**Network metrics**__
- number of peers

