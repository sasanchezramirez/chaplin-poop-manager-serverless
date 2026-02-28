import json
import os
import boto3
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime')

# Environment variables
table_name = os.environ.get('TABLE_NAME', 'ChaplinEvents')
table = dynamodb.Table(table_name)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def get_recent_history(days=7):
    """Fetch the last N days of litter box events from DynamoDB."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cutoff_timestamp = int(cutoff_date.timestamp())
        
        # We query by pet_id "chaplin" and timestamp >= cutoff
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('pet_id').eq('chaplin') & 
                                   boto3.dynamodb.conditions.Key('timestamp').gte(cutoff_timestamp)
        )
        items = response.get('Items', [])
        
        # Sort items chronologically
        items.sort(key=lambda x: x.get('timestamp', 0))
        
        # Format for the LLM to save tokens
        formatted_history = []
        for i in items:
            dt = datetime.fromtimestamp(int(i['timestamp']))
            # Add UTC-5 adjustment for local time context if needed, but UTC is fine.
            # Let's adjust to UTC-5 (Bogota/Lima/NY EST) purely for context (I'm in Colombia :D)
            dt_local = dt - timedelta(hours=5)
            formatted_history.append({
                "fecha_hora": dt_local.strftime("%Y-%m-%d %H:%M:%S"),
                "tipo": i.get('estimated_type', 'unknown'),
                "duracion_segundos": int(i.get('duration_seconds', 0))
            })
            
        return formatted_history
    except Exception as e:
        print(f"Error reading DynamoDB: {e}")
        return []

def ask_bedrock_claude(prompt_text):
    """Send the constructed prompt to Amazon Bedrock Claude 3 Haiku."""
    try:
        model_id = "anthropic.claude-3-haiku-20240307-v1:0"
        
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "temperature": 0.3,
            "messages": [
                {
                    "role": "user",
                    "content": prompt_text
                }
            ]
        }
        
        response = bedrock.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload)
        )
        
        response_body = json.loads(response.get('body').read())
        content = response_body.get('content', [])
        if content:
            return content[0].get('text', 'No generó respuesta.')
        return "Lo siento, el modelo no devolvió una respuesta válida."
        
    except Exception as e:
        print(f"Error calling Bedrock: {e}")
        return f"Error procesando con IA: {str(e)}"

def send_telegram_message(chat_id, text):
    """Send a text message back to the Telegram user."""
    if not TELEGRAM_BOT_TOKEN:
        print("Missing TELEGRAM_BOT_TOKEN")
        return
        
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=data, method='POST')
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"Error sending to Telegram: {e}")

def lambda_handler(event, context):
    try:
        body = event.get('body')
        if not body:
            return {"statusCode": 200, "body": "OK"}
            
        try:
            update = json.loads(body) if isinstance(body, str) else body
        except Exception:
            return {"statusCode": 200, "body": "Invalid JSON"}
            
        message = update.get('message', {})
        text = message.get('text', '')
        chat_id = message.get('chat', {}).get('id')
        
        # Security: Only answer to the authorized owner
        if str(chat_id) != str(TELEGRAM_CHAT_ID):
            print(f"Unauthorized chat_id: {chat_id}")
            return {"statusCode": 200, "body": "Unauthorized Chat ID"}
            
        if not text:
            return {"statusCode": 200, "body": "No text"}
            
        # 1. Fetch History
        history = get_recent_history(days=7)
        history_json = json.dumps(history, indent=2, ensure_ascii=False)
        
        # 2. Construct Prompt for Claude
        system_context = (
            "Eres el asistente inteligente de Santiago, experto en gatos, específicamente analizando la salud y "
            "comportamiento del gato 'Chaplin' basándote en los registros de su arenero inteligente.\n\n"
            "Aquí están los registros de la última semana (hora local):\n"
            f"{history_json}\n\n"
            "Reglas:\n"
            "1. Responde preguntas basándote ESTRICTAMENTE en estos datos.\n"
            "2. Si la respuesta requiere matemáticas (ej. promedios de tiempo, digestión), haz el cálculo paso a paso y da el resultado final aproximado.\n"
            "3. Sé conciso pero amigable. Usa emojis relevantes.\n"
            "4. Asume que 'urine' es orina y 'feces' es popó."
        )
        
        full_prompt = f"{system_context}\n\nPregunta de Santiago: {text}\nTu respuesta analítica:"
        
        # 3. Call LLM
        ai_response = ask_bedrock_claude(full_prompt)
        
        # 4. Reply to Telegram
        send_telegram_message(chat_id, ai_response)
        
        return {
            "statusCode": 200,
            "body": "OK"
        }
        
    except Exception as e:
        print(f"Webhook Error: {e}")
        return {
            "statusCode": 500,
            "body": "Internal Server Error"
        }
