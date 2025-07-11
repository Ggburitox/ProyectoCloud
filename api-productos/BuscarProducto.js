const AWS = require('aws-sdk');
const dynamodb = new AWS.DynamoDB.DocumentClient();

const TABLE_NAME = process.env.PRODUCTOS_TABLE_NAME || 't_productos';
const TOKENS_TABLE_NAME = process.env.TOKENS_TABLE_NAME || 'tokens-dev';

exports.handler = async (event) => {
  console.log("Evento recibido:", JSON.stringify(event));

  try {
    const body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
    const { tenant_id, producto_id } = body || {};
    const tokenHeader = event.headers?.Authorization;

    if (!tenant_id || !producto_id || !tokenHeader) {
      return {
        statusCode: 400,
        headers: corsHeaders(),
        body: JSON.stringify({
          error: 'Faltan tenant_id, producto_id o token de autorización.'
        }),
      };
    }

    const token = tokenHeader.replace(/^Bearer\s+/i, '');

    const tokenData = await dynamodb.get({
      TableName: TOKENS_TABLE_NAME,
      Key: { token }
    }).promise();

    if (!tokenData.Item || new Date() > new Date(tokenData.Item.expires)) {
      return {
        statusCode: 403,
        headers: corsHeaders(),
        body: JSON.stringify({ error: 'Token inválido o expirado.' }),
      };
    }

    const result = await dynamodb.get({
      TableName: TABLE_NAME,
      Key: { tenant_id, producto_id }
    }).promise();

    if (!result.Item) {
      return {
        statusCode: 404,
        headers: corsHeaders(),
        body: JSON.stringify({ error: 'Producto no encontrado.' }),
      };
    }

    return {
      statusCode: 200,
      headers: corsHeaders(),
      body: JSON.stringify(result.Item),
    };

  } catch (err) {
    console.error("Error interno al buscar producto:", err);
    return {
      statusCode: 500,
      headers: corsHeaders(),
      body: JSON.stringify({
        error: 'Error interno al buscar producto',
        detalle: err.message || 'Error desconocido',
      }),
    };
  }
};

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
  };
}
