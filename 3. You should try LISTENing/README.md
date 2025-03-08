# You should try LISTENing

Tim's ultimate plan. He decides to explore the **LISTEN/NOTIFY** feature of PostgreSQL to solve the problem with the database queries.

## Overview

**LISTEN/NOTIFY** is a feature of PostgreSQL that allows the database to send notifications to clients when certain events occur. It allows the server to passively listen for events and react to them in real-time. So, instead of the server constantly polling the database for new data, the database can notify the server when new data is available.

This feature is not just limited to PostgreSQL. It can be used with any database that supports triggers and notifications.

## The Server Side Implementation

For this approach to work, Tim needs to make a few changes to his Flask application. He starts with creating database triggers that will send notifications to the server when new stock prices are inserted into the database.

- The function `notify_stock_price_insert` sends a notification with the new stock data point.
    ```sql
    CREATE OR REPLACE FUNCTION notify_stock_price_insert()
    RETURNS TRIGGER AS $$
    BEGIN
        PERFORM pg_notify('stock_price_insert', row_to_json(NEW)::text);
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    ```

- The trigger `stock_price_insert_trigger` calls the function `notify_stock_price_insert` after an insert operation on the `stock_price` table.
    ```sql
    CREATE TRIGGER stock_price_insert_trigger
    AFTER INSERT ON stock_price
    FOR EACH ROW
    EXECUTE FUNCTION notify_stock_price_insert();
    ```

Tim then updates his Flask application to listen for these notifications and send them to the client using Server-Sent Events (SSE).

```python
@app.route("/tracker/v3", methods=["GET"])
def listen_closely_to_postgres():
    """Uses Postgres LISTEN/NOTIFY to stream the stock prices"""

    def _streamer(last_event_id: int | None = None):
        with app.app_context():
            connection = db.engine.raw_connection()
            cursor = connection.cursor()

            cursor.execute('LISTEN "stock_price_insert";')
            connection.commit()
            while True:
                connection.poll()
                while connection.notifies:
                    notify = connection.notifies.pop(0)
                    id = json.loads(notify.payload)["id"]
                    yield f"id: {id}\ndata: {notify.payload}\n\n"

    last_event_id = request.headers.get("Last-Event-ID")
    return _streamer(last_event_id), 200, {"Content-Type": "text/event-stream"}
```

## How to simulate

Start the server as usual. In another terminal, run the following command to simulate the insertion of stock prices into the database.

```bash
flask shell
```

This will open a Python shell. Run the following commands to insert some stock prices into the database.
```python
from backend.fixtures import load_slow_fixtures

load_slow_fixtures()
```

## Conclusion

Tim is happy.
