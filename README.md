# AlphaStar Documentation
Alphastar is a decentralized electronic communication network that allows market participants to engage in "over-the-counter" (OTC) trading of digital assets. The platform is designed to allow on-chain traders access to insitutional style OTC trading with the benefits of a decentralized exchange. 


This document provides an overview of the AlphaStar platform, including the architecture, message types, and examples of how to interact with the platform.

In this repository you will also find sample code which demonstrate how to interact with the platform using the REST API and Websockets.

# Onboarding
In order to make and or take liquidity on alphastar you will need to follow these steps

## 1. Register your wallet address
Alphastar is in private beta on the Arbitrum testnet and we will only be allowing whitelisted wallet addresses to trade on the platform. This is to ensure that we can provide the best possible experience to our users and to ensure that we can scale the platform effectively as we work with our early partners to scale the platform.

Trading on the Alphastar platform is pseudonymous, meaning that you do not need to provide any personal information to trade on the platform. However, you will need to register your wallet address with the platform in order to trade. OTC trading relationships are bi-lateral, disclosed trading relationships between two parties. All post-trade confirmations will disclose both the buyer and seller wallet addresses to each other (and only to each other). Users may use a single wallet address for all trading relationships, or may use multiple wallet addresses to segregate trading relationships across different strategies.

## 2. Whitelist your IP Address
In order to access the Alphastar platform, you will need to whitelist your IP address. This is to ensure that only authorized users can access the platform. Please provide your IP address to the Alphastar team so that we can whitelist it for you.


## 3. Deposit funds into the Alphastar smart contract
Alphastar is a non-custodial protocol that requires 100% collateralization of funds prior to trading. In order to trade on the platform, you will need to deposit funds into the Alphastar smart contract. The smart contract is deployed on the Arbitrum testnet and supports the following tokens:
- WETH
- USDC

You first need to approve an amount of a token to deposit to the DCN smart contract (see what vertex write here too same process)
- example deposit approval script in `examples/approve.py`
- `examples/constants.py` contains information about which tokens you can deposit currently on TestNet only USDC and WETH are supported

# MAKING ON ALPHASTAR
## Pools
A pool is simply a matching engine in which market makers stream indicative quotes for a single trading pair, and those quotes are matched with taker orders. Pools may be public or private, and may be configured to allow or disallow specific taker addresses. In Testnet we have a single pool, 'WETH-USDC-common' which is a public pool that allows any whitelisted wallet to make or take on it. 

The matching logic is based on price/time priority, meaning that the first order to be received at a given price level will be the first to be matched. In future versions of alphastar, all public wallets will continue with price/time priority, but private pools may be configured to use other matching logic that rewards specific behaviors such as expected market impact, price improvement, reject rates, etc.

## Maker Quote/Order lifecycle
A maker on the Alphastar protocol begins by streaming indicative quotes to the pool. These quotes are not binding, and are used to inform takers of the maker's intent to trade at a given price level. The maker may update or cancel these quotes at any time. When a taker order is received that matches the maker's quote, the maker is notified and may choose to accept or reject the taker order. If the maker accepts the taker order, the trade is executed and the maker is credited with the proceeds of the trade. If the maker rejects the taker order, the taker order is cancelled and the maker is not charged any fees.

1. Maker streams indicative quotes to the pool. These quotes are not binding, and are used to inform takers of the maker's intent to trade at a given price level.
2. Taker order is received that matches the maker's quote.
3. Maker is notified and may choose to accept or reject the taker order within a given time window (100 milliseconds)
4. IF the maker ACCEPTS the taker order, the trade is executed and the maker is credited with the proceeds of the trade.
5. IF the maker REJECTS the taker order, the taker order is cancelled and the maker is not charged any fees.

## Maker Quote/Order websocket connection
In order to connect to the Alphastar maker websocket, you will need to subscribe to the following endpoint:
```ws://dcn.alpha.deepqdigital.net/ws/maker```

Connection requires the following headers:
```python
{"wallet": "0x1234",             # your registered wallet address
 "timestamp": int(time.time()),  # current unix timestamp in seconds as an integer
 "signature": "abcd1234"}        # a signed message derived from the wallet's private key and the timestamp
```

