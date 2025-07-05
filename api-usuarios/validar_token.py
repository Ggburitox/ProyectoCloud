import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
tokens_table = dynamodb.Table(os.environ['TOKENS_TABLE_NAME'])

def lambda_handler(event, context):
    try:
        headers = event.get("headers") or {}
        token = headers.get("Authorization")

        if not token:
            return {
                "statusCode": 403,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "Token requerido"})
            }

        # Buscar el token en la tabla
        token_data = tokens_table.get_item(Key={'token': token})
        item = token_data.get('Item')

        if not item or 'tenant_id' not in item or 'expires' not in item:
            return {
                "statusCode": 403,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "Token inválido o incompleto"})
            }

        if datetime.utcnow() > datetime.fromisoformat(item['expires']):
            return {
                "statusCode": 403,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "Token expirado"})
            }

        return {
            "statusCode": 200,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({
                "mensaje": "Token válido",
                "tenant_id": item['tenant_id'],
                "usuario_id": item.get('usuario_id', item['tenant_id'])  # Por compatibilidad
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "Error interno", "detalle": str(e)})
        }
