const AWS = require('aws-sdk');
const dynamodb = new AWS.DynamoDB.DocumentClient();

const TABLE_NAME = process.env.PRODUCTOS_TABLE_NAME || 't_productos';
const TOKENS_TABLE_NAME = process.env.TOKENS_TABLE_NAME || 'tokens-dev'; 

exports.handler = async (event) => {
  console.log("Evento recibido:", JSON.stringify(event));

  try {

    const body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
    const { tenant_id, producto_id, nombre, descripcion, precio, stock } = body || {};

    const token = event.headers?.Authorization;

    if (!tenant_id || !producto_id || !nombre || !precio || !stock || !token) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'Faltan tenant_id, producto_id, nombre, precio, stock o el token de autorización.'
        }),
      };
    }

    const tokenData = await dynamodb.get({
      TableName: TOKENS_TABLE_NAME,
      Key: { token }
    }).promise();

    if (!tokenData.Item) {
      return {
        statusCode: 403,
        body: JSON.stringify({ error: 'Token inválido o no encontrado.' }),
      };
    }

    const expires = new Date(tokenData.Item.expires);
    if (new Date() > expires) {
      return {
        statusCode: 403,
        body: JSON.stringify({ error: 'Token expirado.' }),
      };
    }

    await dynamodb.put({
      TableName: TABLE_NAME,
      Item: { tenant_id, producto_id, nombre, descripcion, precio, stock }
    }).promise();

    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'Producto creado correctamente' }),
    };
  } catch (err) {
    console.error("Error interno:", err);
    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Error interno al guardar el producto',
        detalle: err.message,
      }),
    };
  }
};
