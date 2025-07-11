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
        headers: corsHeaders(),
        body: JSON.stringify({ error: 'Se requieren tenant_id, producto_id y token' }),
      };
    }

    const tokenData = await dynamodb.get({ TableName: TOKENS_TABLE_NAME, Key: { token } }).promise();
    if (!tokenData.Item || new Date() > new Date(tokenData.Item.expires)) {
      return {
        statusCode: 403,
        headers: corsHeaders(),
        body: JSON.stringify({ error: 'Token inválido o expirado.' }),
      };
    }

    await dynamodb.delete({
      TableName: TABLE_NAME,
      Key: { tenant_id, producto_id }
    }).promise();

    return {
      statusCode: 200,
      headers: corsHeaders(),
      body: JSON.stringify({ message: 'Producto eliminado correctamente' }),
    };

  } catch (err) {
    console.error("Error:", err);
    return {
      statusCode: 500,
      headers: corsHeaders(),
      body: JSON.stringify({ error: 'Error al eliminar producto', detalle: err.message }),
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
