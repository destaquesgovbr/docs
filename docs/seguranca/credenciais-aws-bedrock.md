# Gerenciamento de Credenciais AWS Bedrock

Guia de segurança para gerenciar credenciais AWS Bedrock no DestaquesGovbr.

---

## 🔒 Princípios de Segurança

1. **Nunca commitar credenciais** no Git
2. **Usar IAM roles** sempre que possível (em AWS)
3. **Rotacionar credenciais** periodicamente (90 dias)
4. **Princípio de privilégio mínimo** (apenas permissões necessárias)
5. **Monitorar uso** com CloudTrail e CloudWatch

---

## 🎯 Modos de Autenticação

### 1. Desenvolvimento Local (Padrão)

Usa credenciais locais do AWS CLI.

**Setup**:
```bash
# Configurar via AWS CLI
aws configure

# Ou manualmente editar ~/.aws/credentials:
[default]
aws_access_key_id = AKIA...
aws_secret_access_key = ...
region = us-east-1
```

**Uso no código**:
```python
from news_enrichment import BedrockLLMClient

# Usa ~/.aws/credentials automaticamente
client = BedrockLLMClient(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    region="us-east-1"
)
```

---

### 2. Produção com Variáveis de Ambiente

**Recomendado para**: Cloud Run, containers, CI/CD.

**Setup**:
```bash
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_DEFAULT_REGION="us-east-1"
```

**Cloud Run**:
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: enrichment-worker
spec:
  template:
    spec:
      containers:
      - image: gcr.io/.../enrichment:latest
        env:
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: aws-credentials
              key: access_key_id
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: aws-credentials
              key: secret_access_key
```

**Criar Secret**:
```bash
gcloud secrets create aws-credentials \
  --data-file=aws-credentials.json \
  --replication-policy=automatic
```

---

### 3. IAM Roles (MAIS SEGURO) ⭐

**Recomendado para**: EC2, ECS, Lambda.

**Vantagens**:
- ✅ Sem credenciais no código ou variáveis de ambiente
- ✅ Rotação automática
- ✅ Mais seguro (princípio de privilégio mínimo)

**Setup**:

1. Criar IAM Policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
      ]
    }
  ]
}
```

2. Criar IAM Role:
```bash
aws iam create-role \
  --role-name BedrockEnrichmentWorker \
  --assume-role-policy-document file://trust-policy.json

aws iam put-role-policy \
  --role-name BedrockEnrichmentWorker \
  --policy-name BedrockAccess \
  --policy-document file://bedrock-policy.json
```

3. Anexar role à instância EC2/ECS:
```bash
aws ec2 associate-iam-instance-profile \
  --instance-id i-xxx \
  --iam-instance-profile Name=BedrockEnrichmentWorker
```

4. **Código permanece o mesmo** (boto3 detecta automaticamente):
```python
client = BedrockLLMClient()  # Sem credenciais!
```

---

### 4. AWS Secrets Manager

**Recomendado para**: Rotação automática, multi-ambiente.

**Setup**:
```bash
# Criar secret
aws secretsmanager create-secret \
  --name bedrock-credentials \
  --description "AWS credentials for Bedrock" \
  --secret-string '{"access_key_id":"AKIA...","secret_access_key":"..."}'
```

**Uso no código**:
```python
import boto3
import json

def get_bedrock_credentials():
    """Busca credenciais do Secrets Manager."""
    secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
    response = secrets_client.get_secret_value(SecretId='bedrock-credentials')
    credentials = json.loads(response['SecretString'])
    return credentials

# Usar credenciais
creds = get_bedrock_credentials()
client = BedrockLLMClient(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    region="us-east-1",
    aws_access_key_id=creds['access_key_id'],
    aws_secret_access_key=creds['secret_access_key']
)
```

---

### 5. Airflow Connection URI

**Para integração com Airflow**.

**Formato**:
```
aws://ACCESS_KEY:SECRET_KEY@/?region_name=REGION
```

**Parser automático no worker**:
```python
# Em worker/handler.py (linhas 37-61)
def parse_aws_connection_uri(uri: str) -> Dict[str, str]:
    """
    Parseia connection URI do Airflow.
    
    Exemplo:
        uri = "aws://AKIA...:SECRET@/?region_name=us-east-1"
        → {"access_key_id": "AKIA...", "secret_access_key": "SECRET", "region": "us-east-1"}
    """
    from urllib.parse import urlparse, parse_qs
    
    parsed = urlparse(uri)
    query = parse_qs(parsed.query)
    
    return {
        "access_key_id": parsed.username,
        "secret_access_key": parsed.password,
        "region": query.get('region_name', ['us-east-1'])[0]
    }
```

**Configurar no Airflow**:
```python
# Via Airflow UI ou CLI
airflow connections add aws_bedrock \
  --conn-type aws \
  --conn-login AKIA... \
  --conn-password SECRET \
  --conn-extra '{"region_name": "us-east-1"}'
```

---

## 🔍 Ordem de Precedência

O boto3 busca credenciais nesta ordem:

