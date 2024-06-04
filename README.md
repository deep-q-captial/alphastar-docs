# AlphaStart Documentation

Documentation and examples for AlphaStar.


# Onboarding
In order to make and or take liquidity on alphastar you will need to follow these steps

## Register your wallet address
Only supporting Arbitrum L2 currently.
You will need to register which wallet address you want to link your account for trading.


2. As a market maker you will need to register 2 things lease   
  - An arbitrum wallet address for settlement/deposit/withdraw
  - An IP address (not setup yet but wallet will suffice for screening - just means anyone can try and we might get additional load)


## Depositing funds into the alphastar smart contract
In order to trade you will need to deposit the funds - we are 100% collateralized - if you wish to make a market in WETH-USDC you will need to deposit both WETH and USDC into the smart contract. We do not custody them - the balances are tracked and you agree to the fees imposed by the protocol (DO WE NEED SPECIFIC LEGAL HERE - what do others say)
You first need to approve an amount of a token to deposit to the DCN smart contract (see what vertex write here too same process)
- example deposit approval script in `examples/approve.py`
- `examples/constants.py` contains information about which tokens you can deposit currently on TestNet only USDC and WETH are supported


# Sequence Diagrams
There are 5 message types you can expect to interact with on alphastar. Below is a description of each message type and how to

```python
Quote (websocket type='quote', user publish)
QuoteReject (websocket type='quotereject' subscription only)
MarketData (websocket type='marketdata' subscription only)
QuoteResponse (websocket type='quoteresponse' user publish)
MakerTradeMessage (websocket type='makertrademessage' two-way)
TakerTradeMessage (websocket type='takertrademessage' two-way)
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


## REST endpoints

There are REST endpoints where you can request withdrawal, deposit and see balances for your account (wallet address).

Please refer to http://localhost:8000/docs