const AWS = require('aws-sdk');
const lambda = new AWS.Lambda();
const dynamodb = new AWS.DynamoDB.DocumentClient();

const TABLE_NAME = process.env.PRODUCTOS_TABLE_NAME || 't_productos';

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
          error: 'Faltan tenant_id, producto_id o el token de autorización.'
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
      body: JSON.stringify({
        error: 'Error interno al buscar producto',
        detalle: err.message,
      }),
    };
  }
};