1. **Parâmetros explícitos** (`aws_access_key_id`, `aws_secret_access_key`)
2. **Variáveis de ambiente** (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
3. **Arquivo local** (`~/.aws/credentials`)
4. **IAM role** (se rodando em EC2/ECS/Lambda)
5. **Container credentials** (ECS task role)
6. **Instance metadata** (EC2 instance profile)

Isso garante flexibilidade sem alteração de código.

---

## ✅ Validação e Testes

### Verificar Credenciais Ativas

```bash
# Verificar identidade
aws sts get-caller-identity

# Esperado:
# {
#     "UserId": "AIDAI...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/enrichment-worker"
# }
```

### Verificar Acesso ao Bedrock

```bash
# Listar modelos disponíveis
aws bedrock list-foundation-models --region us-east-1 | grep claude

# Esperado:
# "modelId": "anthropic.claude-3-haiku-20240307-v1:0"
# "modelId": "anthropic.claude-3-sonnet-20240229-v1:0"
# "modelId": "anthropic.claude-3-opus-20240229-v1:0"
```

### Testar Cliente Python

```python
from news_enrichment import BedrockLLMClient

try:
    client = BedrockLLMClient()
    print("✅ Cliente Bedrock inicializado com sucesso")
    print(f"Região: {client.region}")
    print(f"Modelo: {client.model_id}")
except Exception as e:
    print(f"❌ Erro: {e}")
```

---

## 🚨 Troubleshooting

### Erro: "Unable to locate credentials"

**Causa**: Nenhuma credencial configurada.

**Solução**:
```bash
# 1. Verificar variáveis de ambiente
echo $AWS_ACCESS_KEY_ID

# 2. Verificar arquivo
cat ~/.aws/credentials

# 3. Configurar
aws configure
```

---

### Erro: "AccessDeniedException"

**Causa**: Credenciais sem permissão para Bedrock.

**Solução**:
```bash
# Verificar permissões do usuário
aws iam get-user-policy --user-name enrichment-worker --policy-name BedrockAccess

# Adicionar política manualmente
aws iam put-user-policy \
  --user-name enrichment-worker \
  --policy-name BedrockAccess \
  --policy-document file://bedrock-policy.json
```

---

### Erro: "InvalidSignatureException"

**Causa**: Secret key incorreta ou expirada.

**Solução**:
```bash
# Rotacionar credenciais
aws iam create-access-key --user-name enrichment-worker

# Atualizar .env ou secret
export AWS_ACCESS_KEY_ID="nova-key"
export AWS_SECRET_ACCESS_KEY="nova-secret"

# Deletar credencial antiga (após validação)
aws iam delete-access-key --user-name enrichment-worker --access-key-id AKIA_OLD
```

---

## 🔄 Rotação de Credenciais

### Rotação Manual (Recomendado: 90 dias)

```bash
# 1. Criar nova access key
aws iam create-access-key --user-name enrichment-worker > new-key.json

# 2. Atualizar secrets
gcloud secrets versions add aws-credentials --data-file=new-key.json

# 3. Deploy nova versão do worker
gcloud run deploy enrichment-worker --update-secrets=AWS_ACCESS_KEY_ID=aws-credentials:latest

# 4. Validar que funciona
curl https://enrichment-worker-xxx.a.run.app/health

# 5. Deletar credencial antiga
aws iam delete-access-key --user-name enrichment-worker --access-key-id AKIA_OLD
```

### Rotação Automática (AWS Secrets Manager)

```bash
# Configurar rotação automática (90 dias)
aws secretsmanager rotate-secret \
  --secret-id bedrock-credentials \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789012:function:SecretsManagerRotation \
  --rotation-rules AutomaticallyAfterDays=90
```

---

## 📊 Monitoramento

### CloudTrail Events

Monitore chamadas à API Bedrock:

```bash
# Ver invocações recentes
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::Bedrock::Model \
  --max-results 10
```

### CloudWatch Metrics

```bash
# Monitorar throttling
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name ThrottledRequests \
  --dimensions Name=ModelId,Value=anthropic.claude-3-haiku-20240307-v1:0 \
  --start-time 2026-05-05T00:00:00Z \
  --end-time 2026-05-05T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

### Alertas Recomendados

| Métrica | Threshold | Ação |
|---------|-----------|------|
| `InvalidSignature` errors | > 1 | Verificar credenciais |
| `AccessDenied` errors | > 1 | Verificar permissões |
| `ThrottledRequests` | > 10/hour | Reduzir paralelização |
| `UnauthorizedAccess` attempts | > 0 | Investigar segurança |

---

## 📝 Checklist de Segurança

- [ ] Credenciais NUNCA commitadas no Git
- [ ] `.env` no `.gitignore`
- [ ] Secrets armazenados em GCP Secret Manager ou AWS Secrets Manager
- [ ] IAM policy com princípio de privilégio mínimo
- [ ] Rotação de credenciais configurada (90 dias)
- [ ] CloudTrail logging habilitado
- [ ] Alertas de segurança configurados
- [ ] Teste de acesso realizado
- [ ] Documentação atualizada

---

## 📚 Referências

### Interna
- [News Enrichment Worker](../modulos/news-enrichment-worker.md)
- [Onboarding Enriquecimento LLM](../onboarding/ds/enriquecimento-llm.md)
- [Workers Pub/Sub](../onboarding/ds/workers-pubsub.md)

### Externa
- [AWS Bedrock Security](https://docs.aws.amazon.com/bedrock/latest/userguide/security.html)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [boto3 Credentials](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html)

---

**Última atualização**: 05/05/2026  
**Responsável**: Equipe DevSecOps - DestaquesGovbr  
**Revisão**: Trimestral