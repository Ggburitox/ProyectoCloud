import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
tokens_table = dynamodb.Table(os.environ['TOKENS_TABLE_NAME'])
compras_table = dynamodb.Table(os.environ['COMPRAS_TABLE_NAME'])

cors_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*"
}

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError("No serializable")

def lambda_handler(event, context):
    try:
        headers = event.get("headers") or {}
        token = headers.get("Authorization")

        if not token:
            return {
                "statusCode": 403,
                "headers": cors_headers,
                "body": json.dumps({"error": "Token requerido"})
            }

        token_data = tokens_table.get_item(Key={'token': token})
        token_item = token_data.get("Item")

        if not token_item or 'tenant_id' not in token_item or 'usuario_id' not in token_item or 'expires' not in token_item:
            return {
                "statusCode": 403,
                "headers": cors_headers,
                "body": json.dumps({"error": "Token inválido o incompleto"})
            }

        if datetime.utcnow() > datetime.fromisoformat(token_item['expires']):
            return {
                "statusCode": 403,
                "headers": cors_headers,
                "body": json.dumps({"error": "Token expirado"})
            }

        tenant_id = token_item["tenant_id"]
        usuario_id = token_item["usuario_id"]
        scan_result = compras_table.scan()
        todas_compras = scan_result.get("Items", [])

        compras_usuario = [
            compra for compra in todas_compras
            if compra.get("tenant_id") == tenant_id and compra.get("comprador_email") == usuario_id
        ]

        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({"compras": compras_usuario}, default=decimal_default)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({
                "error": "Error interno",
                "detalle": str(e)
            })
        }
