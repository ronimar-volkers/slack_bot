import mysql.connector
from slack_sdk import WebClient
import time
import json
import paho.mqtt.client as mqtt
import base64
import logging
import threading

# Configuração do logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='logs.txt', filemode='a')
# logging.getLogger().addHandler(logging.StreamHandler())

slack_token = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
slack_icon_emoji = ':male_mage:'
slack_user_name = 'XXXXXXX'

Conces = 'admin'
global dev_addr
global tabela_dict
global tabela_dict2
tabela_dict = {}
tabela_dict2 = {}
db_connection = None
registros = {}
device = None
status_chave = None
global message_dict
global tx_count
tx_count = 0
global NumOP

ip = "10.0.0.6"


while True:
    logging.debug("Verificando a conexão ao banco...")
    try:
        db_connection = mysql.connector.connect(
            host=ip,
            user="XXXXXXXXX",
            password="XXXXXXXXXX",
            database="XXXXX"
        )
        print("Conectado ao banco com sucesso!")
        logging.info("Conectado ao banco com sucesso!")
        break  # Se a conexão for estabelecida com sucesso, saia do loop

    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {str(e)}")
        print("Tentando reconectar em 1 minuto...")
        logging.warning("Conectado ao banco quase sem sucesso!")
        time.sleep(60)  # Espera 1 minuto antes de tentar novamentef

# Função para obter o status da chave
def obter_status_chave(valor):
    logging.debug('Verificando o status da chave...')
    valor = valor & 0x01
    global message_dict
    if valor == 1:
        message_dict['attachments'][0]['color'] = "#F44336" 
        return "FECHADA  \U0001f534"
    elif valor == 0:
        return "ABERTA      \U0001f7e2"
    else:
        return "Desconhecida \U0001f7e1"
    
def obter_status_chave_c2(valor):
    logging.debug('Verificando o status da chave...')
    global message_dict
    if valor <= -20:
        message_dict['attachments'][0]['color'] = "#F44336" 
        return "FECHADA  \U0001f534"
    else:
        return "ABERTA      \U0001f7e2"
    
def unsigned_to_signed(unsigned_value):
    if unsigned_value <= 127:
        return unsigned_value
    else:
        return unsigned_value - 256

# Função para obter o nÃ­vel da bateria
def obter_nivel_bateria(valor):
    logging.debug('Verificando o nÃ­vel o bateria...')
    if valor >= 15:
        return "            \U0001f50b"
    elif valor < 15:
        return "            \U0001faab"
    else:
        return "Desconhecida \U0001f7e1"

# Função para alinhar o emoji do RSSI
def alinhar_emoji_RSSI(valor):
    logging.debug('Centralizando o emoji do RSSI...')
    if valor <= (-100):
        return "           \U0001f4e1"
    elif valor > (-100):
        return "             \U0001f4e1"
    else:
        return "Desconhecida \U0001f7e1"

# Callback chamada quando a conexão ao broker MQTT Ã© estabelecida
def on_connect(client, userdata, flags, rc):
    while True:
        try:
            logging.debug('Verificando a conexão ao broker MQTT...')
            if rc == 0:
                print("Conexão ao broker MQTT estabelecida com sucesso!")
                # Inscreva-se no tÃ³pico desejado apÃ³s a conexão bem-sucedida
                client.subscribe("Everynet/uplink/XXXXXXXCloud/#")
                client.subscribe("GIOT-GW/UL/#")
                client.subscribe("Slack/KeepAlive/#")
                logging.info('Conectado ao broker MQTT com sucesso!')
                break  # Sai do loop se a conexão for bem-sucedida
            else:
                print(f"Falha na conexão. CÃ³digo de retorno: {rc}")
        except Exception as e:
            logging.exception(e)
            print("Erro ao conectar ao broker MQTT. Tentando novamente em 5 segundos...")
            time.sleep(5)  # Aguarda 5 segundos antes de tentar novamente

