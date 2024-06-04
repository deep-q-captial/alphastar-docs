# AlphaStart Documentation

Documentation and examples for AlphaStar.


# Onboarding
In order to make and or take liquidity on alphastar you will need to follow these steps

## Register your wallet address
Only supporting Arbitrum L2 currently.
You will need to register which wallet address you want to link your account for trading.


2. As a market maker you will need to register 2 things lease 
  a. An arbitrum wallet address you wish tou will need 
  b. to whitelist an IP address (not setup yet but wallet)

## Depositing funds into the alphastar smart contract
In order to trade you will need to deposit the funds you wish to exchange - we are 100% collateralized at present - if you wish to make a market in WETH-USDC you will need to deposit both WETH and USDC into the smart contract.
You first need to approve amount of ccy to deposit to the DCN smart contract (see what vertex write here too same process)
- example deposit approval script in examples/approve.py
- examples/constants.py contains information about which tokens you can deposit



# Sequence Diagrams
There are 5 message types you can expect to interact with on alphastar. Below is a description of each message type and how to

```python
Quote (websocket type='quote')
QuoteReject (websocket type='quotereject')
MarketData (websocket type='marketdata')
QuoteResponse (websocket type='quoteresponse')
MakerTradeMessage (websocket type='makertrademessage')
TakerTradeMessage (websocket type='takertrademessage')
```


# Trading examples 
We provide a couple of basic examples to get you started and see how you might build a simple sytem to interact with alphastars matching engine.

We use websocket endpoints for you to connect to and send/receive messages. There are three of interest and we provide code exmaple of how one might interact with them.
```python
ws://localhost:8000/ws/marketdata
ws://localhost:8000/ws/maker
ws://localhost:8000/ws/taker
```


## Running a taker strategy
- see examples/dcn_taker.py
- must set environment variable TAKER_PRIVATE_KEY to run script.
```python
TAKER_PRIVATE_KEY=xxx python3 examples/dcn_taker.py 
```

## Running a maker strategy
- see examples/dcn_maker.py
- must set environment variable MAKER_PRIVATE_KEY to run script.
```python
MAKER_PRIVATE_KEY=xxx python3 examples/dcn_taker.py 
```

- API online end point documentation http://localhost:8000/docs


## REST endpoints

There are a series of REST endpoints where you can request withdrawal/deposits

Please refer to http://localhost:8000/docs