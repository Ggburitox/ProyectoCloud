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
          error: 'Se requieren tenant_id, producto_id y token'
        }),
      };
    }

    // Validar token
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

    await dynamodb.delete({
      TableName: TABLE_NAME,
      Key: { tenant_id, producto_id }
    }).promise();

    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'Producto eliminado correctamente' }),
    };

  } catch (err) {
    console.error("Error:", err);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Error al eliminar producto', detalle: err.message }),
    };
  }
};
