import boto3
import json
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')
TABLE_NAME = os.environ['COMPRAS_TABLE_NAME']

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        token = event['headers'].get('Authorization')

        if not token:
            return {'statusCode': 403, 'body': json.dumps({'error': 'Token requerido'})}

        # Validar token
        payload = json.dumps({ 'token': token })
        response = lambda_client.invoke(
            FunctionName='validar_token',
            InvocationType='RequestResponse',
            Payload=payload
        )

        auth_response = json.loads(response['Payload'].read())
        if auth_response.get('statusCode') == 403:
            return {'statusCode': 403, 'body': json.dumps({'error': 'Token inválido'})}

        usuario_data = json.loads(auth_response['body'])
        tenant_id = usuario_data['usuario_id']

        # Datos de la compra
        compra = {
            'tenant_id': tenant_id,
            'compra_id': str(uuid.uuid4()),
            'producto_id': body.get('producto_id'),
            'cantidad': body.get('cantidad'),
            'precio_total': body.get('precio_total'),
            'fecha': datetime.utcnow().isoformat()
        }

        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item=compra)

        return {
            'statusCode': 201,
            'body': json.dumps({'mensaje': 'Compra registrada correctamente'})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Error al registrar compra', 'detalle': str(e)})
        }