An example of how to connect to the maker websocket is provided in `examples/dcn_maker.py`, with the code to to create the authentication headers in `examples/signing.py`.

There are 3 message types that you can expect to interact with on the maker websocket:
```python
Quote (websocket type='quote', user publish)
QuoteReject (websocket type='quotereject' subscription only)
MakerTradeMessage (websocket type='makertrademessage' two-way)
```

## Maker Quote Message
The Quote message is used to stream indicative quotes to the pool. These quotes are not binding, and are used to inform takers of the maker's intent to trade at a given price level. The Quote message has the following fields:

```python
{
    "type": "quote",
    "data": {
      "sending_time": time.time(),    # unix timestamp in seconds as a float
      "quote_id": "abcd1234",         # client generated unique identifier for the quote as a string
      "wallet_id": "0x1234",          # wallet address of the maker as a string
      "pool_id": "WETH-USDC-common",  # pool id as a string
      "bid_px": ["99.99", "99.98", "99.97", "99.96", "99.95", "99.94"],  # list of bid prices as strings
      "offer_px": ["100.01", "100.02", "100.03", "100.04", "100.05", "100.06"],  # list of offer prices as strings
      "valid_until_time": 5.0,       # time in seconds until the quote is considered stale as a float
    }
}
```

When a maker sends the quote message, they will populate two fields. 
- "type": will be set to "quote" to indicate that the maker is sending a new quote update to the pool. 
- "data": will contain the quote data with the following fields:

    - "sending_time": the UTC timestamp in seconds when the quote was sent as a float
    - "quote_id": a client generated unique identifier for the quote as a string -- this is a convenience to the maker to allow them to identify their quotes in the event of a quote reject or maker trade message
    - "wallet_id": the wallet address of the maker as a string. This must be the wallet ID of the maker that was registered with the platform
    - "pool_id": the pool id as a string. In testnet, this will be "WETH-USDC-common"
    - "bid_px": a list of bid prices as strings. Each pool has a fixed number of rungs of liquidity, and the maker must provide a price for each rung. In testnet, the rungs of liquidity are [0.1, 0.5, 1, 5, 10, 20] WETH respectively. If the maker does not wish to provide liquidity at a given price level, they may set the price to "0.0". Finally, prices should be interpreted as the full-amount price the maker is willing to buy or sell up to the amount for that rung of liquidity. 
    - "offer_px": a list of offer prices as strings. (see bid_px for more information)
    - "valid_until_time": the time in seconds until the quote is considered stale as a float. Once the sending_time + valid_until_time has been reached the quote will be removed from the pool. The maximum time a quote can be valid for depends on the pool configuration. In testnet, the maximum time a quote can be valid for is 5 seconds.

Note. There is no cancel quote message. If a maker wishes to remove their quotes from the pool, they may either wait for their quotes to expire or send a new quote message with the bid_px and offer_px set to "0.0".

A note on matching methodology:
the price quoted will be the full-amount price the maker is willing to buy or sell up to the amount for that rung of liquidity. There is no sweeping of liquidity, so if a taker order is placed for 1.0 WETH the order will be filled at the best price available for 1.0 WETH. If the order is for 8.0 WETH, the order will be filled at the best price available for 10.0 WETH. The trade will be given in full to the maker whose price the taker order is matched with. This ensures that the market maker is not penalized for the risk management of other market makers when they win a trade. 


## Maker QuoteReject Message
The QuoteReject message is used to inform the maker that their quote has been rejected by the pool. The QuoteReject message has the following fields:

```python
{
    "type": "quotereject",
    "data": {
      "sending_time": time.time(),   # unix timestamp in seconds as a float
      "quote_id": "abcd1234",        # client generated unique identifier for the quote as a string provided in the originating quote
      "wallet_id": "0x1234",         # wallet address of the maker as a string provided in the originating quote
      "pool_id": "WETH-USDC-common", # pool id as a string provided in the originating quote
      "reason": "quote_expired"      # reason for the quote rejection as a string
    }
}
```

