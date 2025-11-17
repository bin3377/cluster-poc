"""
Booking models
"""

# from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Vehicle(BaseModel):
    id: str
    driver_name: Optional[str] = None
    capacity: int


class Booking(BaseModel):
    """Booking model representing a single booking"""

    id: str
    client_name: str

    pickup_time: Optional[str]  # H:mm AM format
    pickup_address: str
    pickup_latitude: float
    pickup_longitude: float

    appointment_time: Optional[str]  # H:mm AM format
    dropoff_address: str
    dropoff_latitude: float
    dropoff_longitude: float

    ontime: Optional[bool] = None


class ClusterRequest(BaseModel):
    """ClusterRequest model representing the json request to the cluster API"""

    date: str  # MM/DD/YYYY format
    bookings: List[Booking]
    vehicles: List[Vehicle]


class Trip(BaseModel):
    """Trip model representing a single trip on a vehicle"""

    bookings: List[Booking]
    distance: float = 0.0
    duration: float = 0.0
    start_time: str = ""  # H:mm AM format
    end_time: str = ""  # H:mm AM format


class VehiclePlan(BaseModel):
    """VehiclePlan model representing a single vehicle"""

    vehicle: Vehicle
    trips: List[Trip]


class ClusterResponse(BaseModel):
    """ClusterResponse model representing the json response from the cluster API"""

    date: str  # MM/DD/YYYY format
    plan: List[VehiclePlan]