# def extrairValores(buffer, dados):
#     dados.equipamento = buffer[0] >> 4
#     dados.devcode = buffer[0] & 0x0F
#     dados.estado = (buffer[1] >> 7) & 0x01
#     dados.bateria = buffer[1] & 0x7F
#     dados.downlink_request = (buffer[2] >> 7) & 0x01
#     dados.temperatura = buffer[2] & 0x7F
#     dados.key_a = buffer[3] >> 4 & 0x0F
#     dados.key_b = buffer[3] & 0x0F
#     dados.rssi = buffer[4]
#     dados.acc_x = buffer[5]
#     dados.tx_count = (buffer[6] << 8) | buffer[7]
#     dados.fw_version = buffer[8]
#     dados.uplink_period = buffer[9] >> 3
#     dados.rst_cause = buffer[9] & 0x07

def adicionar_registro(device, status_chave, tx_count):
    logging.debug('Adicionando os registros...')
    global registros
    global timestamp
    timestamp = int(time.time())
    registros[device] = [status_chave, timestamp, tx_count]

# Callback chamada quando uma mensagem Ã© recebida em um tÃ³pico inscrito
def on_message(client, userdata, msg):
    try:
        global Conces
        global channel
        payload = msg.payload.decode()
        global message_dict
        global device
        global status_chave
        global registros
        global tx_count
        global dev_addr
        global tabela_dict
        global tabela_dict2
        global NumOP

        message_dict = {
            "attachments": [
                {
                    "mrkdwn_in": ["text"],
                    "fallback": "Alguma coisa legal aqui",
                    "color": "#e8ee00",
                    "title": "**",
                    "fields": [
                        {
                            "value": "Chave = \\nBateria = \\nTemp = \\nRSSI = \\n",
                            "short": False
                        }
                    ],
                    "footer": "XXXXXXX Science System",
                    "footer_icon": "https://dashboard.7science.com.br/img/XXXXXXX.ico",
                    "ts": "null"
                } 
            ]
        }

        try:
            logging.debug('Iniciando o processamento da mensagem MQTT...')
            data = json.loads(payload)
            if ("Everynet/uplink/XXXXXXXCloud" in msg.topic) and (data.get("type") == "uplink" and "params" in data):
                logging.debug('Mensagem do tÃ³pico "Everynet/uplink/XXXXXXXCloud" recebida.')
                params = data["params"]
                if "payload" in params:
                    encoded_payload = params["payload"]
                    decoded_payload = base64.b64decode(encoded_payload)
                    decoded_payload = list(decoded_payload)
                    if len(decoded_payload) > 4:
                        if decoded_payload[0] == 0xcf:
                            logging.debug('Mensagem de payload 0xcf Everynet identificada.')

                            # ObtÃ©m o nome do dispositivo
                            device = data["meta"]["device"]
                            device = str(device).upper()
                            dev_addr = device
                            # ObtÃ©m o status da chave
                            status_chave = obter_status_chave(decoded_payload[1])

                            # ObtÃ©m o nÃ­vel da bateria
                            nivel_bateria = obter_nivel_bateria(decoded_payload[3])

                            # ObtÃ©m o RSSI do gateway
                            rssi = data["params"]["radio"]["hardware"]["rssi"]
                            emoji_RSSI = alinhar_emoji_RSSI(int(rssi))
                            
                            

                            if tabela_dict2[dev_addr] == '' or tabela_dict2[dev_addr] == None:
                                message_dict['attachments'][0]['title'] = f"{device.upper()}"
                                message_dict['attachments'][0]['fallback'] = f"*{device.upper()}*"
                            else:     
                                message_dict['attachments'][0]['title'] = f"{str(tabela_dict2[dev_addr]).upper()}"       
                                message_dict['attachments'][0]['text'] = f"_{device.upper()}_"
                                message_dict['attachments'][0]['fallback'] = f"{str(tabela_dict2[dev_addr]).upper()}"
                                

                            message_dict['attachments'][0]['fields'][0]['value'] = f"Chave   = {status_chave}\nBateria  = {decoded_payload[3]}%{nivel_bateria}\nTemp     = {decoded_payload[4]}°C           \U0001f321\uFE0F\nRSSI       = {int(rssi)}{emoji_RSSI}\n"

                            message_dict['attachments'][0]['ts'] = str(int(time.time()))

                            # ObtÃ©m o RSSI do dispositivo
                            # mensagem += f"DevRSSI  = {decoded_payload[5]}\n"

                            # Salva o Dispositivo atual atual
                            DevAddr = tabela_dict.get(device)  # Procura o DevAddr atual no dicionÃ¡rio

                            if DevAddr is not None:
                                # Armazena o nome do cliente correspondente
                                Conces = DevAddr
                            else:
                                Conces = 'admin'

                        if decoded_payload[0] == 0xc2:
                            logging.debug('Mensagem de payload 0xc2 Everynet identificada.')
                            device = data["meta"]["device"]
                            device = str(device).upper()
                            dev_addr = device
                            # ObtÃ©m o status da chave
                            signed_value = unsigned_to_signed(decoded_payload[5])

                            status_chave = obter_status_chave_c2(signed_value)
                            
                            print(f"Valor: {signed_value}")

                            # ObtÃ©m o nÃ­vel da bateria
                            nivel_bateria = obter_nivel_bateria((decoded_payload[1] & 0x7F))

                            # ObtÃ©m o valor do contador
                            tx_count = decoded_payload[6]<<8 | decoded_payload[7]

                            # ObtÃ©m o RSSI do gateway
                            rssi = data["params"]["radio"]["hardware"]["rssi"]
                            emoji_RSSI = alinhar_emoji_RSSI(int(rssi))
                            
                            message_dict['attachments'][0]['fallback'] = f"*{device.upper()}*"

                            if tabela_dict2[dev_addr] == '' or tabela_dict2[dev_addr] == None:
                                message_dict['attachments'][0]['title'] = f"{device.upper()}"
                                message_dict['attachments'][0]['fallback'] = f"*{device.upper()}*"
                            else:     
                                message_dict['attachments'][0]['title'] = f"{str(tabela_dict2[dev_addr]).upper()}"       
                                message_dict['attachments'][0]['text'] = f"_{device.upper()}_"
                                message_dict['attachments'][0]['fallback'] = f"{str(tabela_dict2[dev_addr]).upper()}"

                            message_dict['attachments'][0]['fields'][0]['value'] = f"Chave   = {status_chave}\nBateria  = {decoded_payload[1] & 0x7F}%{nivel_bateria}\nTemp     = {decoded_payload[2] & 0x7F}°C           \U0001f321\uFE0F\nRSSI       = {int(rssi)}{emoji_RSSI}\n"

                            message_dict['attachments'][0]['ts'] = str(int(time.time()))

                            # ObtÃ©m o RSSI do dispositivo
                            # mensagem += f"DevRSSI  = {decoded_payload[5]}\n"

                            # Salva o Dispositivo atual atual
                            DevAddr = tabela_dict.get(device)  # Procura o DevAddr atual no dicionÃ¡rio

                            if DevAddr is not None:
                                # Armazena o nome do cliente correspondente
                                Conces = DevAddr
                            else:
                                Conces = 'admin'

            elif "GIOT-GW/UL/" in msg.topic:
                logging.debug('Mensagem do tÃ³pico "GIOT-GW/UL/" recebida.')
                encoded_payload = data[0]["data"]
                decoded_payload = bytearray.fromhex(encoded_payload)
                decoded_payload = list(decoded_payload)
                if len(decoded_payload) > 4:
                    if decoded_payload[0] == 0xcf:
                        logging.debug('Mensagem de payload 0xcf GIOT-GW identificada.')

                        # ObtÃ©m o nome do dispositivo
                        device = data[0]["devEUI"]
                        device = str(device).upper()
                        dev_addr = device

                        # ObtÃ©m o status da chave
                        status_chave = obter_status_chave(decoded_payload[1])

                        # ObtÃ©m o nÃ­vel da bateria
                        nivel_bateria = obter_nivel_bateria(decoded_payload[3])

                        # ObtÃ©m o RSSI do gateway
                        rssi = data[0]["rssi"]
                        emoji_RSSI = alinhar_emoji_RSSI(int(rssi))

                        message_dict['attachments'][0]['fallback'] = f"*{device.upper()}*"

                        if tabela_dict2[dev_addr] == '' or tabela_dict2[dev_addr] == None:
                            message_dict['attachments'][0]['title'] = f"{device.upper()}"
                            message_dict['attachments'][0]['fallback'] = f"*{device.upper()}*"
                        else:     
                            message_dict['attachments'][0]['title'] = f"{str(tabela_dict2[dev_addr]).upper()}"       
                            message_dict['attachments'][0]['text'] = f"_{device.upper()}_"
                            message_dict['attachments'][0]['fallback'] = f"{str(tabela_dict2[dev_addr]).upper()}"

                        message_dict['attachments'][0]['fields'][0]['value'] = f"Chave   = {status_chave}\nBateria  = {decoded_payload[3]}%{nivel_bateria}\nTemp     = {decoded_payload[4]}°C           \U0001f321\uFE0F\nRSSI       = {int(rssi)}{emoji_RSSI}\n"

                        message_dict['attachments'][0]['ts'] = str(int(time.time()))

                        # Salva o Dispositivo atual atual
                        DevAddr = tabela_dict.get(device)  # Procura o DevAddr atual no dicionÃ¡rio

                        if DevAddr is not None:
                            # Armazena o nome do cliente correspondente
                            Conces = DevAddr
                        else:
                            Conces = 'admin'
                
                    if decoded_payload[0] == 0xc2:
                        logging.debug('Mensagem de payload 0xc2 GIOT-GW identificada.')

                        device = data[0]["devEUI"]
                        device = str(device).upper()
                        dev_addr = device

                        # ObtÃ©m o status da chave
                        signed_value = unsigned_to_signed(decoded_payload[5])

                        status_chave = obter_status_chave_c2(signed_value)

                        # ObtÃ©m o nÃ­vel da bateria
                        nivel_bateria = obter_nivel_bateria((decoded_payload[1] & 0x7F))
                        
                        # ObtÃ©m o valor do contador
                        tx_count = decoded_payload[6]<<8 | decoded_payload[7]

                        # ObtÃ©m o RSSI do gateway
                        rssi = data[0]["rssi"]
                        emoji_RSSI = alinhar_emoji_RSSI(int(rssi))
                        
                        message_dict['attachments'][0]['fallback'] = f"*{device.upper()}*"

                        if tabela_dict2[dev_addr] == '' or tabela_dict2[dev_addr] == None:
                            message_dict['attachments'][0]['title'] = f"{device.upper()}"
                            message_dict['attachments'][0]['fallback'] = f"*{device.upper()}*"
                        else:     
                            message_dict['attachments'][0]['title'] = f"{str(tabela_dict2[dev_addr]).upper()}"       
                            message_dict['attachments'][0]['text'] = f"_{device.upper()}_"
                            message_dict['attachments'][0]['fallback'] = f"{str(tabela_dict2[dev_addr]).upper()}"

                        message_dict['attachments'][0]['fields'][0]['value'] = f"Chave   = {status_chave}\nBateria  = {decoded_payload[1] & 0x7F}%{nivel_bateria}\nTemp     = {decoded_payload[2] & 0x7F}°C           \U0001f321\uFE0F\nRSSI       = {int(rssi)}{emoji_RSSI}\n"

                        message_dict['attachments'][0]['ts'] = str(int(time.time()))

                        # ObtÃ©m o RSSI do dispositivo
                        # mensagem += f"DevRSSI  = {decoded_payload[5]}\n"

                        # Salva o Dispositivo atual
                        DevAddr = tabela_dict.get(device)  # Procura o DevAddr atual no dicionÃ¡rio

                        if DevAddr is not None:
                            # Armazena o nome do cliente correspondente
                            Conces = DevAddr
                        else:
                            Conces = 'admin'
                            

            elif ("Slack/KeepAlive" in msg.topic):
                Conces = 'admin'
                message_dict['attachments'][0]['title'] = "KEEP WALKING :walking:"
                message_dict['attachments'][0]['fields'][0]['value'] = "TO BEM TIU!"
                message_dict['attachments'][0]['ts'] = str(int(time.time()))
                updated_message = json.dumps(message_dict)
                clientes = WebClient(token=slack_token)
                response = clientes.chat_postMessage(
                    channel= 'admin',
                    text='',
                    blocks=[],
                    attachments=[json.loads(updated_message)['attachments'][0]],
                )
                Conces = 'admin'
                            
        except json.JSONDecodeError:
            logging.error(f"Erro ao decodificar JSON: {payload}")
            print(f"Erro ao decodificar JSON: {payload}")

        updated_message = json.dumps(message_dict)

        clientes = WebClient(token=slack_token)

        logging.debug(f"Dispositivo: {device}")

        if device in registros:
            logging.debug('Dispositivo encontrado nos registros.')

            if registros[device][0] != status_chave and (tx_count > registros[device][2] or registros[device][2] == 0): #or (int(time.time()) - registros[device][1] >= 600):
                
                if message_dict['attachments'][0]['ts'] != "null":
                    try:
                        response = clientes.chat_postMessage(
                            channel= Conces.lower(),
                            text='',
                            blocks=[],
                            attachments=[json.loads(updated_message)['attachments'][0]],
                        )
                        Conces = 'admin'
                        logging.info("Mensagem enviada ao Slack com sucesso")
                        print("Mensagem enviada ao Slack com sucesso")
                        # status_chave, timestamp = registros.pop(device)
                        # registros[device] = [status_chave, timestamp]
                        
                    except:
                        response = clientes.chat_postMessage(
                            channel= 'admin',
                            text='*Mensagem Rejeitada*',
                            blocks=[],
                            attachments=[json.loads(updated_message)['attachments'][0]],
                        )
                        Conces = 'admin'
                        logging.info(f"Mensagem enviada ao Slack com sucesso com excessão")
                        print(f"Mensagem enviada ao Slack com sucesso com excessão")

                adicionar_registro(device, status_chave, tx_count)

        elif device is not None:
            logging.debug('Dispositivo não encontrado nos registros.')

            if message_dict['attachments'][0]['ts'] != "null":
                    try:
                        response = clientes.chat_postMessage(
                            channel= Conces.lower(),
                            text='',
                            blocks=[],
                            attachments=[json.loads(updated_message)['attachments'][0]],
                        )
                        Conces = 'admin'
                        logging.info("Mensagem enviada ao Slack com sucesso")
                        print("Mensagem enviada ao Slack com sucesso")
                    except:
                        response = clientes.chat_postMessage(
                            channel = 'admin',
                            text='*Mensagem Rejeitada*',
                            blocks=[],
                            attachments=[json.loads(updated_message)['attachments'][0]],
                        )
                        Conces = 'admin'
                        logging.info(f"Mensagem enviada ao Slack com sucesso com excessão")
                        print(f"Mensagem enviada ao Slack com sucesso com excessão")
        
            adicionar_registro(device, status_chave, tx_count)
        
        tx_count = 0
        logging.debug(f'Registros atualizados: {registros}')
        print (f'{registros}')
    except:
        logging.debug('ERRO NO SLACK')

    return Conces

