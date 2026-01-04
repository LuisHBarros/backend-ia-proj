#!/bin/bash
set -e

# Script para habilitar o registro de usuários no Keycloak
# Isso permite que novos usuários se registrem através da interface do Keycloak

echo "Enabling user registration in Keycloak..."

# Configurações
KEYCLOAK_URL=${KEYCLOAK_URL:-http://localhost:8080}
KEYCLOAK_ADMIN=${KEYCLOAK_ADMIN:-admin}
KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD:-admin}
REALM=${KEYCLOAK_REALM:-master}

# Aguardar Keycloak estar pronto
echo "Waiting for Keycloak to be ready..."
MAX_RETRIES=60
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -f "${KEYCLOAK_URL}/health/ready" > /dev/null 2>&1 || curl -s -f "${KEYCLOAK_URL}" > /dev/null 2>&1; then
        echo "Keycloak is ready!"
        break
    fi
    echo "Waiting for Keycloak... (${RETRY_COUNT}/${MAX_RETRIES})"
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "ERROR: Keycloak did not become ready in time"
    exit 1
fi

echo "Getting admin token..."

# Obter token de administrador
ADMIN_TOKEN=$(curl -s -X POST "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${KEYCLOAK_ADMIN}" \
    -d "password=${KEYCLOAK_ADMIN_PASSWORD}" \
    -d "grant_type=password" \
    -d "client_id=admin-cli" | jq -r '.access_token')

if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" = "null" ]; then
    echo "ERROR: Failed to get admin token"
    exit 1
fi

echo "Admin token obtained. Updating realm settings..."

# Obter configuração atual do realm
REALM_CONFIG=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${REALM}" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -H "Content-Type: application/json")

# Verificar se já está habilitado
REGISTRATION_ENABLED=$(echo "$REALM_CONFIG" | jq -r '.registrationAllowed')

if [ "$REGISTRATION_ENABLED" = "true" ]; then
    echo "✓ User registration is already enabled in realm '${REALM}'"
else
    echo "Enabling user registration..."
    
    # Atualizar apenas o campo registrationAllowed
    UPDATED_CONFIG=$(echo "$REALM_CONFIG" | jq '.registrationAllowed = true')
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT "${KEYCLOAK_URL}/admin/realms/${REALM}" \
        -H "Authorization: Bearer ${ADMIN_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$UPDATED_CONFIG")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" -eq 204 ] || [ "$HTTP_CODE" -eq 200 ]; then
        echo "✓ User registration enabled successfully!"
    else
        echo "WARNING: Registration update returned HTTP $HTTP_CODE"
        echo "$RESPONSE" | head -n-1
    fi
fi

# Verificar configuração final
echo "Verifying realm configuration..."
FINAL_CONFIG=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${REALM}" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -H "Content-Type: application/json")

echo "✓ Registration allowed: $(echo "$FINAL_CONFIG" | jq -r '.registrationAllowed')"
echo "✓ Registration email as username: $(echo "$FINAL_CONFIG" | jq -r '.registrationEmailAsUsername')"
echo "✓ Edit username allowed: $(echo "$FINAL_CONFIG" | jq -r '.editUsernameAllowed')"

echo "Keycloak registration setup completed!"
echo ""
echo "Users can now register at:"
echo "${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/auth?...&kc_action=REGISTER"

