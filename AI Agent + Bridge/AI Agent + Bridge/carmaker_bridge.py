import time
from pycarmaker import CarMaker, Quantity
from kuksa_client import KuksaClientThread
from kuksa_client.grpc import VSSClient, Datapoint 
import time

# Connect to the KUKSA Databroker with grpc 
config = {
    "ip": "127.0.0.1",
    "port": 55555,
    "protocol": "grpc",  
}
client = KuksaClientThread(config)
client.start()
client.connect()

VSS= VSSClient('127.0.0.1', 55555)
VSS.connect()

#connect to CarMaker
cm = CarMaker("localhost", 16660)
cm.connect()

SoC = Quantity("PT.BCU.BattHV.SOC", Quantity.FLOAT)
Distance = Quantity("Car.Distance", Quantity.FLOAT)
Vehicle_Speed = Quantity("Car.v", Quantity.FLOAT)
charge_Request = Quantity("Car.Charge_Request", Quantity.FLOAT)
Charge_Limit = Quantity("Car.Charge_Limit", Quantity.FLOAT)

#to clear gargbage values
Vehicle_Speed.data = -1.0

#subscribe
cm.subscribe(SoC)
cm.subscribe(Distance)
cm.subscribe(Vehicle_Speed)


#INTIALIZING CHARGE REQUEST VALUES
client.setValue('Vehicle.CurrentLocation.Longitude', 0)
cm.DVA_write(charge_Request, 0)


#intialize charge_request for running loop till value is not updated from AI Agent
charge_request = 0
# Push the values to KUKSA till AI agent return values
while charge_request == 0:
    cm.read()
    client.setValue('Vehicle.Speed', Vehicle_Speed.data)
    client.setValue('Vehicle.Acceleration.Longitudinal', SoC.data)
    client.setValue('Vehicle.TraveledDistance', Distance.data)
    time.sleep(1)

#Get values
    for updates in VSS.subscribe_current_values([
            'Vehicle.CurrentLocation.Longitude', 'Vehicle.Acceleration.Vertical'
        ]):
            charge_request = int(updates['Vehicle.CurrentLocation.Longitude'].value)
            charge_limit = int(updates['Vehicle.Acceleration.Vertical'].value)
            break

print(charge_request)
print(charge_limit)
#Write value of variable in CarMaker
cm.DVA_write(charge_Request, charge_request)
cm.DVA_write(Charge_Limit, charge_limit)

