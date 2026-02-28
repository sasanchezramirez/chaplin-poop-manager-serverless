#!/bin/bash

# Este script empaqueta y despliega la aplicación Serverless usando AWS SAM
# Forzamos --no-session para evitar el error de CloudFormation al crear roles IAM con sesiones temporales de STS.

echo "Iniciando build con SAM..."
aws-vault exec gauge-life --no-session -- sam build

if [ $? -eq 0 ]; then
    echo "🏗️  Build completado. Iniciando deploy..."
    aws-vault exec gauge-life --no-session -- sam deploy
else
    echo "❌ Falló el build. Abortando deploy."
    exit 1
fi
