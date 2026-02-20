# agents_system.py
import asyncio
from uagents import Agent, Context, Model, Bureau
from typing import List, Optional

# -------------------
# KUKSA setup
# -------------------
from kuksa_client import KuksaClientThread
from kuksa_client.grpc import VSSClient, Datapoint 
import time

# Connect to the KUKSA Databroker
config = {
    "ip": "127.0.0.1",
    "port": 55555,
    "protocol": "grpc",  #Connecting with gRPC
}
client = KuksaClientThread(config)
client.start()
client.connect()

VSS= VSSClient('127.0.0.1', 55555)
VSS.connect()

VSS_SPEED = "Vehicle.Speed"
VSS_TRAVELED = "Vehicle.TraveledDistance"
VSS_SOC_PRIMARY = "Vehicle.Acceleration.Longitudinal"

# -------------------
# Constants
# -------------------
TOTAL_ROUTE_LENGTH = 153.0
CONSUMPTION_KWH_PER_KM = 0.15
CHARGING_POWER_KW = 20.0
DEFAULT_BATTERY_CAPACITY_KWH = 40.0
MIN_SOC_ARRIVAL = 15.0
MIN_SOC_FINISH = 30.0
FALLBACK_SPEED_KMH = 63.0
MAX_SOC_TARGET = 90.0


#--------------------
# Station Data
#--------------------
stations = [
    {"station_id": 1, "distance": 2.38},
    {"station_id": 5, "distance": 12.62},
    {"station_id": 8, "distance": 24.30},
    {"station_id": 11, "distance": 55.37},
    {"station_id": 14, "distance": 95.11},
]

# -------------------
# Message Models
# -------------------
class BestStationRequest(Model):
    pass

class StationBreakdown(Model):
    station_id: int
    distance_to_station_km: float
    time_to_station_h: float
    soc_at_arrival_percent: float
    charging_time_h: float
    time_to_destination_h: float
    final_soc_percent: float
    total_trip_time_h: float

class BestStationResponse(Model):
    best_station_id: Optional[int]
    charge_limit: Optional[float]
    breakdowns: List[StationBreakdown]


#defining VSSSubscription
class VSSSubscription:
    def __init__(self):
        # Starting dummy values; in real use, these come from vehicle sensors
        self.speed_kmh: Optional[float] = None
        self.travelled_km: Optional[float] = None
        self.soc_percent: Optional[float] = None
        

    def subscribe_current_values(self):
        # this method updates the parameters below continuously
        for updates in VSS.subscribe_current_values([
        'Vehicle.Speed', 'Vehicle.TraveledDistance', 'Vehicle.Acceleration.Longitudinal']):
            self.speed_kmh = float(updates['Vehicle.Speed'].value)*3.6  # Convert m/s to km/h
            self.travelled_km = float(updates['Vehicle.TraveledDistance'].value)/1000  # Convert m to km
            self.soc_percent = float(updates['Vehicle.Acceleration.Longitudinal'].value)
            break


def calculate_soc_drop(distance_km: float, battery_capacity_kwh: float) -> float:
    return (distance_km * CONSUMPTION_KWH_PER_KM / battery_capacity_kwh) * 100.0

def calculate_charging_time(soc_current: float, soc_target: float, battery_capacity_kwh: float) -> float:
    if soc_target <= soc_current:
        return 0.0
    energy_needed_kwh = (soc_target - soc_current) / 100.0 * battery_capacity_kwh
    return energy_needed_kwh / CHARGING_POWER_KW

vss = VSSSubscription()
vss.subscribe_current_values()


# -------------------
# Optimizer Agent
# -------------------
optimizer = Agent(name="optimizer", port=8001, seed="optimizer-seed")

