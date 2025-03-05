from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_cors import CORS


# Define the database and migration objects
db = SQLAlchemy(model_class=type("NewBase", (DeclarativeBase,), {}))
cors = CORS()
migrate = Migrate()


# Stock Price Model
class StockPrice(db.Model):
    __tablename__ = "stock_price"

    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
