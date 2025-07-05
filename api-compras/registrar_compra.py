import json
import boto3
import uuid
from datetime import datetime
import os

dynamodb = boto3.resource('dynamodb')
tokens_table = dynamodb.Table(os.environ['TOKENS_TABLE_NAME'])
productos_table = dynamodb.Table(os.environ['PRODUCTOS_TABLE_NAME'])
compras_table = dynamodb.Table(os.environ['COMPRAS_TABLE_NAME'])

def lambda_handler(event, context):
    try:
        headers = event.get("headers") or {}
        token = headers.get("Authorization")

        if not token:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Token requerido"})
            }

        # Verificar token
        token_data = tokens_table.get_item(Key={'token': token})
        item = token_data.get('Item')

        if not item or 'tenant_id' not in item or 'usuario_id' not in item or 'expires' not in item:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Token inválido o incompleto"})
            }

        if datetime.utcnow() > datetime.fromisoformat(item['expires']):
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Token expirado"})
            }

        tenant_id = item['tenant_id']         # ← Petshop
        comprador_email = item['usuario_id']  # ← Email del usuario

        # Leer el body del request
        body = json.loads(event.get("body", "{}"))
        producto_id = body.get("producto_id")
        producto_tenant_id = body.get("tenant_id")  # tienda del producto

        if not producto_id or not producto_tenant_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Falta el producto_id o tenant_id del producto"})
            }

        prod_response = productos_table.get_item(Key={
            "tenant_id": producto_tenant_id,
            "producto_id": producto_id
        })
        producto = prod_response.get("Item")

        if not producto:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Producto no encontrado"})
            }

        if producto["stock"] <= 0:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Producto sin stock"})
            }

        productos_table.update_item(
            Key={
                "tenant_id": producto_tenant_id,
                "producto_id": producto_id
            },
            UpdateExpression="SET stock = stock - :val",
            ConditionExpression="stock > :zero",
            ExpressionAttributeValues={":val": 1, ":zero": 0}
        )

        compra_id = str(uuid.uuid4())
        compra_item = {
            "tenant_id": tenant_id,  # ← la tienda que hizo la compra
            "compra_id": compra_id,
            "producto_id": producto_id,
            "producto_tenant_id": producto_tenant_id,  # ← la tienda del producto
            "comprador_email": comprador_email,        # ← el usuario real
            "detalle_producto": {
                "nombre": producto["nombre"],
                "descripcion": producto["descripcion"],
                "precio": producto["precio"]
            },
            "fecha": datetime.utcnow().isoformat()
        }

        compras_table.put_item(Item=compra_item)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "mensaje": "Compra registrada con éxito",
                "compra_id": compra_id
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error interno",
                "detalle": str(e)
            })
        }
