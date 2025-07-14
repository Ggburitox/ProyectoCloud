const AWS = require('aws-sdk');
const dynamodb = new AWS.DynamoDB.DocumentClient();

const TABLE_NAME = process.env.PRODUCTOS_TABLE_NAME || 't_productos';
const TOKENS_TABLE_NAME = process.env.TOKENS_TABLE_NAME || 'tokens-dev';

exports.handler = async (event) => {
  console.log("Evento recibido:", event);

  try {
    const body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
    const { tenant_id, producto_id, nombre, precio } = body || {};
    const token = event.headers?.Authorization;

    if (!tenant_id || !producto_id || !token || (!nombre && !precio)) {
      return {
        statusCode: 400,
        headers: corsHeaders(),
        body: JSON.stringify({ error: 'Se requieren tenant_id, producto_id, token y al menos nombre o precio' }),
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

    let updateExpr = 'set';
    const attrValues = {};

    if (nombre) {
      updateExpr += ' nombre = :n,';
      attrValues[':n'] = nombre;
    }
    if (precio) {
      updateExpr += ' precio = :p,';
      attrValues[':p'] = precio;
    }
    updateExpr = updateExpr.slice(0, -1); // quitar coma final

    await dynamodb.update({
      TableName: TABLE_NAME,
      Key: { tenant_id, producto_id },
      UpdateExpression: updateExpr,
      ExpressionAttributeValues: attrValues
    }).promise();

    return {
      statusCode: 200,
      headers: corsHeaders(),
      body: JSON.stringify({ message: 'Producto modificado correctamente' }),
    };

  } catch (err) {
    console.error("Error:", err);
    return {
      statusCode: 500,
      headers: corsHeaders(),
      body: JSON.stringify({ error: 'Error al modificar producto', detalle: err.message }),
    };
  }
};

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE',
  };
}
