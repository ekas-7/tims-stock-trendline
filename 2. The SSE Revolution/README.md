# The SSE Revolution

Tim realizes that he needs a new plan that allows the server to respond with multiple events at a time, without the need for the client to make multiple requests. He decides to use Server-Sent Events (SSE) to solve this problem.

## Overview

Server-Sent Events (SSE) is a technology that allows the server to send events to the client over a single, long-lived connection. The client can then listen for these events and update the UI accordingly. SSE is a great fit for Tim's application because it allows the server to push multiple events to the client without the need for the client to make multiple requests.

## The Server Side Implementation

Tim updates his Flask application to use SSE. He creates a new endpoint that streams stock prices to the client using the `text/event-stream` content type.

```python
@app.route("/tracker/v2", methods=["GET"])
def finally_we_can_sse():
    """Uses SSE event stream for updating the stock prices"""

    def _streamer(last_event_id: int | None = None):
        with app.app_context():
            base_query = StockPrice.query.order_by(StockPrice.created_at.asc())
            if last_event_id:
                base_query = base_query.filter(StockPrice.id > last_event_id)
            for price in base_query:
                time.sleep(1)  # Simulate a long running process
                yield f"id: {price.id}\ndata: {json.dumps(stock_to_dict(price), default=str)}\n\n"

    last_event_id = request.headers.get("Last-Event-ID")
    return _streamer(last_event_id), 200, {"Content-Type": "text/event-stream"}
```

### The SSE Stream Format

The server sends events to the client in the following format:

```
id: 1
data: {"id": 1, "price": 150.0, "created_at": "2021-01-01T00:00:00"}

id: 2
data: {"id": 2, "price": 151.0, "created_at": "2021-01-01T00:00:01"}

...
```

The `id` field is used to keep track of the last event sent to the client. The client can send this `id` back to the server in the `Last-Event-ID` header to resume the stream from where it left off.

## The Polling Conundrum Revisited

Tim is happy with the new implementation. The server is now able to push multiple events to the client without the need for the client to make multiple requests. The client can now listen for these events and update the UI accordingly. However, this approach still does not address the problem with the database queries. Tim again needs a new plan.