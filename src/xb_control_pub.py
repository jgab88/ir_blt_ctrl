import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import paho.mqtt.client as mqtt
import subprocess
import re

# MQTT Broker Configuration
MQTT_BROKER = "192.168.0.52"  # Replace with your MQTT broker IP address
MQTT_PORT = 1883  # Replace with your MQTT broker port

# Xbox Controller Configuration
EVTEST_CMD = ["sudo", "evtest", "/dev/input/event6"]  # Replace with the correct event device path

# MQTT Topics
LEFT_SPEED_TOPIC = "IR/Controller/Left/Speed"
LEFT_DIRECTION_TOPIC = "IR/Controller/Left/Direction"
RIGHT_SPEED_TOPIC = "IR/Controller/Right/Speed"
RIGHT_DIRECTION_TOPIC = "IR/Controller/Right/Direction"
DIRECTION_MODE_TOPIC = "IR/Controller/Dir_mode"

# Regular expressions for parsing evtest output
AXIS_RE = re.compile(r"type 3 \(EV_ABS\), code (\d+) \(ABS_(\w+)\), value (-?\d+)")
BUTTON_RE = re.compile(r"type 1 \(EV_KEY\), code (\d+) \(BTN_(\w+)\), value (-?\d+)")

# MQTT Client Setup
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d", rc)

client = mqtt.Client(transport="tcp")
client.on_connect = on_connect
client.connect(MQTT_BROKER, MQTT_PORT)
client.loop_start()

# Direction mode (True for forward, False for reverse)
direction_mode = True

# Function to parse evtest output and publish to MQTT topics
def parse_evtest_output(line):
    global direction_mode  # Declare direction_mode as global

    axis_match = AXIS_RE.search(line)
    button_match = BUTTON_RE.search(line)

    if axis_match:
        axis_code, axis_name, axis_value = axis_match.groups()
        axis_code = int(axis_code)
        axis_value = int(axis_value)

        if axis_name == "Z":
            if axis_code == 2:  # Left Bumper
                speed_value = axis_value if direction_mode else -axis_value
                client.publish(LEFT_SPEED_TOPIC, payload=str(speed_value))

        elif axis_name == "RZ":
            if axis_code == 5:  # Right Bumper
                speed_value = axis_value if direction_mode else -axis_value
                client.publish(RIGHT_SPEED_TOPIC, payload=str(speed_value))

    if button_match:
        button_code, button_name, button_value = button_match.groups()
        button_code = int(button_code)
        button_value = int(button_value)

        if button_name == "SOUTH" and button_value == 1:  # A button pressed
            direction_mode = not direction_mode
            client.publish(DIRECTION_MODE_TOPIC, payload=str(int(direction_mode)))

# Run evtest and process its output
evtest_process = subprocess.Popen(EVTEST_CMD, stdout=subprocess.PIPE, universal_newlines=True)
for line in evtest_process.stdout:
    parse_evtest_output(line)