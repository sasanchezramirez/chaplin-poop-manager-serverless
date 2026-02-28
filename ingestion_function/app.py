import json
import os
import boto3
import urllib.request
import urllib.parse
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME', 'ChaplinEvents')
table = dynamodb.Table(table_name)
expected_api_key = os.environ.get('API_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def lambda_handler(event, context):
    try:
        # Simple API Key Authorization check
        headers = event.get('headers', {})
        api_key = headers.get('x-api-key')
        
        if not expected_api_key or api_key != expected_api_key:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Forbidden: Invalid x-api-key"})
            }
            
        body = json.loads(event.get('body', '{}'))
        
        pet_id = body.get('pet_id')
        duration_seconds = body.get('duration_seconds')
        timestamp = body.get('timestamp')
        
        if not pet_id or duration_seconds is None or not timestamp:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: pet_id, duration_seconds, timestamp"})
            }
            
        # Estimate the type based on duration (empirical threshold)
        # Assuming < 60s is pee, >= 60s is poop
        estimated_type = "urine" if int(duration_seconds) < 60 else "feces"
        
        item = {
            'pet_id': str(pet_id),
            # DynamoDB partition and sort keys expect exact type matching.
            # Convert to int to match the N (Number) type in the table definition.
            'timestamp': int(timestamp),
            'duration_seconds': int(duration_seconds),
            'estimated_type': estimated_type,
            'received_at': int(datetime.utcnow().timestamp())
        }
        
        # Write to DynamoDB
        table.put_item(Item=item)
        
        # --- Telegram Integration ---
        try:
            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                tipo_msg = "un popó 💩" if estimated_type == "feces" else "un pipí 💧"
                message_text = f"🐾 *¡Alerta Arenero!*\n\nChaplin acaba de hacer {tipo_msg}.\n⏱️ Duración: {duration_seconds} segundos."
                
                telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                data = urllib.parse.urlencode({
                    'chat_id': TELEGRAM_CHAT_ID,
                    'text': message_text,
                    'parse_mode': 'Markdown'
                }).encode('utf-8')
                
                req = urllib.request.Request(telegram_url, data=data, method='POST')
                with urllib.request.urlopen(req, timeout=5) as response:
                    print(f"Telegram notification sent. Status: {response.status}")
        except Exception as tel_err:
            print(f"Failed to send Telegram notification: {str(tel_err)}")
            # We don't return an error to the user if ONLY telegram fails.
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Event successfully recorded",
                "item": item
            })
        }
        
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON body"})
        }
    except Exception as e:
        print(f"Error processing event: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
