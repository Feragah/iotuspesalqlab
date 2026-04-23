import network
import time
import ujson
from machine import Pin
from umqtt.simple import MQTTClient

# --- WiFi ---
SSID = "Wokwi-GUEST"
PASSWORD = ""

# --- MQTT ---
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT   = 1883
MQTT_TOPIC  = b"uspesalq/iot/esp32/dht22"
CLIENT_ID   = b"esp32-atuador-fernando-001"

# --- Hardware ---
RELE_PIN = 26
rele = Pin(RELE_PIN, Pin.OUT)
rele.value(0)                 # garante desligado no boot

# --- Regra de acionamento ---
TEMP_LIMITE = 25.0            # graus Celsius
UMID_LIMITE = 50.0            # percentual
HISTERESE_TEMP = 1.0          # margem para evitar chaveamento em oscilacao
HISTERESE_UMID = 2.0

# --- Estado ---
rele_ligado = False


def avaliar_regra(temp, umid):
    """
    Decide se o rele deve estar ligado ou desligado.
    Liga:    temp >= 25 E umid >= 50
    Desliga: temp <  24 E umid <  48 (com histerese)
    """
    global rele_ligado

    if not rele_ligado:
        if temp >= TEMP_LIMITE and umid >= UMID_LIMITE:
            rele.value(1)
            rele_ligado = True
            print(">>> RELE LIGADO (ventilador ON)")
    else:
        if (temp < TEMP_LIMITE - HISTERESE_TEMP
                and umid < UMID_LIMITE - HISTERESE_UMID):
            rele.value(0)
            rele_ligado = False
            print(">>> RELE DESLIGADO (ventilador OFF)")


def callback(topic, msg):
    try:
        dados = ujson.loads(msg)
    except ValueError:
        print("Payload nao e JSON:", msg)
        return

    t = dados.get("temperatura")
    u = dados.get("umidade")
    if t is None or u is None:
        print("JSON sem campos esperados:", dados)
        return

    temp = float(t)
    umid = float(u)

    estado = "LIGADO" if rele_ligado else "DESLIGADO"
    print("SUB temp={:.1f}C umid={:.1f}% | rele={}".format(
        temp, umid, estado))

    avaliar_regra(temp, umid)


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
    c = MQTTClient(CLIENT_ID, MQTT_BROKER, port=MQTT_PORT, keepalive=60)
    c.set_callback(callback)
    c.connect()
    c.subscribe(MQTT_TOPIC)
    print("Inscrito em", MQTT_TOPIC.decode())
    print("Regra: LIGA se temp>={}C E umid>={}%".format(
        TEMP_LIMITE, UMID_LIMITE))
    print("       DESLIGA se temp<{}C E umid<{}%".format(
        TEMP_LIMITE - HISTERESE_TEMP, UMID_LIMITE - HISTERESE_UMID))
    return c


conectar_wifi()
client = conectar_mqtt()

while True:
    try:
        client.check_msg()
        time.sleep(0.1)
    except OSError as e:
        print("Erro MQTT:", e)
        # fail-safe: desliga o rele ao perder conexao
        rele.value(0)
        rele_ligado = False
        print(">>> RELE DESLIGADO por falha de conexao (fail-safe)")
        time.sleep(3)
        try:
            client = conectar_mqtt()
        except Exception as e2:
            print("Falha ao reconectar:", e2)
            time.sleep(3)
