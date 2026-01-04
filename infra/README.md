# Infraestrutura

Este diretório contém os arquivos de configuração da infraestrutura do backend.

## Arquivos

- `init-db.sh`: Script de inicialização do PostgreSQL que cria os bancos de dados `chat_db` e `keycloak_db`, além de ativar a extensão `pgvector` no `chat_db`. Este script é executado automaticamente na primeira inicialização do container.
- `ensure-databases.sh`: Script auxiliar para garantir que os bancos existam (pode ser executado manualmente se necessário).
- `prometheus.yml`: Configuração do Prometheus para coleta de métricas dos serviços.

## Como funciona

### Inicialização do Banco de Dados

O script `init-db.sh` é executado automaticamente quando o container do PostgreSQL é iniciado pela primeira vez. Ele:

1. Cria o banco `chat_db` (se não existir)
2. Cria o banco `keycloak_db` (se não existir)
3. Ativa a extensão `pgvector` no `chat_db` para suporte a busca vetorial (RAG)

### Prometheus

O arquivo `prometheus.yml` configura o Prometheus para coletar métricas de:
- Próprio Prometheus
- Aplicação FastAPI (endpoint `/metrics`)
- Outros serviços (quando exporters forem adicionados)

## Notas

- O script `init-db.sh` precisa ter permissão de execução no Linux/Mac. No Windows com Docker, isso é gerenciado automaticamente.
- **IMPORTANTE - Problema Comum**: O script `init-db.sh` só é executado na primeira inicialização do PostgreSQL (quando o volume é criado pela primeira vez). Se o volume já existir, o script **NÃO será executado novamente**.
  
  **Se você encontrar o erro "database keycloak_db does not exist":**
  
  1. **Solução Recomendada (apaga todos os dados)**: Remover o volume e recriar:
     ```bash
     docker-compose down -v
     docker-compose up -d
     ```
  
  2. **Solução Alternativa (preserva dados)**: Executar o script manualmente dentro do container:
     ```bash
     docker-compose exec db bash /docker-entrypoint-initdb.d/init-db.sh
     ```
     Ou usar o script `ensure-databases.sh`:
     ```bash
     docker cp backend-ia-proj/infra/ensure-databases.sh backend-ia-db:/tmp/
     docker-compose exec db bash /tmp/ensure-databases.sh
     ```

- O healthcheck do PostgreSQL verifica se os bancos `chat_db` e `keycloak_db` existem antes de marcar o serviço como saudável, garantindo que o Keycloak só inicie após os bancos estarem criados.
- Para modificar as configurações, edite os arquivos e reinicie os containers com `docker-compose restart <service>`.
- Este diretório é referenciado pelo `docker-compose.yml` na raiz de `backend-ia-proj`.
