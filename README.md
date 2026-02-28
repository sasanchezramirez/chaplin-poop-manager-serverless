# Chaplin Poop Manager - AWS Serverless

Este es el backend Serverless para Chaplin Poop Manager, definido usando AWS SAM (Serverless Application Model). Contiene una base de datos DynamoDB, un API Gateway (HTTP API) y una función AWS Lambda para ingerir los datos del ESP32.

## Requisitos previos

1. Descargar e instalar AWS CLI: `brew install awscli` (y configurar credenciales `aws configure`).
2. Descargar e instalar AWS SAM CLI: `brew install aws/tap/aws-sam-cli`.

## Estructura del Proyecto

* `template.yaml`: El archivo de infraestructura como código (IaC).
* `ingestion_function/app.py`: La lógica de la función Lambda que procesa el payload, calcula si es orina o heces, y guarda en BD.

## Despliegue en AWS

Ejecuta los siguientes comandos desde este mismo directorio (ChaplinPoopManager-AWS):

1. **Construir el proyecto:**
   ```bash
   sam build
   ```

2. **Desplegar en AWS:**
   La primera vez que despliegues, usa el comando "guided" para configurar las opciones.
   ```bash
   sam deploy --guided
   ```
   * Te pedirá el nombre de tu stack de cloudformation (ej. `chaplin-poop-manager`).
   * Te pedirá una región (ej. `us-east-1`).
   * Te pedirá el parámetro `ChaplinApiKey`. **Establece aquí tu contraseña secreta** que usarás después en el código C++ del ESP32. Por defecto es `chaplin-super-secret-key-change-me`.
   * Acepta permitir que SAM cree roles de IAM.
   * Acepta desplegar los cambios.

3. **Obtener el Endpoint HTTP:**
   Una vez finalice, la consola devolverá unos "Outputs". Copia el valor de `ApiEndpoint`. Ese URL es al que debe llamar el ESP32.

## Prueba del Endpoint

Puedes simular una llamada desde la terminal a la URL generada en el paso anterior, agregando el Header `x-api-key`:

```bash
curl -X POST \
  https://XXXX.execute-api.us-east-1.amazonaws.com/ingest \
  -H "Content-Type: application/json" \
  -H "x-api-key: <TU_API_KEY>" \
  -d '{
    "pet_id": "chaplin",
    "duration_seconds": 75,
    "timestamp": 1718911520
  }'
```
