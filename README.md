# Chaplin Poop Manager - Serverless Backend

Este es el backend Serverless para **Chaplin Poop Manager**, construido con AWS SAM (Serverless Application Model). Contiene una base de datos DynamoDB, un API Gateway y dos funciones AWS Lambda: una para ingerir los datos del arenero (ESP32) y notificarte, y otra para actuar como un bot conversacional impulsado por Inteligencia Artificial.

## 🌟 Características Actuales (Features)

1. **Ingesta de Datos Inteligente (`ingestion_function`):**
   - Recibe datos del sensor ESP32 a través de una API HTTP.
   - Seguridad mediante `x-api-key`.
   - Clasificación automática (orina vs. heces) basada en la duración de la estadía de Chaplin en el arenero.
   - Guardado asíncrono en Amazon DynamoDB bajo demanda (Pay-Per-Request).
   - **NUEVO:** Envía notificaciones instantáneas a tu Telegram cada vez que Chaplin va al baño.

2. **Asistente de IA Conversacional (`telegram_webhook`):**
   - Integración bidireccional con Telegram mediante Webhooks.
   - **NUEVO:** Conectado a **Amazon Bedrock (Claude 3 Haiku)**.
   - Permite chatear con el bot en Telegram en lenguaje natural (ej. *"¿A qué hora promedio hizo digestión Chaplin si comió a las 2pm?"*).
   - Utiliza una técnica de RAG (Retrieval-Augmented Generation) para leer los datos de los últimos 7 días de DynamoDB y responder preguntas analíticas exactas sobre la salud y hábitos del gato.

---

## 📂 Estructura del Proyecto

* `template.yaml`: El archivo principal de infraestructura como código (CloudFormation/SAM).
* `samconfig.toml`: Archivo excluido de Git (.gitignore) que guarda tus tokens, llaves de API y configuraciones de AWS.
* `deploy.sh`: Script automatizado seguro para realizar empaquetado y despliegue rápido usando `aws-vault`.
* `ingestion_function/app.py`: Lógica de la Lambda que recibe datos del ESP32, guarda en DynamoDB y notifica a Telegram.
* `telegram_webhook/app.py`: Lógica del chatbot interactivo conectado a AWS Bedrock.

---

## 🚀 Despliegue Rápido y Seguro

Ejecuta el script personalizado desde este directorio. Esto evitará problemas de tokens STS (`Security token invalid`) en CloudFormation si usas credenciales temporales o `aws-vault`.

```bash
chmod +x deploy.sh
./deploy.sh
```

*(Nota: Asegúrate de tener tu archivo `samconfig.toml` con las variables y tokens vigentes antes de lanzar el deploy).*

---

## 🤖 Configuración de la IA y Telegram

### 1. Activar Amazon Bedrock
Para que el bot conversacional funcione, **debes aceptar los términos de uso de Anthropic** en AWS:
1. Ve a la consola de **AWS > Amazon Bedrock > Chat (Playgrounds)**.
2. Haz clic en "Select Model" y elige **Anthropic Claude 3 Haiku**.
3. Haz clic en el mensaje de **"Submit use case details"**. Llena el formulario breve (es gratis y automático).
4. Espera a que diga *Access granted*.

### 2. Configurar el Webhook de Telegram
Después de desplegar (`./deploy.sh`), toma la URL que te retorna CloudFormation llamada `WebhookEndpoint` (ej. `https://XXXX.../telegram-webhook`) y ejecuta este comando para enlazar tu bot de Telegram con AWS:

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=<WEBHOOK_ENDPOINT_AQUI>"
```

---

## 🧪 Cómo probar el Sensor (ESP32 / API)

Puedes simular el ESP32 desde la terminal mandando un Payload a la URL de `ApiEndpoint`:

```bash
curl -X POST \
  https://XXXX.execute-api.us-east-1.amazonaws.com/ingest \
  -H "Content-Type: application/json" \
  -H "x-api-key: <TU_API_KEY>" \
  -d '{
    "pet_id": "chaplin",
    "duration_seconds": 75,
    "timestamp": '$(date +%s)'
  }'
```
