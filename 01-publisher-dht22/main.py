import network
import time
import ujson
import dht
from machine import Pin
from umqtt.simple import MQTTClient

# --- WiFi ---
SSID = "Wokwi-GUEST"
PASSWORD = ""

# --- MQTT ---
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT   = 1883
MQTT_TOPIC  = b"uspesalq/iot/esp32/dht22"
CLIENT_ID   = b"esp32-pub-fernando-001"

# --- Sensor ---
sensor = dht.DHT22(Pin(15))
INTERVALO_S = 3   # DHT22 exige >= 2s entre leituras


def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando ao WiFi", end="")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.3)
            print(".", end="")
    print("\nWiFi OK. IP:", wlan.ifconfig()[0])


def conectar_mqtt():
    c = MQTTClient(CLIENT_ID, MQTT_BROKER,
                   port=MQTT_PORT, keepalive=60)
    c.connect()
    print("Conectado ao broker MQTT")
    return c


conectar_wifi()
client = conectar_mqtt()

while True:
    try:
        sensor.measure()
        temperatura = sensor.temperature()   # graus Celsius
        umidade     = sensor.humidity()      # %

        payload = ujson.dumps({
            "temperatura": temperatura,
            "umidade": umidade,
            "ts": time.time()
        })

        client.publish(MQTT_TOPIC, payload)
        print("PUB", MQTT_TOPIC.decode(), "->", payload)
        time.sleep(INTERVALO_S)

    except OSError as e:
        print("Erro MQTT:", e, "- reconectando em 3s")
        time.sleep(3)
        client = conectar_mqtt()
    except Exception as e:
        print("Erro sensor:", e)
        time.sleep(INTERVALO_S)
