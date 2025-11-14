"""
Booking models
"""

# from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Booking(BaseModel):
    """Booking model representing a single booking"""

    client_name: str

    pickup_time: Optional[str]  # H:mm AM format
    pickup_address: str
    pickup_latitude: str
    pickup_longitude: str

    appointment_time: Optional[str]  # H:mm AM format
    dropoff_address: str
    dropoff_latitude: str
    dropoff_longitude: str


class ClusterRequest(BaseModel):
    """ClusterRequest model representing the json request to the cluster API"""

    date: str  # MM/DD/YYYY format
    bookings: List[Booking]


class Trip(BaseModel):
    """Trip model representing a single trip on a vehicle"""

    bookings: List[Booking]
    distance: float
    duration: float


class Vehicle(BaseModel):
    """Vehicle model representing a single vehicle"""

    driver_name: str
    trips: List[Trip]


class ClusterResponse(BaseModel):
    """ClusterResponse model representing the json response from the cluster API"""

    date: str  # MM/DD/YYYY format
    vehicles: List[Vehicle]
