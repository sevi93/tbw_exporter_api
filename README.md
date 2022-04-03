# Python Custom TBW Exporter

Custom TBW prometheus exporter API

## Install
### Prerequisites
- python3 and pip
- process Manager 2 (pm2)

### Install dependencies
`pip3 install -r requirements.txt`

## Configuration
### Copy the example config
`cp src/config/config.example src/config/config`

### Run
`pm2 start package.json`

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
- staged payout
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
- delegate wallet balance

__**Voters metrics**__
- List of voters with the amount of tokens

__**Network metrics**__
- number of peers

__**Token metrics**__
- Token price

__**Delegate transactions metrics**__
- List of the last 100 payout transactions with address,date,amount
