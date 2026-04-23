import network
import time
import ujson
from machine import Pin, I2C
from umqtt.simple import MQTTClient
from ssd1306 import SSD1306_I2C

# --- WiFi ---
SSID = "Wokwi-GUEST"
PASSWORD = ""

# --- MQTT ---
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT   = 1883
MQTT_TOPIC  = b"uspesalq/iot/esp32/dht22"
CLIENT_ID   = b"esp32-sub-fernando-001"

# --- OLED (I2C0: SCL=22, SDA=21) ---
LARGURA = 128
ALTURA  = 64
i2c  = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
oled = SSD1306_I2C(LARGURA, ALTURA, i2c)

# --- Estado compartilhado ---
estado = {
    "temp": None,
    "umid": None,
    "msgs": 0,
    "wifi_ip": "-",
    "status": "Iniciando"
}


def mostrar_status(titulo, *linhas):
    """Tela de status simples (usada durante boot/reconexao)."""
    oled.fill(0)
    oled.text(titulo, 0, 0)
    oled.hline(0, 10, LARGURA, 1)
    y = 18
    for linha in linhas:
        oled.text(linha, 0, y)
        y += 10
    oled.show()


def desenhar_tela():
    """Tela principal com os dados do DHT22."""
    oled.fill(0)
    # Cabecalho
    oled.text("DHT22 via MQTT", 0, 0)
    oled.hline(0, 10, LARGURA, 1)
    # Leituras
    if estado["temp"] is None:
        oled.text("Aguardando", 0, 22)
        oled.text("dados...", 0, 34)
    else:
        oled.text("Temp: {:.1f} C".format(estado["temp"]), 0, 18)
        oled.text("Umid: {:.1f} %".format(estado["umid"]), 0, 32)
    # Rodape
    oled.hline(0, 48, LARGURA, 1)
    oled.text("Msgs: {}".format(estado["msgs"]), 0, 54)
    oled.show()


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

    estado["temp"] = float(t)
    estado["umid"] = float(u)
    estado["msgs"] += 1
    print("SUB temp={:.1f}C umid={:.1f}% (#{})".format(
        estado["temp"], estado["umid"], estado["msgs"]))
    desenhar_tela()


def conectar_wifi():
    mostrar_status("WiFi", "Conectando...", SSID)
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.3)
    estado["wifi_ip"] = wlan.ifconfig()[0]
    print("WiFi OK. IP:", estado["wifi_ip"])
    mostrar_status("WiFi OK", "IP:", estado["wifi_ip"])
    time.sleep(1)


def conectar_mqtt():
    mostrar_status("MQTT", "Conectando ao", MQTT_BROKER)
    c = MQTTClient(CLIENT_ID, MQTT_BROKER, port=MQTT_PORT, keepalive=60)
    c.set_callback(callback)
    c.connect()
    c.subscribe(MQTT_TOPIC)
    print("Inscrito em", MQTT_TOPIC.decode())
    mostrar_status("MQTT OK", "Inscrito em:", MQTT_TOPIC.decode())
    time.sleep(1)
    desenhar_tela()
    return c


conectar_wifi()
client = conectar_mqtt()

while True:
    try:
        client.check_msg()
        time.sleep(0.1)
    except OSError as e:
        print("Erro MQTT:", e)
        mostrar_status("MQTT erro", str(e), "Reconectando...")
        time.sleep(3)
        try:
            client = conectar_mqtt()
        except Exception as e2:
            print("Falha ao reconectar:", e2)
            time.sleep(3)
