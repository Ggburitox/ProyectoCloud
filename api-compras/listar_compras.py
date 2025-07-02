import boto3
import json
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')
TABLE_NAME = os.environ['COMPRAS_TABLE_NAME']

def lambda_handler(event, context):
    try:
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

        table = dynamodb.Table(TABLE_NAME)

        resultado = table.query(
            KeyConditionExpression=Key('tenant_id').eq(tenant_id),
            Limit=20
        )

        return {
            'statusCode': 200,
            'body': json.dumps(resultado.get('Items', []))
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Error al listar compras', 'detalle': str(e)})
        }