The reason message may be as follows:
- "Insufficient funds to cover the quote" - the maker does not have sufficient funds in the alphastar smart contract to cover the quote
- "pool_id {pool_id} does not match {actual_pool_id}" - the pool_id provided in the quote message is not a valid pool_id
- "length of bid_px {n} does not match {m}" - where n is the length of the bid_px list in the quote message and m is the number of rungs of liquidity in the pool
- "length of offer_px {n} does not match {m}" - where n is the length of the offer_px list in the quote message and m is the number of rungs of liquidity in the pool
- "valid_until_time {t} is greater than {x}" - where t is the valid_until_time in the quote message and x is the maximum valid_until_time for the pool

## Maker Trade Message
The MakerTradeMessage is the primary message that the maker will receive from during the order lifecycle. The Maker will receive a message when a taker requests an order. They will have 100 milliseconds to respond to the order with an accept or reject message. Finally, the maker will receive a final confirmation to indicate the order has been `DONE` or `NOT_DONE`.

```python
{
  "type": "makertrademessage",
  "data": {
    "timestamp": time.time(),  # unix timestamp in seconds as a float. The time the message was sent
    "match_timestamp": time.time(), # unix timestamp in seconds as a float. The time the taker order and maker quote were matched in the pool
    "wallet_id": "0x1234",    # wallet address of the maker as a string
    "pool_id": "WETH-USDC-common",  # pool id as a string
    "symbol": "WETH-USDC",    # trading pair as a string -- in testnet will always be WETH-USDC
    "trade_id": 1,           # unique identifier for the trade as an integer -- assigned by the matching engine on trade match
    "taker_wallet_id": "0x5678",  # wallet address of the taker as a string
    "side": "BUY",          # side of the trade as a string -- BUY or SELL
    "requested_quantity": '0.75',  # quantity requested by the taker as a string
    "requested_price": '100.0',   # price requested by the taker as a string
    "quote_price": '100.0',       # price of the maker quote as a string
    "quote_quantity": "1.0",     # quantity of the maker quote as a string
    "quote_id": "abcd1234",      # The quote_id of the maker quote that matched with the taker order
    "quote_created_at": time.time(),  # unix timestamp in seconds as a float. The time the maker quote was accepted into the pool matching engine
    "valid_until_time": 5.0,     # time in seconds until the quote is considered stale as a float, taken from the maker quote
    "maker_fee": "0.0",          # the maker fee amount on the trade in maker_fee_ccy terms as a string
    "maker_fee_ccy": "USDC",     # the maker fee currency as a string -- for testnet will always be USDC
    "executed_quantity": "0.75", # the quantity of the trade that was executed as a string
    "executed_price": "100.0",   # the price of the trade that was executed as a string
    "status": "PENDING"          # the status of the trade as a string -- REQUEST, ACCEPT, REJECT, DONE, NOT_DONE
    "msg": "system message"      # a system message as a string 
  }
}
```

