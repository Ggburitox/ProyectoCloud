import json
import boto3
import hashlib
import uuid
import os

dynamodb = boto3.resource("dynamodb")
USERS_TABLE = os.environ.get("USERS_TABLE_NAME")

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        email = body.get("email")
        password = body.get("password")
        nombre = body.get("nombre")
        apellidos = body.get("apellidos")
        direccion = body.get("direccion")
        tenant_id = body.get("tenant_id")

        if not email or not password or not nombre or not apellidos or not direccion or not tenant_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Faltan campos requeridos'})
            }

        tabla_usuarios = dynamodb.Table(USERS_TABLE)

        # Validar si ya existe el usuario
        result = tabla_usuarios.get_item(Key={
            'tenant_id': tenant_id,
            'usuario_id': email
        })

        if 'Item' in result:
            return {
                'statusCode': 409,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'El usuario ya existe en esta tienda'})
            }

        salt = uuid.uuid4().hex
        password_hash = hash_password(password, salt)

        nuevo_usuario = {
            'tenant_id': tenant_id,
            'usuario_id': email,
            'nombre': nombre,
            'apellidos': apellidos,
            'direccion': direccion,
            'password': password_hash,
            'salt': salt
        }

        tabla_usuarios.put_item(Item=nuevo_usuario)

        return {
            'statusCode': 201,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({"message": "Usuario registrado correctamente"})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Error interno', 'detalle': str(e)})
        }
