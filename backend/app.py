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