The MakerTradeMessage will always have the type "makertrademessage" and the "data" field will contain a dictionary with the following fields:
- "timestamp": the UTC timestamp in seconds when the message was sent as a float
- "match_timestamp": the UTC timestamp in seconds when the taker order and maker quote were matched in the pool as a float
- "wallet_id": the wallet address of the maker as a string. This must be the wallet ID of the maker that was registered with the platform
- "pool_id": the pool id as a string. In testnet, this will be "WETH-USDC-common"
- "symbol": the trading pair as a string. In testnet, this will always be "WETH-USDC"
- "trade_id": a unique identifier for the trade as an integer. This is assigned by the matching engine on trade match
- "taker_wallet_id": the wallet address of the taker as a string. 
- "side": the side of the trade as a string. This will be either "BUY" or "SELL"
- "requested_quantity": the quantity requested by the taker as a string. This is the quantity that the taker is requesting to trade. It may be any value between 0 and the maximum quantity available in the pool. Trades are always matched with the rung of liquidity closest to, but not exceeding, the requested quantity.
- "requested_price": the price requested by the taker as a string. This is the price that the taker is requesting to trade at. This may not always be exactly equal to the price quoted by the maker, as the matching engine will always match the taker with the best price that is available in the pool.
- "quote_price": the price of the maker quote as a string. This is the price that the maker quoted in the pool. This may not always be exactly equal to the requested price of the taker, as the matching engine will always match the taker with the best price that is available in the pool.
- "quote_quantity": the quantity of the maker quote as a string. This is the quantity that the maker quoted in the pool. 
- "quote_id": the quote_id of the maker quote that matched with the taker order. This is the quote_id that the maker provided in the Quote message.
- "quote_created_at": the UTC timestamp in seconds when the maker quote was accepted into the pool matching engine as a float
- "valid_until_time": the time in seconds until the quote is considered stale as a float. This is the valid_until_time that the maker provided in the Quote message.
- "maker_fee": the maker fee amount on the trade in maker_fee_ccy terms as a string. This is the maker fee that will be charged to the maker if the trade is executed.
- "maker_fee_ccy": the maker fee currency as a string. For testnet, this will always be "USDC"
- "executed_quantity": the quantity of the trade that was executed as a string. This is the quantity that was matched between the taker and the maker.
- "executed_price": the price of the trade that was executed as a string. The matching engine will always match the taker with the best price that is available in the pool that is equal to or better than the requested price of the taker. If the maker has provided liquidity at a better price than the requested price of the taker, the maker has the choice to either fill the trade at the requested price of the taker OR to price improve the taker trade. Price improvement will be tracked and stored as a metric in maker analytics. If the maker attempts to fill the trade at a price that is worse than the requested price of the taker, the trade will be rejected and the maker will be credited with a REJECT in its maker analytics profile.
- "status": the status of the trade as a string. This will be one of the following values: 
    - "REQUEST": the trade has been requested by the taker and the maker has a set time limit (100ms in testnet) to respond with an ACCEPT or REJECT message from the `timestamp` field. 
    - "ACCEPT": IF the maker chooses to accept the trade, the maker will change the status to ACCEPT, set executed_quantity equal to requested_quantity, and set executed_price to a value that is equal to or better than the requested price of the taker. They will then send the message back to the pool over the maker websocket.
    - "REJECT": IF the maker chooses to reject the trade, the maker will change the status to REJECT, set executed_quantity to "0.0", and set executed_price to "0.0". They will then send the message back to the pool over the maker websocket.
    - "DONE": The system will send a final confirmation message to the maker to indicate that the trade has been executed with the final trade details. This message should be used as the golden source of truth for the trade execution. The sending of an ACCEPT message does not guarantee that the trade will be executed. 
    - "NOT_DONE": The system will send a final confirmation message to the maker to indicate that the trade has not been executed. The system will provide a reason for the trade not being executed in the `msg` field. The possible paths to a NOT_DONE status are: 1. the maker sends a REJECT message, 2. The maker sends an ACCEPT message where the executed_quantity is not equal to the requested quantity, 3. The maker sends an ACCEPT message where the executed_price is worse than the requested price of the taker.

## Trade Acceptance
When a maker receives a MakerTradeMessage with a status of "REQUEST", they have the option to accept or reject the trade. The purpose of this mechanism is to allow the maker to protect themselves from tail risk of large, adverse market moves while quotes/orders are in flight. We do not impose any restrictions on the maker's ability to accept or reject trades, but we do track the maker's acceptance rates, their average time to accept or reject trades, the average price improvement on accepts, and the average cost of rejected trades. These metrics will be used to inform the maker's reputation on the platform and may be used to inform future trading relationships with the maker.

### Accepting a trade without price improvement
```python
msg = sample_function_to_retrieve_message_from_websocket()
if msg['type'] == 'makertrademessage' and msg['data']['status'] == 'REQUEST':
    # accept the trade
    msg['data']['status'] = 'ACCEPT'
    msg['data']['executed_quantity'] = msg['data']['requested_quantity']
    msg['data']['executed_price'] = msg['data']['requested_price']
    send_message_to_websocket(msg)
```

