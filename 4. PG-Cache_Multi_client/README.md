# Real-Time Stock Price Tracker

A Flask-based application that demonstrates different techniques for streaming real-time stock price data to a web client, with a focus on efficiency and performance.

## Features

- **Multiple Implementation Methods**: Four different approaches to real-time data streaming
- **PostgreSQL Integration**: Leverages PostgreSQL features for efficient data delivery
- **Server-Sent Events (SSE)**: Real-time updates without polling
- **PQ-Caching**: Optimized data access with PostgreSQL-based caching

## Implementation Methods

### 1. Simple Polling (`/tracker/v1`)
- Basic implementation using traditional HTTP polling
- Client periodically requests new data from the server
- Simulates a long-running process with artificial delay

### 2. Server-Sent Events (`/tracker/v2`)
- Uses SSE to stream stock prices to the client
- Establishes a persistent connection
- Server pushes data to the client as it becomes available
- Still queries the database directly for each record

### 3. PostgreSQL LISTEN/NOTIFY (`/tracker/v3`)
- Leverages PostgreSQL's LISTEN/NOTIFY feature for real-time updates
- Database sends notifications when new data is inserted
- Server listens for these notifications and forwards them to clients
- Eliminates the need for polling or repetitive database queries

### 4. PQ-Caching (`/tracker/v4`)
- Combines PostgreSQL's LISTEN/NOTIFY with a caching mechanism
- Pre-processes and caches stock price data in a dedicated table
- Uses database triggers to automatically populate the cache
- Provides immediate access to historical data with real-time updates
- Includes smart cache maintenance with usage tracking and periodic cleanup

## Setup and Configuration

### Prerequisites
- Python 3.10+
- PostgreSQL 13+
- Flask and required extensions

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/stock-price-tracker.git
   cd stock-price-tracker
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the database:
   ```bash
   # Create a PostgreSQL database
   createdb stock_tracker

   # Apply database migrations
   flask db upgrade
   ```

5. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env to set your PostgreSQL connection string
   ```

### Database Triggers Setup

For the LISTEN/NOTIFY feature (routes v3 and v4), you need to set up PostgreSQL triggers:

```sql
-- Function to send notifications on stock price insert
CREATE OR REPLACE FUNCTION notify_stock_price_insert()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('stock_price_insert', row_to_json(NEW)::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to call the notification function
CREATE TRIGGER stock_price_insert_trigger
AFTER INSERT ON stock_price
FOR EACH ROW
EXECUTE FUNCTION notify_stock_price_insert();
```

## Running the Application

1. Start the Flask server:
   ```bash
   flask run --port=8080
   ```

2. Open the HTML file in your browser:
   ```bash
   # For version 3 using LISTEN/NOTIFY
   open index.html
   
   # For version 4 using PQ-Caching
   open index_v4.html
   ```

## Simulating Data

Use the Flask shell to simulate the insertion of stock prices:

```bash
flask shell
```

Then run:
```python
from backend.fixtures import load_slow_fixtures

load_slow_fixtures()
```

## Performance Comparison

### Route 1 (Simple Polling)
- ❌ High server load due to frequent requests
- ❌ Inefficient use of resources
- ❌ Higher latency for updates

### Route 2 (Server-Sent Events)
- ✅ Reduced number of connections
- ✅ Lower network overhead
- ❌ Still queries database for each record

### Route 3 (PostgreSQL LISTEN/NOTIFY)
- ✅ Real-time updates
- ✅ Lower server load
- ✅ No polling required
- ❌ No efficient access to historical data

### Route 4 (PQ-Caching)
- ✅ Real-time updates
- ✅ Immediate access to historical data
- ✅ Reduced database load
- ✅ Optimized JSON processing
- ✅ Intelligent cache management
- ✅ Best overall performance

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.