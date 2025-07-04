import boto3
import hashlib
import uuid
import json
import os
from datetime import datetime, timedelta

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()

def lambda_handler(event, context):
    try:
        USERS_TABLE = os.environ['USERS_TABLE_NAME']
        TOKENS_TABLE = os.environ['TOKENS_TABLE_NAME']

        body = json.loads(event.get("body", "{}"))
        email = body.get("email")
        password = body.get("password")
        tenant_id = body.get("tenant_id")

        if not email or not password or not tenant_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Email, contraseña y tenant_id son requeridos'})
            }

        usuario_id = email

        dynamodb = boto3.resource('dynamodb')
        tabla_usuarios = dynamodb.Table(USERS_TABLE)
        response = tabla_usuarios.get_item(Key={
            'tenant_id': tenant_id,
            'usuario_id': usuario_id
        })

        if 'Item' not in response:
            return {
                'statusCode': 403,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Usuario no existe o credenciales incorrectas'})
            }

        stored_password_hash = response['Item'].get('password')
        stored_salt = response['Item'].get('salt')

        if not stored_password_hash or not stored_salt:
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Configuración inválida en base de datos'})
            }

        password_to_check_hash = hash_password(password, stored_salt)

        if password_to_check_hash != stored_password_hash:
            return {
                'statusCode': 403,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Credenciales incorrectas'})
            }

        token = str(uuid.uuid4())
        expiration = datetime.utcnow() + timedelta(hours=1)

        registro_token = {
            'token': token,
            'tenant_id': tenant_id,
            'usuario_id': usuario_id,
            'expires': expiration.isoformat()
        }

        tabla_tokens = dynamodb.Table(TOKENS_TABLE)
        tabla_tokens.put_item(Item=registro_token)

        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                "token": token
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'error': 'Error interno en el servidor',
                'detalle': str(e)
            })
        }
