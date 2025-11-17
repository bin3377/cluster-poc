from typing import List

import pandas as pd
from pandas import DataFrame
from sklearn.cluster import KMeans

from app.models.carpool import (
    CarpoolRequest,
    CarpoolResponse,
    Trip,
    Vehicle,
    VehiclePlan,
)
from app.utils.timeaddr import get_datetime_by_address


async def calculate(request: CarpoolRequest) -> CarpoolResponse:
    df = prepare_df(request)
    df = apply_clustering(df, len(request.vehicles))

    return CarpoolResponse(date=request.date, plan=[])


def prepare_df(request: CarpoolRequest) -> DataFrame:
    """
    Prepare Dataframe with reuqest

    Converts raw data & time into full datetime fields.
    Retrieving only relevant information: Pick-up times, Appointment times (if exist),
    Pickup Latitude, Pickup Longitude
    """

    df = pd.DataFrame([b.model_dump() for b in request.bookings])
    df["raw"] = request.bookings

    df["pickup_datetime"] = None  # default None (Flexible)

    try:
        df["pickup_datetime"] = df.apply(
            lambda row: get_datetime_by_address(
                request.date, str(row["pickup_time"]), str(row["pickup_address"])
            ),
            axis=1,
        )

    except Exception as err:
        print("Warning: parsing pickup time failed:", err)

    df["appointment_datetime"] = None  # default None

    try:
        df["appointment_datetime"] = df.apply(
            lambda row: get_datetime_by_address(
                request.date,
                str(row["appointment_time"]),
                str(row["dropoff_address"]),
            ),
            axis=1,
        )
    except Exception as err:
        print("Warning: parsing appointment time failed:", err)

    print(df)

    return df


def apply_clustering(df: DataFrame, n_clusters: int) -> DataFrame:
    """
    Clustering bookings to groups geographically based on their pickup coordinates with K-means++

    Args:
        - df = subsetted dataframe from Step 1.
        - n_clusters = # of clusters will be divied into

    Returns:
        - dataframe with new column to assign clients to their respective clusters
    """

    coords = df[["pickup_latitude", "pickup_longitude"]]  # Retrieve coords from the df
    kmeans = KMeans(
        n_clusters=n_clusters, init="k-means++"
    )  # apply K-means++ clustering algorithm
    df["cluster"] = kmeans.fit_predict(
        coords
    )  # append a column to the dataframe with clustering assignments

    print(df)

    return df  # return dataframe


def group_by_time(df: DataFrame, time_threshold_minutes: int = 30):
    """
    Group by pickup time (chaining logic)

    "Chaining" ensures that clients within the same cluster are also close in pickup time (default window = 30 min)
    Sort clients first within their clusters.
    Grouping clients by time groups within their respective clusters.
    This helps enforce time constraints for efficient carpooling.

    Sorts clients within each cluster by pickup time, then splits them into 30-minute windows.
        •	Ensures clients in a group are picked up close in time
        •	Adds a Time Group ID column
        •	Each (Cluster, Time Group) combo is a candidate carpool
    """

    df = df.sort_values("pickup_datetime").copy()
    time_groups = []
    group_id = 1
    prev_time = df.iloc[0]["pickup_datetime"]
    time_groups.append(group_id)
    for i in range(1, len(df)):
        curr_time = df.iloc[i]["pickup_datetime"]

        if (curr_time - prev_time).total_seconds() / 60 <= time_threshold_minutes:
            time_groups.append(group_id)
        else:
            group_id += 1
            time_groups.append(group_id)
        prev_time = curr_time
    df["time_group"] = time_groups

    print(df)

    return df


def get_vehicle_plans(df: DataFrame, vehicles: List[Vehicle]) -> List[VehiclePlan]:
    """
    Populate trips
    """

    vehicle_plans = []
    for vehicle in vehicles:
        vehicle_plans.append(VehiclePlan(vehicle=vehicle, trips=[]))

    n_vehicles = len(vehicles)
    idx_vehicle = 0

    for cluster_id in df["cluster"].unique():
        cluster_df = df[df["cluster"] == cluster_id].copy()
        cluster_df = group_by_time(cluster_df)
        vehicle_capacity = vehicles[idx_vehicle].capacity

        for time_group_id in cluster_df["time_group"].unique():
            tg_df = cluster_df[cluster_df["time_group"] == time_group_id].copy()
            if len(tg_df) <= vehicle_capacity:
                # Group is small enough, proceed as-is
                vehicle_plans[idx_vehicle].trips.append(
                    Trip(
                        bookings=tg_df.iloc[0]["raw"],
                    )
                )

            else:
                # Too many clients – split into sub groups based on vehicle capacity
                pass

        idx_vehicle = (idx_vehicle + 1) % n_vehicles

    return vehicle_plans
