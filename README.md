# Skales IoT Notification Robot 🤖

Bem-vindo ao Skales IoT Notification Robot! Este é um projeto Python incrível que lida com notificações provenientes de dispositivos IoT e as integra ao Slack para uma experiência de monitoramento inigualável. 🚀

## Funcionalidades Principais
- **Integração com Banco de Dados:** Estabelece conexão com o banco de dados MySQL para obter dados essenciais.
- **Processamento MQTT:** Recebe mensagens MQTT de dispositivos IoT, interpreta os payloads e gera notificações significativas.
- **Integração Slack:** Notificações enviadas de forma elegante para canais do Slack, mantendo a equipe sempre informada.
- **Atualização Automática de Tabelas:** Mantém tabelas de referência atualizadas, garantindo precisão nos dados exibidos.

## Pré-requisitos
Certifique-se de ter instalado:
- Python 3.6+
- Bibliotecas Python: mysql-connector, slack_sdk, paho-mqtt

## Configuração Inicial
1. Clone o repositório: `git clone https://github.com/sevenscience/skales-iot-robot.git`
2. Instale as dependências: `pip install -r requirements.txt`
3. Configure suas credenciais do MySQL e Slack no arquivo `config.py`.
4. Execute o script principal: `python main.py`

## Estrutura do Projeto
|-- skales-iot-robot/
|-- logs.txt
|-- main.py
|-- config.py
|-- requirements.txt
|-- README.md
|-- src/
|-- skales_robot/
|-- init.py
|-- mqtt_handler.py
|-- slack_handler.py
|-- database_handler.py


## Como Contribuir
Adoraríamos receber sua contribuição para tornar este robô ainda mais incrível! Sinta-se à vontade para:
- Reportar problemas
- Enviar solicitações de melhoria
- Adicionar novos recursos

Lembre-se, a inovação é a chave! 🚀

## Licença
Este projeto é licenciado sob a [Licença MIT](LICENSE).

Dê uma estrela se este robô deixou seu dia mais feliz! ⭐️
