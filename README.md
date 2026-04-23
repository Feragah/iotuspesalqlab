# IoT USP ESALQ — Laboratório MQTT com ESP32 + MicroPython

Laboratório prático demonstrando o padrão **publish/subscribe** com MQTT, usando três projetos ESP32 simulados no [Wokwi](https://wokwi.com) comunicando-se via broker público [EMQX](https://www.emqx.com/en/mqtt/public-mqtt5-broker).

## Arquitetura

```
┌──────────────────┐           ┌──────────────────┐
│ 01 Publisher     │           │ 02 Subscriber    │
│ ESP32 + DHT22    │           │ ESP32 + OLED     │
│ Publica leituras │           │ Exibe na tela    │
└────────┬─────────┘           └────────▲─────────┘
         │                              │
         │  JSON                        │  JSON
         │  {temperatura, umidade}      │
         ▼                              │
    ┌─────────────────────────────────────┐
    │     broker.emqx.io:1883             │
    │  Topico: uspesalq/iot/esp32/dht22   │
    └─────────────────────────────────────┘
         │
         │  JSON
         ▼
┌──────────────────┐
│ 03 Atuador       │
│ ESP32 + Rele+LED │
│ Regra: liga se   │
│ temp>=25 E       │
│ umid>=50         │
└──────────────────┘
```

Os três ESP32 rodam independentes. O publisher nao sabe da existencia dos subscribers; os subscribers nao sabem quem publicou. Todos conhecem apenas o broker e o nome do topico. Esse **desacoplamento** e a principal vantagem do MQTT.

## Conteudo do repositorio

| Pasta | Papel | Hardware simulado |
|---|---|---|
| `01-publisher-dht22/` | Publica temperatura e umidade em JSON | ESP32 + DHT22 |
| `02-subscriber-oled/` | Assina o topico e exibe os dados no display | ESP32 + SSD1306 128x64 (I2C) |
| `03-subscriber-atuador-rele/` | Assina o topico e aciona rele por regra | ESP32 + modulo rele + LED indicador |

## Pre-requisitos

- Conta gratuita no [Wokwi](https://wokwi.com).
- Navegador moderno para o [MQTTX Web](https://mqttx.app/web-client) (opcional, para observar o trafego).

## Como executar

Para cada projeto:

1. Crie um novo projeto **MicroPython ESP32** em [wokwi.com/projects/new/micropython-esp32](https://wokwi.com/projects/new/micropython-esp32).
2. Substitua o conteudo de `main.py` pelo arquivo correspondente desta pasta.
3. Substitua o conteudo de `diagram.json` pelo arquivo correspondente.
4. **Apenas no projeto 02**: adicione tambem o arquivo `ssd1306.py` na raiz do projeto Wokwi (clique no icone de novo arquivo no Wokwi).
5. Clique em **Play**.

Rode os tres projetos em **abas separadas** do navegador, simultaneamente. A partir daqui:

- Clique no DHT22 do projeto 01 para abrir os sliders de temperatura e umidade.
- Ajuste os valores e observe o display atualizar no projeto 02.
- Ultrapasse os limites de acionamento (temp >= 25, umid >= 50) e observe o rele clicar e o LED acender no projeto 03.

## Configuracoes compartilhadas

Todos os projetos usam as mesmas constantes:

| Parametro | Valor |
|---|---|
| WiFi SSID | `Wokwi-GUEST` (rede aberta simulada pelo Wokwi) |
| Broker | `broker.emqx.io` |
| Porta TCP (ESP32) | `1883` |
| Porta WebSocket TLS (MQTTX Web) | `8084`, path `/mqtt`, SSL ligado |
| Topico de dados | `uspesalq/iot/esp32/dht22` |
| Formato do payload | `{"temperatura": <float>, "umidade": <float>, "ts": <int>}` |

## Observando o trafego com MQTTX Web

Para inspecionar as mensagens em tempo real:

1. Acesse [mqttx.app/web-client](https://mqttx.app/web-client).
2. Configure uma nova conexao:
   - Host (dropdown): `wss://`
   - Host (endereco): `broker.emqx.io`
   - Port: `8084`
   - Path: `/mqtt`
   - SSL/TLS: **ligado** (obrigatorio por causa da pagina HTTPS do MQTTX Web)
3. Conecte e inscreva-se no topico wildcard `uspesalq/iot/esp32/#` para capturar tudo.

Atraves do MQTTX voce tambem pode **publicar manualmente** mensagens no topico, testando o sistema sem o publisher real. Envie um JSON como:

```json
{"temperatura": 30, "umidade": 70}
```

E observe os dois subscribers reagirem instantaneamente.

## Limitacoes da biblioteca `umqtt.simple`

Os codigos usam a biblioteca `umqtt.simple` que acompanha o firmware MicroPython do Wokwi. Ela e deliberadamente minimalista:

- Suporta apenas QoS 0 e QoS 1. **QoS 2 nao e suportado**.
- Implementa apenas MQTT 3.1.1 (sem recursos de MQTT 5 como User Properties, Response Topic, Message Expiry).
- Nao tem reconexao automatica — esta implementada manualmente nos loops principais.

Para casos de uso que demandem mais, veja `umqtt.robust` (reconexao automatica) ou `mqtt_as` (MQTT 3.1.1 completo com asyncio).

## Topicos de estudo sugeridos

Experimentos que podem ser realizados com esta base:

- **QoS 0 vs QoS 1** — observar o handshake PUBACK.
- **Retained messages** — preservar o ultimo estado para novos subscribers.
- **Last Will and Testament (LWT)** — detectar perda de conexao.
- **Clean Session** — sessoes persistentes com acumulo de mensagens.
- **Multiplos subscribers no mesmo topico** — fan-out do broker.
- **Desacoplamento** — publicar manualmente pelo MQTTX sem o sensor.

## Autor

Fernando — material didatico para curso de pos-graduacao em IoT.
