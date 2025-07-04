import json
import boto3
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
tokens_table = dynamodb.Table(os.environ['TOKENS_TABLE_NAME'])
compras_table = dynamodb.Table(os.environ['COMPRAS_TABLE_NAME'])

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    try:
        headers = event.get("headers") or {}
        token = headers.get("Authorization")

        if not token:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Token requerido"})
            }

        token_data = tokens_table.get_item(Key={'token': token})
        item = token_data.get("Item")

        if not item or 'tenant_id' not in item or 'expires' not in item:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Token inválido o incompleto"})
            }

        tenant_id = item['tenant_id']  # ← CORREGIDO

        compras = compras_table.query(
            KeyConditionExpression=Key("tenant_id").eq(tenant_id)
        )

        return {
            "statusCode": 200,
            "body": json.dumps({"compras": compras.get("Items", [])}, default=decimal_default)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error interno",
                "detalle": str(e)
            })
        }
