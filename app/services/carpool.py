from datetime import timedelta
from typing import Dict, List, Optional

import pandas as pd
from pandas import DataFrame
from sklearn.cluster import KMeans

from app.models.carpool import (
    CarpoolConfig,
    CarpoolRequest,
    CarpoolResponse,
    Trip,
    Vehicle,
    VehiclePlan,
)
from app.utils.timeaddr import get_datetime_by_address


async def calculate(request: CarpoolRequest) -> CarpoolResponse:
    df = prepare_df(request)
    df = group_same_addresses(df)
    if request.config is None:
        request.config = CarpoolConfig()
    if request.config.pool_neighbors:
        df = group_close_coordinates(df, request.config.geo_clusters)
    plan = assign_to_vehicle(df, request.vehicles, request.config.max_wait_minutes)

    write_result_to_df(df, plan)
    print("\n\n")
    print(
        df[
            [
                "id",
                "client_name",
                "pickup_time",
                "cluster_id",
                "group_key",
                "vehicle_id",
                "trip_id",
            ]
        ]
    )
    print("\n\n")

    return CarpoolResponse(date=request.date, plan=plan)


def prepare_df(request: CarpoolRequest) -> DataFrame:
    """
    Prepare Dataframe with reuqest

    Converts raw data & time into full datetime fields.
    Retrieving only relevant information: Pick-up times, Appointment times (if exist),
    Pickup Latitude, Pickup Longitude
    """

    df = pd.DataFrame([b.model_dump() for b in request.bookings])
    df["raw"] = request.bookings

    def safe_get_datetime(date, time_str, address):
        try:
            return get_datetime_by_address(date, str(time_str), str(address))
        except Exception as e:
            print("Failed:", time_str, address, "=>", e)
            return None

    df_filtered = df[~df["pickup_time"].isin([None, "", "OPEN"])]

    df["pickup_datetime"] = df_filtered.apply(
        lambda row: safe_get_datetime(
            request.date, row["pickup_time"], row["pickup_address"]
        ),
        axis=1,
    )

    df_filtered = df[~df["appointment_time"].isin([None, "", "OPEN"])]

    df["appointment_datetime"] = df_filtered.apply(
        lambda row: safe_get_datetime(
            request.date, row["appointment_time"], row["dropoff_address"]
        ),
        axis=1,
    )

    # print(df[["pickup_datetime", "appointment_datetime"]])

    return df


def group_same_addresses(df: DataFrame) -> DataFrame:
    """
    Group bookings by same dropoff address then same pickup address

    """

    # 1. count addresses
    drop_counts = df["dropoff_address"].value_counts()
    pickup_counts = df["pickup_address"].value_counts()

    cluster_id = 1

    # 2. group same dropoff_address if has multiple entries
    for addr, cnt in drop_counts.items():
        if cnt > 1:
            mask = df["dropoff_address"] == addr
            df.loc[mask, "cluster_id"] = cluster_id
            df.loc[mask, "group_key"] = "DROPOFF=" + addr
            cluster_id += 1

    # 3. group same pickup_address if has multiple entries and not grouped yet
    for addr, cnt in pickup_counts.items():
        if cnt > 1:
            mask = (df["cluster_id"].isna()) & (df["pickup_address"] == addr)
            if mask.sum() > 0:
                df.loc[mask, "cluster_id"] = cluster_id
                df.loc[mask, "group_key"] = "PICKUP=" + addr
                cluster_id += 1

    # print(df[["client_name", "cluster_id"]])

    return df


def group_close_coordinates(
    df: DataFrame,
    n_clusters=8,
    init="k-means++",
    n_init="auto",
    max_iter=300,
    verbose=0,
    random_state=None,
    algorithm="lloyd",
) -> DataFrame:
    """
    Group bookings geographically based on their pickup coordinates with K-means++
    """

    # 1. operate only 'cluster_id' is NA
    mask = df["cluster_id"].isna()
    df_na = df[mask]
    if df_na.empty:
        return df

    if len(df_na) < n_clusters:
        return df

    # 2. find max of cluster_id as the KMeans output start index
    if df["cluster_id"].dropna().empty:
        start = 1
    else:
        start = int(df["cluster_id"].dropna().max()) + 1

    # 3. KMeans clustering on coordinates
    coords = df_na[["pickup_latitude", "pickup_longitude"]]
    kmeans = KMeans(
        n_clusters=n_clusters,
        init=init,
        n_init=n_init,
        max_iter=max_iter,
        verbose=verbose,
        random_state=random_state,
        algorithm=algorithm,
    )
    labels = kmeans.fit_predict(coords)

    # 4. write back to df['cluster_id']
    df.loc[mask, "cluster_id"] = labels + start
    df.loc[mask, "group_key"] = "GEO-" + labels.astype(str)

    # print(df[["pickup_latitude", "pickup_longitude", "cluster_id"]])

    return df


