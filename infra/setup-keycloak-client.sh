#!/bin/bash
set -e

# Script para configurar o cliente Keycloak automaticamente
# Este script cria o cliente "chat-api" no realm "master" do Keycloak

echo "Setting up Keycloak client..."

# Configurações
KEYCLOAK_URL=${KEYCLOAK_URL:-http://localhost:8080}
KEYCLOAK_ADMIN=${KEYCLOAK_ADMIN:-admin}
KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD:-admin}
REALM=${KEYCLOAK_REALM:-master}
CLIENT_ID=${KEYCLOAK_CLIENT_ID:-chat-api}
FRONTEND_URL=${FRONTEND_URL:-http://localhost:3001}

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

echo "Keycloak is ready. Getting admin token..."

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

echo "Admin token obtained. Checking if client exists..."

# Verificar se o cliente já existe
EXISTING_CLIENT=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${REALM}/clients?clientId=${CLIENT_ID}" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -H "Content-Type: application/json")

CLIENT_COUNT=$(echo "$EXISTING_CLIENT" | jq '. | length')

if [ "$CLIENT_COUNT" -gt 0 ]; then
    echo "Client '${CLIENT_ID}' already exists. Updating configuration..."
    
    # Obter ID do cliente existente
    CLIENT_UUID=$(echo "$EXISTING_CLIENT" | jq -r '.[0].id')
    
    # Atualizar configuração do cliente
    CLIENT_CONFIG=$(cat <<EOF
{
    "clientId": "${CLIENT_ID}",
    "name": "Chat API Client",
    "description": "Client for Chat API frontend application",
    "enabled": true,
    "publicClient": true,
    "standardFlowEnabled": true,
    "implicitFlowEnabled": false,
    "directAccessGrantsEnabled": true,
    "serviceAccountsEnabled": false,
    "redirectUris": [
        "${FRONTEND_URL}/auth/callback",
        "${FRONTEND_URL}/*",
        "${FRONTEND_URL}/magic-link/callback",
        "http://localhost:3000/auth/callback",
        "http://localhost:3000/*",
        "http://localhost:3000/magic-link/callback",
        "http://localhost:3001/magic-link/callback"
    ],
    "webOrigins": [
        "${FRONTEND_URL}",
        "http://localhost:3000",
        "http://localhost:3001"
    ],
    "attributes": {
        "post.logout.redirect.uris": "${FRONTEND_URL}/*"
    }
}
EOF
)
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT "${KEYCLOAK_URL}/admin/realms/${REALM}/clients/${CLIENT_UUID}" \
        -H "Authorization: Bearer ${ADMIN_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$CLIENT_CONFIG")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" -eq 204 ] || [ "$HTTP_CODE" -eq 200 ]; then
        echo "Client '${CLIENT_ID}' updated successfully!"
    else
        echo "WARNING: Client update returned HTTP $HTTP_CODE"
        echo "$RESPONSE" | head -n-1
    fi
else
    echo "Client '${CLIENT_ID}' does not exist. Creating new client..."
    
    # Criar novo cliente
    CLIENT_CONFIG=$(cat <<EOF
{
    "clientId": "${CLIENT_ID}",
    "name": "Chat API Client",
    "description": "Client for Chat API frontend application",
    "enabled": true,
    "publicClient": true,
    "standardFlowEnabled": true,
    "implicitFlowEnabled": false,
    "directAccessGrantsEnabled": true,
    "serviceAccountsEnabled": false,
    "redirectUris": [
        "${FRONTEND_URL}/auth/callback",
        "${FRONTEND_URL}/*",
        "${FRONTEND_URL}/magic-link/callback",
        "http://localhost:3000/auth/callback",
        "http://localhost:3000/*",
        "http://localhost:3000/magic-link/callback",
        "http://localhost:3001/magic-link/callback"
    ],
    "webOrigins": [
        "${FRONTEND_URL}",
        "http://localhost:3000",
        "http://localhost:3001"
    ],
    "attributes": {
        "post.logout.redirect.uris": "${FRONTEND_URL}/*"
    }
}
EOF
)
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${KEYCLOAK_URL}/admin/realms/${REALM}/clients" \
        -H "Authorization: Bearer ${ADMIN_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$CLIENT_CONFIG")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" -eq 201 ] || [ "$HTTP_CODE" -eq 200 ]; then
        echo "Client '${CLIENT_ID}' created successfully!"
    else
        echo "ERROR: Client creation returned HTTP $HTTP_CODE"
        echo "$RESPONSE" | head -n-1
        exit 1
    fi
fi

# Verificar se o cliente foi criado corretamente
echo "Verifying client configuration..."
FINAL_CHECK=$(curl -s -X GET "${KEYCLOAK_URL}/admin/realms/${REALM}/clients?clientId=${CLIENT_ID}" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -H "Content-Type: application/json")

FINAL_COUNT=$(echo "$FINAL_CHECK" | jq '. | length')
if [ "$FINAL_COUNT" -gt 0 ]; then
    echo "✓ Client '${CLIENT_ID}' is properly configured in realm '${REALM}'"
    echo "✓ Client enabled: $(echo "$FINAL_CHECK" | jq -r '.[0].enabled')"
    echo "✓ Public client: $(echo "$FINAL_CHECK" | jq -r '.[0].publicClient')"
    echo "✓ Standard flow enabled: $(echo "$FINAL_CHECK" | jq -r '.[0].standardFlowEnabled')"
    echo "✓ Redirect URIs: $(echo "$FINAL_CHECK" | jq -r '.[0].redirectUris | join(", ")')"
else
    echo "ERROR: Client verification failed - client not found after setup"
    exit 1
fi

echo "Keycloak client setup completed!"