### Accepting a trade with price improvement
```python
msg = sample_function_to_retrieve_message_from_websocket()
if msg['type'] == 'makertrademessage' and msg['data']['status'] == 'REQUEST':
    # accept the trade with price improvement
    msg['data']['status'] = 'ACCEPT'
    msg['data']['executed_quantity'] = msg['data']['requested_quantity']
    # can price improve by giving your quoted price, or any other logic which improves upon the taker's requested price
    msg['data']['executed_price'] = msg['data']['quote_price']
    send_message_to_websocket(msg)
```

### Rejecting a trade
```python
msg = sample_function_to_retrieve_message_from_websocket()
if msg['type'] == 'makertrademessage' and msg['data']['status'] == 'REQUEST':
    # reject the trade
    msg['data']['status'] = 'REJECT'
    msg['data']['executed_quantity'] = '0.0'
    msg['data']['executed_price'] = '0.0'
    send_message_to_websocket(msg)
```

## Running a maker strategy
- see examples/dcn_maker.py
- must set environment variable MAKER_PRIVATE_KEY to run script.
```python
MAKER_PRIVATE_KEY=xxx python3 examples/dcn_taker.py 
```

# TAKING ON ALPHASTAR
Market participants on Alphastar can simultaneously make and take liquidity. 

## Taker Order lifecycle
A taker on the Alphastar protocol follows the below order lifecycle:
1. Taker subscribes to the marketdata websocket to receive indicative quotes from the pool in real-time with a `MarketData` message
2. Taker sends a `QuoteRequest` message to the pool to request a trade based on the indicative quotes
3. IF the taker's `QuoteRequest` is not matched, the taker will receive a `TakerTradeMessage` with a `REJECT` status and a message explaining why the trade missed.
4. IF the taker's QuoteRequst is matched with a Maker Quote it is sent to the maker for acceptance or rejection
5. Taker receives a TakerTradeMessage from the pool with the Maker's response, either `ACCEPT` or `REJECT`

## Marketdata websocket connection
In order to connect to the Alphastar market data websocket, you will need to subscribe to the following endpoint:
```ws://dcn.alpha.deepqdigital.net/ws/mktdata```

When subscribed you will see a stream of continuous, real-time quotes as market makers update their pricing into the pool. The message type will be
```python
MarketData (websocket type='marketdata' subscription only)
```

## MarketData Message
The `MarketData` message will have the following format:

```python 
{
    "type": "marketdata",
    "data": {
        'timestamp': 1.1,  # UTC timestamp in seconds as a float. The time the quote was updated in the pool.
        'pool_id': 'ETH-USD_common',  # pool id as a string
        'sequence_number': 300,       # sequence number of the quote as an integer -- system generated
        'symbol': 'WETH-USDC',        # trading pair as a string
        'bids': ['100', '99', '98', '97', '96', '95'],  # list of bid prices as strings
        'offers': ['101', '102', '103', '104', '105', '106'],  # list of offer prices as strings
        'sizes': ['0.1', '0.5', '1', '5', '10', '20']  # corresponding sizes in ccy0 terms (WETH in testnet) as strings
    }
}
```
The MarketData message will always have the type "marketdata" and the "data" field will contain a dictionary with the following fields:
- "timestamp": the UTC timestamp in seconds when the quote was updated in the pool as a float. This is the time the pool accepted the quote from the maker.
- "pool_id": the pool id as a string. In testnet, this will be "WETH-USDC-common"
- "sequence_number": the sequence number of the quote as an integer. This is a system generated field that is used to track the order of quotes in the pool.
- "symbol": the trading pair as a string. In testnet, this will always be "WETH-USDC"
- "bids": a list of bid prices as strings. Each pool has a fixed number of rungs of liquidity, and the taker is shown the best price available at that time for each rung of liquidity. In testnet, the rungs of liquidity are [0.1, 0.5, 1, 5, 10, 20] WETH respectively. If there is no liquidity available at a given price level, the price will be set to "0.0". 
- "offers": a list of offer prices as strings. (see bids for more information)
- "sizes": a list of corresponding sizes in ccy0 terms (WETH in testnet) as strings. The size is the amount of liquidity available at each price level. If there is no liquidity available at a given price level, the size will be set to "0.0".

