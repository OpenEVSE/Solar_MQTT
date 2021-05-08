from sense_energy import Senseable
import time
import requests
import json
import paho.mqtt.client as mqtt
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sense_email = "user@domain.com" #Sense Username
sense_password = "password"         #Sense Username


sense = Senseable()
sense.authenticate(sense_email, sense_password)
sense.update_realtime()
#sense.update_trend_data()


mqtt_broker = "mqtt.domain.com"               #MQTT broker
mqtt_port = 8883                                #MQTT port standard 1883 or secure 8883
mqtt_user = "username"                          #MQTT username
mqtt_password = "password"                 #MQTT password
mqtt_topic = "sense/"                           #MQTT base topic

def on_connect(client, userdata, flags, rc):     # Setup for MQTT connection
    if rc==0:
        client.connected_flag=True 
    else:
        print("Bad connection Returned code=",rc)
mqtt.Client.connected_flag=False 

client = mqtt.Client('openevse') 
client.username_pw_set(username = mqtt_user,password = mqtt_password)    #For MQTT connections with username and passrord
client.on_connect=on_connect  
client.connect(mqtt_broker, mqtt_port)
client.loop_start()

print("Connecting to broker ",mqtt_broker)
client.connect(mqtt_broker)     
while not client.connected_flag: 
    time.sleep(1)
while client.connected_flag:
    ret= client.publish(mqtt_topic +"loadPower", sense.active_power)
    ret= client.publish(mqtt_topic +"solarPower", sense.active_solar_power)
    ret= client.publish(mqtt_topic +"ExcessPower", sense.active_solar_power - sense.active_power)
    print ("Solar Power", sense.active_solar_power, "watts")
    print ("Total Load", sense.active_power, "watts")
    print ("Excess Power", sense.active_solar_power - sense.active_power, "watts")
    print ("Published to MQTT")
    print ()
    time.sleep(5)
	
client.loop_stop()    #Stop loop 
client.disconnect() # disconnect
