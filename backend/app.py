from flask import Flask, request
from .extensions import db, migrate, cors, StockPrice
import time
from dotenv import load_dotenv
import json
import os


# Load the environment variables and initialize flask app
load_dotenv(dotenv_path=".env.example")
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("POSTGRESQL_DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Setup extensions
db.init_app(app)
migrate.init_app(app, db)
cors.init_app(app)


def stock_to_dict(price):
    return {"id": price.id, "price": price.price, "created_at": price.created_at}


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


@app.route("/tracker/v3", methods=["GET"])
def listen_closely_to_postgres():
    """Uses Postgres LISTEN/NOTIFY to stream the stock prices"""

    def _streamer(last_event_id: int | None = None):
        # HINT: Check out redis pub/sub for inspiration
        with app.app_context():
            connection = db.engine.raw_connection()
            cursor = connection.cursor()

            cursor.execute('LISTEN "stock_price_insert";')
            connection.commit()
            while True:
                # No need to sleep here as the event is triggered by the database
                connection.poll()
                while connection.notifies:
                    notify = connection.notifies.pop(0)
                    id = json.loads(notify.payload)["id"]
                    yield f"id: {id}\ndata: {notify.payload}\n\n"

    last_event_id = request.headers.get("Last-Event-ID")
    return _streamer(last_event_id), 200, {"Content-Type": "text/event-stream"}


@app.route("/tracker/v4", methods=["GET"])
def pq_caching_tracker():
    """Uses PostgreSQL for caching stock prices to improve performance"""

    def _streamer(last_event_id: int | None = None):
        with app.app_context():
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            
            # Create a temporary table for caching if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_price_cache (
                    id SERIAL PRIMARY KEY,
                    price_id INTEGER REFERENCES stock_price(id),
                    payload JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_stock_price_cache_price_id ON stock_price_cache(price_id)
            """)
            
            # Create or replace a function to update the cache
            cursor.execute("""
                CREATE OR REPLACE FUNCTION update_stock_price_cache() RETURNS TRIGGER AS $$
                BEGIN
                    INSERT INTO stock_price_cache (price_id, payload)
                    VALUES (NEW.id, (SELECT json_build_object(
                        'id', NEW.id,
                        'price', NEW.price,
                        'created_at', NEW.created_at
                    )));
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            # Create trigger if it doesn't exist (first check if it exists)
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_trigger 
                    WHERE tgname = 'stock_price_cache_trigger'
                )
            """)
            trigger_exists = cursor.fetchone()[0]
            
            if not trigger_exists:
                cursor.execute("""
                    CREATE TRIGGER stock_price_cache_trigger
                    AFTER INSERT ON stock_price
                    FOR EACH ROW
                    EXECUTE FUNCTION update_stock_price_cache();
                """)
            
            connection.commit()
            
            # Function to clean up old cache entries (run periodically)
            cursor.execute("""
                CREATE OR REPLACE FUNCTION cleanup_stock_price_cache() RETURNS void AS $$
                BEGIN
                    DELETE FROM stock_price_cache 
                    WHERE created_at < NOW() - INTERVAL '1 day'
                    AND accessed_at < NOW() - INTERVAL '1 hour';
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            # Set up LISTEN/NOTIFY for cache invalidation
            cursor.execute('LISTEN "stock_price_insert";')
            connection.commit()
            
            # Get initial data from cache if available
            base_query = """
                SELECT payload FROM stock_price_cache
                WHERE price_id > %s
                ORDER BY price_id ASC
            """
            
            # Use 0 if last_event_id is None
            cursor.execute(base_query, (last_event_id or 0,))
            cached_results = cursor.fetchall()
            
            # Send cached results immediately
            for cached_result in cached_results:
                payload = cached_result[0]
                price_id = payload['id']
                
                # Update access time to indicate this cache entry was used
                cursor.execute("""
                    UPDATE stock_price_cache 
                    SET accessed_at = CURRENT_TIMESTAMP
                    WHERE price_id = %s
                """, (price_id,))
                connection.commit()
                
                yield f"id: {price_id}\ndata: {json.dumps(payload, default=str)}\n\n"
            
            # Then listen for new notifications
            last_processed_id = max([r[0]['id'] for r in cached_results]) if cached_results else (last_event_id or 0)
            
            while True:
                connection.poll()
                while connection.notifies:
                    notify = connection.notifies.pop(0)
                    payload = json.loads(notify.payload)
                    price_id = payload["id"]
                    
                    # Only process if this is a new price we haven't sent yet
                    if price_id > last_processed_id:
                        last_processed_id = price_id
                        
                        # Run cache cleanup occasionally (probabilistic to avoid doing it too often)
                        if price_id % 20 == 0:  # Every ~20 notifications
                            cursor.execute("SELECT cleanup_stock_price_cache()")
                            connection.commit()
                        
                        yield f"id: {price_id}\ndata: {notify.payload}\n\n"

    last_event_id = request.headers.get("Last-Event-ID")
    return _streamer(last_event_id), 200, {"Content-Type": "text/event-stream"}