def atualizar_tabela_dict():
    global dev_addr
    global tabela_dict
    global tabela_dict2

    tabela_dict2 = {}

    while True:
        try:
            db_connection = mysql.connector.connect(
            host=ip,
            user="XXXXXXX",
            password="XXXXXXXXX",
            database="XXXXXXXXXXXXX"
            )
            logging.debug("Conectado ao banco de dados com sucesso!")
            # Consulta para recuperar a tabela SensorInput
            select_query = "SELECT DevAddr, Cliente, Contador, NumOP FROM SensorInput"

            # Executa a consulta
            cursor = db_connection.cursor()
            cursor.execute(select_query)

            # Recupera todas as linhas da consulta
            results = cursor.fetchall()

            tabela_dict = {}
            logging.info("Tabela atualizada com sucesso!")
            print("Tabela atualizada com sucesso!")
            

            # Preenche o dicionÃ¡rio com os dados da tabela
            for row in results:
                dev_addr = row[0]  # Coluna DevAddr
                cliente = row[1]  # Coluna Cliente
                contador = row[2] # Coluna Contador
                NumOP = row[3] # Coluna NumOP
                tabela_dict[dev_addr] = cliente
                tabela_dict2[dev_addr] = NumOP

            # Encerra o cursor
            cursor.close()
            db_connection.close()
        
            time.sleep(300) # Atualizar 5 minuto antes de

        except Exception as e:
        # Mensagem de erro
            slack_info = f"Encontramos problemas ao atualizar os dados :pleading_face: Erro: {str(e)}"
            logging.error(f"Encontramos problemas ao atualizar os dados :pleading_face: Erro: {str(e)}")
            try:
                # Tentativa de fechar a consulta ao banco de dados
                if cursor:
                    cursor.close()
                if db_connection and db_connection.is_connected():
                    db_connection.close()
                slack_info += " Consulta ao banco de dados fechada com sucesso."
                logging.info("Banco de dados fechado com sucesso apÃ³s erro!")

            except Exception as db_error:
                slack_info += f" Erro ao fechar a consulta ao banco de dados: {str(db_error)}"
                logging.error("Erro ao fechar a consulta ao banco de dados: {str(db_error)}")

            time.sleep(60)  # Pausa de 1 minuto antes de tentar novamente