## Taker Order websocket connection
In order to connect to the Alphastar taker websocket, you will need to subscribe to the following endpoint:
```ws://dcn.alpha.deepqdigital.net/ws/taker```

When subscribed you will be able to send trades via a QuoteResponse message and receive responses via a TakerTradeMessage message. Only the taker's trades will be visible on this websocket. The message types will be:

```python
QuoteResponse (websocket type='quoteresponse' user publish)
TakerTradeMessage (websocket type='takertrademessage' two-way)
```

## QuoteRequest Message
If a taker wishes to place an order based on the indicative quotes shown to them in a given pool, they will send a `QuoteResponse` message over the taker websocket with the following format:

```python
{
    "type": "quoteresponse",
    "data": {
        'pool_id': 'ETH-USD_common', 
        'price': '101.00', 
        'quantity': '0.1', 
        'quote_resp_id': 'quote_response_id', 
        'side': 'SELL', 
        'symbol': 'WETH-USDC', 
        'sending_time': 1712784773.339189, 
        'wallet_id': 'taker_wallet'
    }
}
```

Takers will always buy on the offer price and sell on the bid price. The `QuoteRequest` message will always have the type "quoteresponse" and the "data" field will contain a dictionary with the following fields:
- "pool_id": the pool id as a string. In testnet, this will be "WETH-USDC-common"
- "price": the price of the order as a string. This is the price that the taker is requesting to trade at. 
    - Prices should be interpreted as "full-amount", meaning if a taker wishes to buy 1.0 WETH, they will request the price shown at the 1.0 rung of liquidity rather than adding up the previous rungs of liquidity to get the price.
    - There are no partial fills. All orders are "Fill or Kill" orders. If the taker requests 1.0 WETH, they will receive 1.0 WETH at the price they requested or better OR they will have their trade rejected.
    - If the taker requests a price that is not available in the pool, the trade will be rejected.
- "quantity": the quantity of the order as a string. This is the quantity that the taker is requesting to trade.
    - The quantity requested may be any number greater than 0 and less than or equal to the maximum quantity available in the pool.
    - If the quantity requested is in-between two rungs of liquidity, round up to the next rung of liquidity.
- "quote_resp_id": a client generated unique identifier for the order as a string. This is a convenience to the taker to allow them to identify their orders in the event of a trade confirmation or rejection.
- "side": the side of the trade as a string. This will be either "BUY" or "SELL"
- "symbol": the trading pair as a string. In testnet, this will always be "WETH-USDC"
- "sending_time": the UTC timestamp in seconds when the order was sent as a float
- "wallet_id": the wallet address of the taker as a string. This must be the wallet ID of the taker that was registered with the platform

Because quotes on the alphastar platform are indicative, the taker must wait for the maker to accept or reject the trade before the trade is executed. The taker will receive a `TakerTradeMessage` from the pool with the maker's response.

## TakerTradeMessage
The TakerTradeMessage will have the following format:

