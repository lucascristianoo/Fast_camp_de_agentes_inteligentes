# Importamos bibliotecas necessárias
import requests  # Para requisições HTTP
import time  # Para controle de intervalos
import sys  # Para manipulação do sistema (ex.: saída com erro)
from typing import Set  # Para tipagem de conjuntos

# Verificação de dependências no início da execução
try:
    print("Verificando dependências...")
    import requests
    import time
    print("Dependências carregadas com sucesso.")
except ImportError as e:
    print(f"Erro ao importar dependências: {e}")
    sys.exit(1)  # Encerra o programa em caso de erro

# Configurações globais para APIs
# URL base da API do Langflow
API_URL = "http://127.0.0.1:7860/api/v1/run"
# ID do fluxo específico no Langflow
FLOW_ID = "c01cb267-27bd-4a4c-9785-e633a3c5fadf"

# Configurações do WAHA (WhatsApp API)
WAHA_API_URL = "http://localhost:3000/api"  # URL base da API WAHA
OWNER_CHAT_ID = "556281847834@c.us"  # ID do chat do proprietário (destinatário das respostas)
SESSION_NAME = "default"  # Nome da sessão WAHA, deve corresponder à configuração do servidor
INITIAL_CHAT_IDS = [
    "556281847834@c.us",  # Número do proprietário
    "556291249164@c.us"   # Número do remetente inicial
]

# Função para limpar e truncar mensagens, evitando textos longos ou formatados incorretamente
def clean_and_truncate(text: str, max_length: int = 1000) -> str:
    text = text.replace("*", "")  # Remove formatação Markdown (ex.: negrito)
    if len(text) > max_length:
        text = text[:max_length - 3] + "..."  # Trunca texto se exceder o limite
    return text

"""
A função ask_langflow_question envia uma mensagem para o Langflow e retorna a resposta da IA.
- Monta uma requisição POST com a mensagem no formato JSON.
- Configura o tipo de entrada/saída como "chat".
- Extrai a resposta do campo específico no JSON retornado.
- Lida com erros de rede ou formato de resposta.
"""
def ask_langflow_question(message: str, flow_id: str = FLOW_ID) -> str:
    print(f"Enviando mensagem ao Langflow: {message}")
    url = f"{API_URL}/{flow_id}"  # Monta URL com o ID do fluxo
    headers = {"Content-Type": "application/json"}  # Define tipo de conteúdo como JSON
    payload = {
        "input_type": "chat",
        "output_type": "chat",
        "tweaks": {
            "ChatInput-Jv1g7": {"input_value": message}  # Define mensagem como entrada
        }
    }
    try:
        response = requests.post(url, json=payload, headers=headers)  # Envia requisição
        response.raise_for_status()  # Levanta exceção para códigos de erro HTTP
        data = response.json()  # Converte resposta para JSON
        # Extrai texto da resposta da IA
        ai_text = data["outputs"][0]["outputs"][0]["results"]["message"]["text"]
        print(f"Resposta do Langflow recebida: {ai_text[:100]}...")  # Log parcial da resposta
        return ai_text
    except (requests.exceptions.RequestException, KeyError, IndexError) as e:
        print(f"Erro ao processar mensagem no Langflow: {e}")
        return "Erro ao processar a mensagem."  # Retorna mensagem padrão em caso de erro

