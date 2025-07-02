import boto3
import os
import json
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
TOKENS_TABLE = os.environ.get('TOKENS_TABLE_NAME', 't_tokens')

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        token = body.get("token")

        if not token:
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Token requerido'})
            }

        tabla = dynamodb.Table(TOKENS_TABLE)
        response = tabla.get_item(Key={'token': token})

        if 'Item' not in response:
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Token inválido o no encontrado'})
            }

        item = response['Item']
        expires_str = item.get('expires')

        if not expires_str:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Token sin expiración registrada'})
            }

        expires = datetime.strptime(expires_str, '%Y-%m-%d %H:%M:%S')
        now = datetime.utcnow()

        if now > expires:
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Token expirado'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({
                'mensaje': 'Token válido',
                'usuario_id': item['usuario_id'],
                'rol': item.get('rol', 'cliente')  # Por si usas roles luego
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Error interno al validar token', 'detalle': str(e)})
        }