```python
{
    "type": "takertrademessage",
    "data": {
        'executed_price': '0.0',  # the price of the trade that was executed as a string
        'executed_quantity': '0.0',  # the quantity of the trade that was executed as a string
        'maker_wallet_id': '',  # wallet address of the maker as a string
        'match_timestamp': 1712784337.795921,  # UTC timestamp in seconds as a float. The time the taker order and maker quote were matched in the pool
        'msg': 'Trade Miss: Price BUY is less than the best offer price 100.85',  # a system message as a string
        'pool_id': 'ETH-USD_common',  # pool id as a string
        'price': '100.77',  # the price of the order as a string provided by the taker's QuoteResponse message
        'quantity': '0.1',  # the quantity of the order as a string provided by the taker's QuoteResponse message
        'quote_id': 'quote_response_id',  # the quote_response_id of the taker's QuoteResponse message
        'side': 'BUY',  # the side of the trade as a string provided by the taker's QuoteResponse message
        'status': 'REJECT',  # the status of the trade as a string -- ACCEPT, REJECT
        'symbol': 'WETH-USDC',  # trading pair as a string provided by the taker's QuoteResponse message
        'taker_fee': '0.0',  # the taker fee amount on the trade in taker_fee_ccy terms as a string
        'taker_fee_ccy': 'USDC',  # the taker fee currency as a string -- for testnet will always be USDC
        'taker_timestamp': 1712784337.795392,  # UTC timestamp in seconds as a float. The time the taker order was sent to the pool
        'timestamp': 1712784337.795921,  # UTC timestamp in seconds as a float. The time the message was sent
        'type': 'TRADE_RESPONSE',  # the type of the message as a string -- TRADE_RESPONSE
        'wallet_id': 'taker_wallet'  # wallet address of the taker as a string provided by the taker's QuoteResponse message
    }
}
```
The TakerTradeMessage will always have the type "takertrademessage" and the "data" field will contain a dictionary with the following fields:
- "executed_price": the price of the trade that was executed as a string. This is the price that the trade was executed at. If the trade was rejected, this will be set to "0.0". If the trade was accepted the price will always be equal to or better than the price requested by the taker.
- "executed_quantity": the quantity of the trade that was executed as a string. This is the quantity that was matched between the taker and the maker. If the trade was rejected, this will be set to "0.0". If the trade was accepted the quantity will always be equal to the quantity requested by the taker.
- "maker_wallet_id": the wallet address of the maker as a string. This is the wallet address of the maker that was matched with the taker.
    - If the trade missed, or was not matched in the pool this will be an empty string
    - If the trade matched, this will be the wallet address of the maker that was matched with the taker, regardless of whether they accept or reject the trade.
- "match_timestamp": the UTC timestamp in seconds when the taker order and maker quote were matched in the pool as a float
- "msg": a system message as a string. This message will provide the taker with information on why the trade was rejected or missed.
- "pool_id": the pool id as a string. In testnet, this will be "WETH-USDC-common"
- "price": the price of the order as a string. This is the price that the taker requested to trade at.
- "quantity": the quantity of the order as a string. This is the quantity that the taker requested to trade.
- "quote_id": the quote_id of the taker's QuoteResponse message. This is the quote_id that the taker provided in the QuoteResponse message.
- "side": the side of the trade as a string. This will be either "BUY" or "SELL"
- "status": the status of the trade as a string. This will be one of the following values:
    - "ACCEPT": the trade was accepted by the maker and executed. 
    - "REJECT": the trade was rejected by the maker OR the trade missed and was not matched in the pool. 
- "symbol": the trading pair as a string. In testnet, this will always be "WETH-USDC"
- "taker_fee": the taker fee amount on the trade in taker_fee_ccy terms as a string. This fee is deducted from the taker's account when the trade is executed.
- "taker_fee_ccy": the taker fee currency as a string. For testnet, this will always be "USDC"
- "taker_timestamp": the UTC timestamp in seconds when the taker order was sent to the pool as a float
- "timestamp": the UTC timestamp in seconds when the message was sent as a float
- "type": the type of the message as a string. This will always be "TRADE_RESPONSE"
- "wallet_id": the wallet address of the taker as a string. This must be the wallet ID of the taker that was registered with the platform


## Running a taker strategy
- see examples/dcn_taker.py
- must set environment variable TAKER_PRIVATE_KEY to run script.
```python
TAKER_PRIVATE_KEY=xxx python3 examples/dcn_taker.py 
```


# Trading examples 
We provide a couple of basic examples to get you started and see how you might build a simple sytem to interact with alphastars matching engine.

We use websocket endpoints for you to connect to and send/receive messages. There are three of interest and we provide code exmaple of how one might interact with them.
```python  
ws://dcn.alpha.deepqdigital.net/ws/marketdata
ws://dcn.alpha.deepqdigital.net/ws/maker
ws://dcn.alpha.deepqdigital.net/ws/taker
```

## REST endpoints
There are REST endpoints where you can request withdrawal, deposit and see balances for your account (wallet address).
```http://dq-alpha.deepqdigital.net/docs```
