"""
Booking models
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Vehicle(BaseModel):
    id: str
    driver_name: Optional[str] = None
    capacity: int

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Vehicle) and self.id == other.id


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

    passenger_count: int = 1


class CarpoolRequest(BaseModel):
    """CarpoolRequest model representing the json request to the cluster API"""

    date: str  # MM/DD/YYYY format
    bookings: List[Booking]
    vehicles: List[Vehicle]


class Trip(BaseModel):
    """Trip model representing a carpooling trip of a vehicle"""

    bookings: List[Booking]
    distance: float = 0.0
    duration: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def total_passengers(self):
        return sum(b.passenger_count for b in self.bookings)


class VehiclePlan(BaseModel):
    """VehiclePlan model representing the plan for single vehicle"""

    vehicle: Vehicle
    trips: List[Trip]


class CarpoolResponse(BaseModel):
    """CarpoolResponse model representing the json response from the cluster API"""

    date: str  # MM/DD/YYYY format
    plan: List[VehiclePlan]
