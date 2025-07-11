#!/bin/bash

STAGES=("dev" "prod" "test")

for stage in "${STAGES[@]}"; do
  echo "Desplegando api-compras en stage: $stage"
  sls deploy --stage $stage
  echo "Desplegado en $stage"
  echo "-----------------------------"
done

echo "Todos los stages de api-usuarios desplegados."
