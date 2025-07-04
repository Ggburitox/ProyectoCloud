import boto3
import json
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
productos_table = dynamodb.Table(os.environ['PRODUCTOS_TABLE_NAME'])
compras_table = dynamodb.Table(os.environ['COMPRAS_TABLE_NAME'])
tokens_table = dynamodb.Table(os.environ['TOKENS_TABLE_NAME'])

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        token = event.get("headers", {}).get("Authorization")
        producto_id = body.get("producto_id")

        if not token or not producto_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Faltan token o producto_id"})
            }

        # Validar token
        token_resp = tokens_table.get_item(Key={"token": token})
        token_data = token_resp.get("Item")
        if not token_data or datetime.utcnow() > datetime.fromisoformat(token_data["expires"]):
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Token inválido o expirado"})
            }

        tenant_id = token_data["tenant_id"]

        # Obtener producto
        producto_resp = productos_table.get_item(Key={"tenant_id": tenant_id, "producto_id": producto_id})
        producto = producto_resp.get("Item")
        if not producto:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Producto no encontrado"})
            }

        if producto["stock"] <= 0:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Stock insuficiente"})
            }

        # Restar stock
        productos_table.update_item(
            Key={"tenant_id": tenant_id, "producto_id": producto_id},
            UpdateExpression="SET stock = stock - :dec",
            ConditionExpression="stock > :zero",
            ExpressionAttributeValues={":dec": 1, ":zero": 0}
        )

        # Registrar compra
        compra_id = str(uuid.uuid4())
        compras_table.put_item(Item={
            "tenant_id": tenant_id,
            "compra_id": compra_id,
            "producto_id": producto_id,
            "detalle_producto": {
                "nombre": producto["nombre"],
                "descripcion": producto["descripcion"],
                "precio": producto["precio"]
            },
            "fecha": datetime.utcnow().isoformat()
        })

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Compra registrada correctamente"})
        }

    except Exception as e:
        print("Error:", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Error interno", "detalle": str(e)})
        }
