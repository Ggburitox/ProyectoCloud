const AWS = require('aws-sdk');
const axios = require('axios');
const dynamodb = new AWS.DynamoDB.DocumentClient();

const TABLE_NAME = process.env.PRODUCTOS_TABLE_NAME || 't_productos';
const VALIDAR_TOKEN_URL = 'https://n7rvm0z7c1.execute-api.us-east-1.amazonaws.com/dev/usuario/validar';

exports.handler = async (event) => {
  console.log("Evento recibido:", event);

  try {
    const body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
    const { tenant_id, producto_id, nombre, precio } = body || {};
    const token = event.headers?.Authorization;

    // Validación básica
    if (!tenant_id || !producto_id || !nombre || !precio || !token) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'Faltan tenant_id, producto_id, nombre, precio o el token de autorización.'
        }),
      };
    }

    // Validación de token vía HTTP
    try {
      const authResponse = await axios.post(
        VALIDAR_TOKEN_URL,
        { token }
      );

      if (authResponse.status === 403) {
        return {
          statusCode: 403,
          body: JSON.stringify({ error: 'Forbidden - Acceso No Autorizado' }),
        };
      }
    } catch (authError) {
      console.error("Error en validación de token:", authError.message);
      return {
        statusCode: 403,
        body: JSON.stringify({ error: 'Token inválido o error al validar' }),
      };
    }

    // Guardar en DynamoDB
    await dynamodb.put({
      TableName: TABLE_NAME,
      Item: { tenant_id, producto_id, nombre, precio }
    }).promise();

    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'Producto creado correctamente' }),
    };

  } catch (err) {
    console.error("Error general:", err);
    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Error interno al guardar el producto',
        detalle: err.message,
      }),
    };
  }
};
