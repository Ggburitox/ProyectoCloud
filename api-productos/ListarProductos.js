const AWS = require('aws-sdk');
const dynamodb = new AWS.DynamoDB.DocumentClient();

const TABLE_NAME = process.env.PRODUCTOS_TABLE_NAME || 't_productos';
const LIMITE = 20;

exports.handler = async (event) => {
  console.log("Evento recibido:", event);

  try {

    const body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
    const { tenant_id, startKey } = body || {};

    if (!tenant_id) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'Se requiere tenant_id' }),
      };
    }

    const params = {
      TableName: TABLE_NAME,
      Limit: LIMITE,
      KeyConditionExpression: 'tenant_id = :tenant_id',
      ExpressionAttributeValues: {
        ':tenant_id': tenant_id
      }
    };

    if (startKey) {
      params.ExclusiveStartKey = {
        tenant_id: tenant_id,
        producto_id: startKey
      };
    }

    const result = await dynamodb.query(params).promise();

    return {
      statusCode: 200,
      body: JSON.stringify({
        items: result.Items,
        nextPageToken: result.LastEvaluatedKey?.producto_id || null
      }),
    };

  } catch (err) {
    console.error("Error:", err);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Error al listar productos', detalle: err.message }),
    };
  }
};