#starts this 
@optimizer.on_message(model=BestStationRequest, replies=BestStationResponse)
async def handle_request(ctx: Context, sender: str, msg: BestStationRequest):
    ctx.logger.info("Received best station request")

    #get current values from KUKSA
    vss.subscribe_current_values()

    # Extract vehicle data (fallbacks if needed)
    speed_kmh = vss.speed_kmh if vss.speed_kmh and vss.speed_kmh > 0 else FALLBACK_SPEED_KMH
    traveled_km = vss.travelled_km if vss.travelled_km is not None else 0.0
    soc_percent = vss.soc_percent if vss.soc_percent is not None else 0.0
    battery_capacity = DEFAULT_BATTERY_CAPACITY_KWH
    if soc_percent is None or soc_percent <= 0.0:
        ctx.logger.error("Invalid SoC reading")
        return

    #intializing values
    best_station_id = None
    best_charge_limit = None
    best_total_time = float("inf")
    breakdowns: List[StationBreakdown] = []
    battery_capacity = DEFAULT_BATTERY_CAPACITY_KWH

    #running loop to select best station
    for s in stations:
        station_id = s["station_id"]
        station_distance = s["distance"]
        distance_to_station = station_distance - traveled_km
        
        #eliminating station that are crossed
        if distance_to_station < 0:
            continue

        time_to_station = distance_to_station / speed_kmh
        soc_at_station = soc_percent - calculate_soc_drop(distance_to_station, battery_capacity)

        #eliminating stations where SoC at reaching station is below threshold
        if soc_at_station < MIN_SOC_ARRIVAL:
            continue

        distance_rest = TOTAL_ROUTE_LENGTH - station_distance #reaminingd distance to be traveled
        soc_target = min(MAX_SOC_TARGET, calculate_soc_drop(distance_rest, battery_capacity) + MIN_SOC_FINISH)
        charging_time = calculate_charging_time(soc_at_station, soc_target, battery_capacity)
        time_to_finish = distance_rest / speed_kmh
        final_soc = max(MIN_SOC_FINISH, round(soc_target - calculate_soc_drop(distance_rest, battery_capacity), 2))
        total_time = time_to_station + charging_time + time_to_finish

        breakdowns.append(StationBreakdown(
            station_id=station_id,
            distance_to_station_km=round(distance_to_station, 2),
            time_to_station_h=round(time_to_station, 2),
            soc_at_arrival_percent=round(soc_at_station, 2),
            charging_time_h=round(charging_time, 2),
            time_to_destination_h=round(time_to_finish, 2),
            final_soc_percent=final_soc,
            total_trip_time_h=round(total_time, 2),
        ))

        #appending best station
        if total_time < best_total_time:
            best_total_time = total_time
            best_station_id = station_id
            best_charge_limit = soc_target

    if best_station_id is None:
        ctx.logger.error("No station found")
        return

    await ctx.send(sender, BestStationResponse(
        best_station_id=best_station_id,
        charge_limit=best_charge_limit,
        breakdowns=breakdowns
    ))

# -------------------
# Requester Agent
# -------------------
requester = Agent(name="requester", port=8002, seed="requester-seed")
THRESHOLD = 25.0

@requester.on_interval(period=5.0)  # check every 5s
async def check_soc(ctx: Context):
    vss.subscribe_current_values()
    soc = vss.soc_percent #get SoC from KUKSA
    print(soc)
    if soc is not None and soc < THRESHOLD:
        ctx.logger.info(f"SoC low ({soc:.2f}%), requesting optimizer")
        await ctx.send(optimizer.address, BestStationRequest())

#request for charging through Optimizer Agent
@requester.on_message(model=BestStationResponse)
async def handle_response(ctx: Context, sender: str, msg: BestStationResponse):
    ctx.logger.info(f"Booking successful → Best station {msg.best_station_id} with charge limit {msg.charge_limit}")
    #publishing value through VSS
    client.setValue('Vehicle.CurrentLocation.Longitude', msg.best_station_id)
    client.setValue('Vehicle.Acceleration.Vertical', msg.charge_limit)
    for b in msg.breakdowns:
        ctx.logger.info(str(b))
    

# -------------------
# Run both agents
# -------------------
if __name__ == "__main__":
    bureau = Bureau()
    bureau.add(optimizer)
    bureau.add(requester)
    bureau.run()