# Função para enviar mensagens via WAHA
def send_waha_message(chat_id: str, text: str):
    text = clean_and_truncate(text)  # Limpa e trunca mensagem antes de enviar
    print(f"Enviando mensagem para {chat_id}: {text[:100]}...")
    url = f"{WAHA_API_URL}/sendText"  # Endpoint para envio de mensagens
    payload = {
        "session": SESSION_NAME,  # Nome da sessão WAHA
        "chatId": chat_id,  # ID do destinatário
        "text": text  # Conteúdo da mensagem
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Verifica erros HTTP
        print("Mensagem enviada com sucesso.")
        return response.json()  # Retorna resposta da API
    except requests.exceptions.HTTPError as e:
        print(f"Erro ao enviar mensagem para {chat_id}: {e}")
        try:
            error_details = response.json()  # Tenta extrair detalhes do erro
            print(f"Detalhes do erro: {error_details}")
        except:
            pass
        return None  # Retorna None em caso de falha

# Função para obter novas mensagens de um chat específico via WAHA
def get_new_messages(chat_id: str, processed_ids: Set[str], monitored_chats: Set[str]) -> list:
    print(f"Verificando mensagens para chatId: {chat_id}")
    url = f"{WAHA_API_URL}/messages?chatId={chat_id}"  # Endpoint para obter mensagens
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=10)  # Requisição com timeout
        response.raise_for_status()
        messages = response.json()  # Converte resposta para JSON
        print(f"Mensagens recebidas para {chat_id}: {len(messages)}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter mensagens para {chat_id}: {e}")
        return []  # Retorna lista vazia em caso de erro

    new_messages = []
    for msg in messages:
        message_id = msg.get("id")  # ID único da mensagem
        sender = msg.get("from")  # Remetente
        msg_type = msg.get("type")  # Tipo de mensagem (ex.: texto)
        from_me = msg.get("fromMe", False)  # Verifica se é mensagem enviada pelo bot
        body = msg.get("body", "")  # Conteúdo da mensagem
        to = msg.get("to", "")  # Destinatário
        print(f"Processando mensagem {message_id}: type={msg_type}, fromMe={from_me}, from={sender}, to={to}, body={body}")
        # Filtra mensagens novas, não enviadas pelo bot e com conteúdo
        if (message_id not in processed_ids and 
            not from_me and 
            body):
            new_messages.append(msg)
            processed_ids.add(message_id)  # Marca mensagem como processada
            print(f"Mensagem válida encontrada: {body}")
            # Adiciona remetente à lista de chats monitorados, se novo
            if sender and sender != chat_id and sender not in monitored_chats:
                monitored_chats.add(sender)
                print(f"Novo remetente adicionado para monitoramento: {sender}")

    return new_messages  # Retorna lista de mensagens novas

# Loop principal para monitoramento contínuo de mensagens
def main():
    print("Iniciando o script...")
    processed_ids: Set[str] = set()  # Conjunto para IDs de mensagens processadas
    monitored_chats: Set[str] = set(INITIAL_CHAT_IDS)  # Conjunto de chats monitorados
    polling_interval = 5  # Intervalo entre verificações (segundos)
    max_retries = 3  # Número máximo de tentativas em caso de erro

    print("Iniciando polling de mensagens do WAHA...")
    print(f"Chats monitorados inicialmente: {monitored_chats}")
    while True:
        try:
            print(f"Iniciando ciclo de polling. Chats monitorados: {monitored_chats}")
            for chat_id in list(monitored_chats):  # Itera sobre chats monitorados
                retries = 0
                while retries < max_retries:
                    try:
                        # Obtém novas mensagens do chat
                        new_messages = get_new_messages(chat_id, processed_ids, monitored_chats)
                        for msg in new_messages:
                            message_text = msg.get("body")  # Texto da mensagem
                            sender = msg.get("from")  # Remetente
                            print(f"Mensagem recebida de {sender}: {message_text}")

                            # Envia mensagem ao Langflow para processamento
                            ai_response = ask_langflow_question(message_text)
                            print(f"Resposta do Langflow: {ai_response[:100]}...")

                            # Monta e envia resposta apenas para o proprietário
                            response_text = f"De {sender}: {message_text}\nResposta: {ai_response}"
                            send_waha_message(OWNER_CHAT_ID, response_text)
                            print(f"Resposta enviada para {OWNER_CHAT_ID}")
                        break  # Sai do loop de tentativas após sucesso
                    except requests.exceptions.ConnectionError as e:
                        retries += 1
                        print(f"Erro de conexão ao verificar {chat_id}: {e}. Tentativa {retries}/{max_retries}")
                        if retries < max_retries:
                            time.sleep(5)  # Aguarda antes de nova tentativa
                        else:
                            print(f"Falha após {max_retries} tentativas para {chat_id}.")
                            break

        except Exception as e:
            print(f"Erro ao processar mensagens: {e}")

        print(f"Aguardando {polling_interval} segundos para o próximo ciclo...")
        time.sleep(polling_interval)  # Pausa antes do próximo ciclo

# Ponto de entrada do script
if __name__ == "__main__":
    try:
        print("Executando main()...")
        main()  # Inicia o loop principal
    except Exception as e:
        print(f"Erro crítico no script: {e}")
        sys.exit(1)  # Encerra com erro em caso de falha crítica