def _find_vehicle_idx_with_less_trips(
    vehicles: List[Vehicle], result: Dict[Vehicle, List[Trip]]
) -> int:
    min = 999999999
    for i, v in enumerate(vehicles):
        if not result.get(v):
            return i
        trips = result.get(v)
        if len(trips) < min:
            min = len(trips)
            min_idx = i
    return min_idx


def assign_bookings_to_vehicles(
    df: DataFrame,
    vehicles: List[Vehicle],
    result: Dict[Vehicle, List[Trip]],
    max_wait_minutes: int,
):
    # print("assign_bookings_to_vehicles", len(df))
    # 1. divide into df with pickup_datetime (sort by time) and no pickup_datetime (OPEN)
    df_has_pickup = (
        df[df["pickup_datetime"].notna()].sort_values("pickup_datetime").copy()
    )
    df_no_pickup = df[df["pickup_datetime"].isna()].copy()

    # 2. Greedy grouping for bookings has pickup_time
    idx_vehicle = _find_vehicle_idx_with_less_trips(vehicles, result)
    current_vehicle = vehicles[idx_vehicle]
    current_trip: Optional[Trip] = None

    def close_current_vehicle():
        # close current vehicle and round robin to the next vehicle
        nonlocal current_trip, idx_vehicle, current_vehicle, result

        if current_trip:
            result[current_vehicle].append(current_trip)
            idx_vehicle = (idx_vehicle + 1) % len(vehicles)
            current_vehicle = vehicles[idx_vehicle]
        current_trip = None

    for _, row in df_has_pickup.iterrows():
        if not current_trip:
            # start from empty
            current_trip = Trip(
                bookings=[row["raw"]],
                start_time=row["pickup_datetime"],
            )

        elif (
            row["pickup_datetime"] - current_trip.start_time
            <= timedelta(minutes=max_wait_minutes)
            and current_vehicle.capacity
            >= current_trip.total_passengers + row["passenger_count"]
        ):
            # check time window and capacity
            current_trip.bookings.append(row["raw"])

        else:
            # start a new trip
            close_current_vehicle()
            current_trip = Trip(
                bookings=[row["raw"]],
                start_time=row["pickup_datetime"],
            )

    close_current_vehicle()

    # 3. Fill bookings without pickup_time

    for _, row in df_no_pickup.iterrows():
        placed = False

        # try exist trips first
        for v in vehicles:
            for trip in result[v]:
                if v.capacity >= trip.total_passengers + row["passenger_count"]:
                    trip.bookings.append(row["raw"])
                    placed = True
                    break
            if placed:
                break

        if not placed:
            # start a new trip on current vehicle
            current_trip = Trip(
                bookings=[row["raw"]],
            )
            close_current_vehicle()


def write_result_to_df(df: DataFrame, plan: List[VehiclePlan]) -> DataFrame:
    for vp in plan:
        vehicle = vp.vehicle
        trips = vp.trips
        for trip_id, trip in enumerate(trips):
            for b in trip.bookings:
                mask = df["id"] == b.id
                df.loc[mask, "vehicle_id"] = vehicle.id
                df.loc[mask, "trip_id"] = trip_id

    df.sort_values(["vehicle_id", "trip_id", "pickup_datetime"], inplace=True)
    df.reset_index(inplace=True)
    # df["trip_id"] = df["trip_id"].where(df["trip_id"].notna(), None).astype(int)
    # df["cluster_id"] = (
    #     df["cluster_id"].where(df["cluster_id"].notna(), None).astype(int)
    # )

    return df


def assign_to_vehicle(
    df: DataFrame, vehicles: List[Vehicle], max_wait_minutes: int
) -> List[VehiclePlan]:
    """assign bookings to vehicles"""

    result: Dict[Vehicle, List[Trip]] = {}
    for vehicle in vehicles:
        result[vehicle] = []

    # 1. sort vehicles by capacity
    vehicles = sorted(vehicles, key=lambda v: -v.capacity)

    # 2. assign clustered bookings as multi-load trips
    df_clustered = df[df["cluster_id"].notna()]

    # print("df_clustered", len(df_clustered))

    for cluster_id in df_clustered["cluster_id"].unique():
        cluster_df = df_clustered[df_clustered["cluster_id"] == cluster_id].copy()
        # print(cluster_df[["client_name", "cluster_id", "pickup_datetime"]])
        assign_bookings_to_vehicles(cluster_df, vehicles, result, max_wait_minutes)

    # 3. assign non-clustered bookings as single-load trips
    df_non_clustered = df[df["cluster_id"].isna()].sort_values("passenger_count")

    idx_vehicle = _find_vehicle_idx_with_less_trips(vehicles, result)
    current_vehicle = vehicles[idx_vehicle]

    for _, row in df_non_clustered.iterrows():
        current_trip = Trip(
            bookings=[row["raw"]],
        )
        result[current_vehicle].append(current_trip)
        idx_vehicle = (idx_vehicle + 1) % len(vehicles)
        current_vehicle = vehicles[idx_vehicle]

    return [VehiclePlan(vehicle=v, trips=t) for v, t in result.items()]
