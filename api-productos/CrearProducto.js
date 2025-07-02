const AWS = require('aws-sdk');
const lambda = new AWS.Lambda();
const dynamodb = new AWS.DynamoDB.DocumentClient();

const TABLE_NAME = process.env.PRODUCTOS_TABLE_NAME || 't_productos';

exports.handler = async (event) => {
  console.log("Evento recibido:", event);

  try {
    const body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
    const { tenant_id, producto_id, nombre, precio } = body || {};
    const token = event.headers?.Authorization;

    if (!tenant_id || !producto_id || !nombre || !precio || !token) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          error: 'Faltan tenant_id, producto_id, nombre, precio o el token de autorización.'
        }),
      };
    }

    const invokeResult = await lambda.invoke({
      FunctionName: 'validar_token',
      InvocationType: 'RequestResponse',
      Payload: JSON.stringify({ token })
    }).promise();

    const authResponse = JSON.parse(invokeResult.Payload);
    if (authResponse.statusCode === 403) {
      return {
        statusCode: 403,
        body: JSON.stringify({ error: 'Forbidden - Acceso No Autorizado' }),
      };
    }

    await dynamodb.put({
      TableName: TABLE_NAME,
      Item: { tenant_id, producto_id, nombre, precio }
    }).promise();

    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'Producto creado correctamente' }),
    };
  } catch (err) {
    console.error("Error:", err);
    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Error interno al guardar el producto',
        detalle: err.message,
      }),
    };
  }
};
