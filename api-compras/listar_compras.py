import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
compras_table = dynamodb.Table(os.environ['COMPRAS_TABLE_NAME'])
tokens_table = dynamodb.Table(os.environ['TOKENS_TABLE_NAME'])

def lambda_handler(event, context):
    try:
        token = event.get("headers", {}).get("Authorization")

        if not token:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Token requerido"})
            }

        token_resp = tokens_table.get_item(Key={"token": token})
        token_data = token_resp.get("Item")
        if not token_data or datetime.utcnow() > datetime.fromisoformat(token_data["expires"]):
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Token inválido o expirado"})
            }

        tenant_id = token_data["tenant_id"]

        response = compras_table.query(
            KeyConditionExpression="tenant_id = :tid",
            ExpressionAttributeValues={":tid": tenant_id}
        )

        return {
            "statusCode": 200,
            "body": json.dumps({"compras": response.get("Items", [])})
        }

    except Exception as e:
        print("Error:", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Error interno", "detalle": str(e)})
        }
