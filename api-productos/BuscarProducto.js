const AWS = require('aws-sdk');
const dynamodb = new AWS.DynamoDB.DocumentClient();

const TABLE_NAME = process.env.PRODUCTOS_TABLE_NAME || 't_productos';
const TOKENS_TABLE_NAME = process.env.TOKENS_TABLE_NAME || 'tokens-dev';

exports.handler = async (event) => {
  console.log("Evento recibido:", event);

  try {
    const body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
    const { tenant_id, producto_id } = body || {};
    const token = event.headers?.Authorization;

    if (!tenant_id || !producto_id || !token) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'Faltan tenant_id, producto_id o token de autorización.'
        }),
      };
    }

    const tokenData = await dynamodb.get({ TableName: TOKENS_TABLE_NAME, Key: { token } }).promise();
    if (!tokenData.Item || new Date() > new Date(tokenData.Item.expires)) {
      return {
        statusCode: 403,
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
        body: JSON.stringify({ error: 'Producto no encontrado' }),
      };
    }

    return {
      statusCode: 200,
      body: JSON.stringify(result.Item),
    };

  } catch (err) {
    console.error("Error:", err);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Error interno al buscar producto', detalle: err.message }),
    };
  }
};
