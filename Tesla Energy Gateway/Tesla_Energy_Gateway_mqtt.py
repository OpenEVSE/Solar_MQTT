import time
import requests
import json
import paho.mqtt.client as mqtt
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
 
powerwall_ip = "192.168.1.2"        # local IP address for Tesla energy gateway
powerwall_email = "name@domain.com" # local email for Tesla energy gateway
powerwall_password = "password"     # local password for Tesla energy gateway

mqtt_broker = "mqtt.domain.com"     #MQTT broker
mqtt_port = 8883                    #MQTT port standard 1883 or secure 8883
mqtt_user = "username"              #MQTT username
mqtt_password = "password"          #MQTT password
mqtt_topic = "Tesla_Energy/"        #MQTT base topic

baseline_load = 400                 # watts of baseline always on houshold load
target_soe = 90                     # battery % to target + and minus 5%

def on_connect(client, userdata, flags, rc):     # Setup for MQTT connection
    if rc==0:
        client.connected_flag=True 
    else:
        print("Bad connection Returned code=",rc)
mqtt.Client.connected_flag=False 

payload = {'username': 'customer', 'email': powerwall_email, 'password': powerwall_password, 'force_sm_off': False}
r = requests.post('https://' + powerwall_ip + '/api/login/Basic', verify = False, data = payload) # Authenticate to Tesla Energy Gateway

client = mqtt.Client('openevse') 
client.username_pw_set(username = mqtt_user,password = mqtt_password)    #For MQTT connections with username and password # out if no username/password
client.on_connect=on_connect  
client.connect(mqtt_broker, mqtt_port)
client.loop_start()

print("Connecting to broker ",mqtt_broker)
client.connect(mqtt_broker)     
while not client.connected_flag: 
    time.sleep(1)
while client.connected_flag:
    soe = requests.get('https://' + powerwall_ip + '/api/system_status/soe', verify=False, cookies = r.cookies)       #HTTP GET /api/system_status/soe
    meters = requests.get('https://' + powerwall_ip + '/api/meters/aggregates', verify=False, cookies = r.cookies)    #HTTP GET /api/meters/aggregates

    soe.json()
    soe_json = json.loads(soe.text)                 #parse JSON
    meters.json()
    meters_json = json.loads(meters.text)       # parse JSON
    
    site_json = meters_json["site"]                #Extract site JSON
    battery_json = meters_json["battery"]          #Extract battery JSON
    load_json = meters_json["load"]                #Extract load JSON
    solar_json = meters_json["solar"]		   #Extract solar JSON

    battery_soe = int(soe_json["percentage"])      #Extract Values
    site_power = int(site_json["instant_power"])
    battery_power = int(battery_json["instant_power"])
    battery_voltage = int(battery_json["instant_average_voltage"])
    battery_freq = int(battery_json["frequency"])
    load_power = int(load_json["instant_power"])
    solar_power = int(solar_json["instant_power"]) # End Extract Values

    if battery_soe < target_soe - 5: # Check Battery % reserve power to charge if below target
      print ("Charging Powerwall " + str(battery_soe) + "% " + str(battery_power) + " watts")
      if battery_power > 0:
        excess_power = solar_power - battery_power - 1800
      else:
        excess_power = solar_power - 1800
    if battery_soe > target_soe + 5: # Check Battery % alocate additional power to discharge if abeve target
      print ("Discharging Powerwall" + str(battery_soe) + "% "+ str(battery_power) + " watts")
      if battery_power > 0:
        excess_power = solar_power - battery_power + 200
      else:
        excess_power = solar_power + 200
    if battery_soe >= target_soe - 5 and battery_soe <= target_soe + 5: # Check Battery % reserve exact power to maintain if near target
     print ("Maintaining Powerwall" + str(battery_soe) + "% " + str(battery_power) + " watts")
     if battery_power > 0:
        excess_power = solar_power - battery_power - baseline_load
     else:
        excess_power = solar_power - baseline_load
	 
    print ("Grid Power   " + str(site_power) + " watts") # Print latest values
    print ("Solar Power  " + str(solar_power) + " watts")
    print ("Excess Power " + str(excess_power) + " watts")
	 
    ret= client.publish(mqtt_topic +"soe", battery_soe)  # Publish latest values to MQTT stats
    ret= client.publish(mqtt_topic +"sitePower", site_power)
    ret= client.publish(mqtt_topic +"batteryPower", battery_power)
    ret= client.publish(mqtt_topic +"loadPower", load_power)
    ret= client.publish(mqtt_topic +"solarPower", solar_power)
    ret= client.publish(mqtt_topic +"excessPower", excess_power)
    ret= client.publish(mqtt_topic +"voltage", battery_voltage)
    ret= client.publish(mqtt_topic +"frequency", battery_freq)
    print ("Published to MQTT")
    print ()
    time.sleep(5)
	
client.loop_stop()    #Stop loop 
client.disconnect() # disconnect