def enviar_mensagem_mqtt():
    while True:
        try:
            # Inicialização do cliente MQTT
            client = mqtt.Client()
            client.username_pw_set("XXXXX", "XXXXXXX")

            # Conexão ao broker MQTT
            client.connect("XXXXXXXXXXX", 1883, 60)

            # Loop para manter a conexão ativa
            client.loop_start()

            # Montagem da mensagem em formato JSON
            tovivo = {
                "attachments": [
                    {
                        "mrkdwn_in": ["text"],
                        "fallback": "XXXXX",
                        "color": "#e8ee00",
                        "text": ":checkered_flag: :walking:",
                        "fields": [
                            {
                                "value": "keepalive",
                                "short": False
                            }
                        ],
                        "footer": "Empresa",
                        "footer_icon": "XXXXXXXXX",
                        "ts": "null"
                    } 
                ]
            }

            up_vivo = json.dumps(tovivo)

            topic_every = "Slack/KeepAlive"
            client.publish(topic_every, up_vivo)

            # Aguarda um curto perÃ­odo para permitir que a mensagem seja enviada
            time.sleep(5)

            # Parada do loop e desconexão do broker MQTT
            client.loop_stop()
            client.disconnect()

            time.sleep(14395)  # Espera 4h antes de executar a consulta novamente
        except Exception as e:
            print(f"Encontramos problemas ao enviar a mensagem MQTT. Erro: {str(e)}")

# Configuração do cliente MQTT
client = mqtt.Client()

# Definição dos callbacks
client.on_connect = on_connect
client.on_message = on_message

# Configuração de autenticação
client.username_pw_set("XXXXXXX", "XXXXXXX.123")

# Conecte-se ao broker MQTT
client.connect("XXXXXXXiot.online", 1883, 60)

# Inicie o loop para manter a conexão e processar as mensagens recebidas
client.loop_start()

# Inicia as threads para atualizar tabela_dict e enviar a mensagem MQTT em segundo plano
thread_tabela = threading.Thread(target=atualizar_tabela_dict)
thread_mqtt = threading.Thread(target=enviar_mensagem_mqtt)

# Define as threads como daemon para que elas sejam encerradas automaticamente ao final do programa
# thread_tabela.daemon = True
# thread_mqtt.daemon = True

# Inicia as threads
thread_tabela.start()
thread_mqtt.start()

# Aguarda o encerramento das threads
while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        print("Encerrando o programa...")
        break

# Parar o loop e desconectar do broker MQTT
client.loop_stop()
client.disconnect()
logging.info("Loop MQTT parado e desconexão do broker MQTT realizada")
