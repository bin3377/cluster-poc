# Cluster PoC

A proof-of-concept FastAPI application for carpool optimization. It takes a list of bookings and vehicles and generates an optimized plan for vehicle trips.

## Features

- Groups bookings by the same pickup/dropoff address.
- Clusters geographically close bookings using K-means (Optional).
- Assigns bookings to vehicles based on capacity and time windows.
- Provides a flexible configuration for the carpooling algorithm.

## API Endpoint

### `POST /api/v1/carpool`

Calculates the carpool plan.

**Request Body:**

```json
{
  "date": "MM/DD/YYYY",
  "bookings": [
    {
      "id": "string",
      "client_name": "string",
      "pickup_time": "H:mm AM/PM",
      "pickup_address": "string",
      "pickup_latitude": "float",
      "pickup_longitude": "float",
      "appointment_time": "H:mm AM/PM",
      "dropoff_address": "string",
      "dropoff_latitude": "float",
      "dropoff_longitude": "float",
      "passenger_count": "int"
    }
  ],
  "vehicles": [
    {
      "id": "string",
      "driver_name": "string",
      "capacity": "int"
    }
  ],
  "config": {
    "max_wait_minutes": "int",
    "pool_neighbors": "boolean",
    "geo_clusters": "int"
  }
}
```

**Response Body:**

```json
{
  "date": "MM/DD/YYYY",
  "plan": [
    {
      "vehicle": {
        "id": "string",
        "driver_name": "string",
        "capacity": "int"
      },
      "trips": [
        {
          "bookings": [
            {
              "id": "string",
              "client_name": "string",
              "pickup_time": "H:mm AM/PM",
              "pickup_address": "string",
              "pickup_latitude": "float",
              "pickup_longitude": "float",
              "appointment_time": "H:mm AM/PM",
              "dropoff_address": "string",
              "dropoff_latitude": "float",
              "dropoff_longitude": "float",
              "passenger_count": "int"
            }
          ],
          "start_time": "datetime"
        }
      ]
    }
  ]
}
```

## Getting Started

### Prerequisites

- Python 3.12+

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/bin3377/cluster-poc.git
    cd cluster-poc
    ```
2.  Install uv:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
3.  Create a virtual environment:
    ```bash
    uv venv
    ```
4.  Install the dependencies:
    ```bash
    uv sync
    ```

### Running the Application

```bash
uv run uvicorn main:app --reload --port 8080
```

The API will be available at `http://localhost:8080/docs`.

### Try example payload

```bash
curl -sS -X 'POST' \
  'http://localhost:8080/api/v1/carpool' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d @./example_request.json
```

## Project Structure

```
.
├── app
│   ├── models      # Pydantic models
│   ├── routers     # FastAPI routers
│   └── services    # Business logic
├── config
│   └── config.dev.yaml # Configuration files
├── main.py         # FastAPI application entrypoint
├── pyproject.toml  # Project metadata and dependencies
└── test            # Tests
```
