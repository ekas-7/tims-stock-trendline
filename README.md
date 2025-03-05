# Tim's Stock Trendline

A dummy stock price viewer application built for demonstration in Electrothon hackathon.

## Overview

This project aims to illustrate the basic concepts and ideas that go while designing an application. The primary focus is how applications are conceived, designed, and improved over time.

## Installation

Fork or download the repository to your local machine to get started. Update the `.env.example` to correctly point towards your postgresql server. Afterwards, execute the following commands to set up the project:
```bash
# Clone the repository
git clone https://github.com/<yourusername>/tims-stock-trendline.git

# Navigate to the project directory
cd tims-stock-trendline

# Install dependencies
make dev

# Update postgresql schema with necessary migrations
make migrate
```

## Project Structure
Project tree structure is as follows:
```
tims-stock-trendline/
├── 1. The Beginning/                       # The first steps
├── 2. The SSE Revolution/                  # The second step, I guess
├── 3. You should try LISTENing/            # This has to be good
├── backend/                                # Flask application project
├── migrations/                             # Database migrations and trigger setup
├── pyproject.toml                          # Base application dependencies and configuration
├── Makefile                                # For making your life easier
└── README.md                               # Project documentation
```

# Getting Started
In order to start the backend server, execute the following command:
```bash
# Use Makefile to start the flask application at port 8080
make run

# OR, if you feel like a pro
uv run flask run --port 8080 --reload
```

The three implementations can be viewed under:
- [The Beginning](1.%20The%20Beginning/)
- [The SSE Revolution](2.%20The%20SSE%20Revolution/)
- [You should try LISTENing](3.%20You%20should%20try%20LISTENing/)

## License

This project is licensed under the MIT License.
