# The Beginning

Tim starts with the idea of creating a stock trendline application. He starts with a simple polling mechanism to fetch stock prices from an external API.

## Overview

Long Polling is a technique used to reduce the number of requests made to the server. Instead of making a request every second, the client makes a request and the server holds the request until new data is available. This reduces the number of requests made to the server and is more efficient than traditional polling.

## The Server Side Implementation

Tim starts with a simple Flask application that fetches stock prices from an existing databse. If the client sends a `Last-Event-ID` header, the server will only return the stock prices that are newer than the `Last-Event-ID`.

```python
@app.route("/tracker/v1", methods=["GET"])
def simple_polling_tracker():
    """Simple polling to get the stock prices"""
    with app.app_context():
        last_event_id = request.headers.get("Last-Event-ID")
        base_query = StockPrice.query.order_by(StockPrice.created_at.asc())
        if last_event_id:
            base_query = base_query.filter(StockPrice.id > last_event_id)
        time.sleep(1)  # Simulate a long running process
        price = base_query.first()
        if price is None:
            return {}, 204
        return stock_to_dict(price), 200
```

## The Polling Conundrum

Tim is happy with the initial implementation, but he soon realizes that the server is still getting a lot of requests. Long Polling can only be used to reduce the number of requests, but it doesn't eliminate the problem. The server is still only able to respond back with a single stock price at a time.

Tim needs a new plan.