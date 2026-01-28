# Configuração Claude Code + VSCode via AWS Bedrock

## Passo 1: Instalar o AWS CLI

Caso ainda não tenha o AWS CLI instalado, siga as instruções no link oficial:

<https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>

Para verificar se está instalado, execute:

```bash
aws --version
```

Você deve ter o **AWS CLI v2** para usar o método SSO recomendado.

---

## Passo 2: Configuração de Credenciais AWS

Existem duas formas de configurar as credenciais AWS. Recomendamos o **Método 1 (SSO)** por ser mais prático e seguro.

### Método 1: AWS SSO (Recomendado) ✅

Este método é mais conveniente pois as credenciais são renovadas automaticamente e não expiram a cada poucas horas.

#### 2.1.1 Configurar AWS SSO

Execute o comando abaixo no terminal:

```bash
aws configure sso
```

O comando fará várias perguntas. Responda conforme abaixo:

**1. SSO session name (Recommended):**
```
cpqd
```

**2. SSO start URL:**
```
https://aws-inspire.awsapps.com/start/#
```

**3. SSO region:**
```
sa-east-1
```

**4. SSO registration scopes:**
- Apenas aperte **Enter** (deixe o padrão)

#### 2.1.2 Fazer Login via Navegador

Após responder as perguntas acima, o AWS CLI irá:
1. Abrir automaticamente uma página no navegador
2. Solicitar que você faça login com sua conta CPQD
3. Pedir autorização para o AWS CLI acessar sua conta

Após autorizar, volte para o terminal e continue respondendo:

**5. There are X AWS accounts available to you:**
- Selecione a conta desejada (provavelmente `aws_inspire_m7`)

**6. There are X roles available to you:**
- Selecione a role apropriada (ex: `dev`)

**7. CLI default client Region:**
```
sa-east-1
```

**8. CLI default output format:**
```
json
```

**9. CLI profile name:**
```
cpqd-sso
```

#### 2.1.3 Verificar a Configuração

Para verificar se a configuração foi bem-sucedida, execute:

```bash
aws sts get-caller-identity --profile cpqd-sso
```

Se retornar suas informações de usuário, está tudo configurado! ✅

#### 2.1.4 Renovar Credenciais (Quando Expirarem)

Quando as credenciais expirarem, basta executar:

```bash
aws sso login --profile cpqd-sso
```

O navegador abrirá novamente para você fazer login e as credenciais serão renovadas automaticamente.

---

### Método 2: Credenciais Temporárias Manuais (Alternativo)

⚠️ **Aviso:** Este método requer renovação manual das credenciais a cada poucas horas. Recomendamos usar o Método 1 (SSO).

#### 2.2.1 Obter as Credenciais

1. Acesse o portal <https://aws-inspire.awsapps.com/start>
2. Faça login com sua conta CPQD
3. Clique no ícone de **setinha apontada para a direita** (→) antes do cubo amarelo escrito **"aws_inspire_m7"**
4. Uma aba será aberta com 2 links
5. Clique em **"Chaves de acesso"**
6. As credenciais necessárias serão exibidas

#### 2.2.2 Exportar as Variáveis de Ambiente

Execute os seguintes comandos no terminal, substituindo os valores pelos obtidos no passo anterior:

```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_SESSION_TOKEN="your-session-token"
```

**Importante:** Substitua os valores entre aspas pelas suas credenciais reais.

#### 2.2.3 Configurar o AWS CLI

Execute o comando:

```bash
aws configure
```

O comando solicitará as seguintes informações:

- **AWS Access Key ID**: cole a chave de acesso obtida anteriormente
- **AWS Secret Access Key**: cole a chave secreta obtida anteriormente
- **Default region name**: `sa-east-1`
- **Default output format**: `json`

#### 2.2.4 Verificar a Configuração

Para verificar se a configuração foi bem-sucedida, execute:

```bash
aws sts get-caller-identity
```

⚠️ **Lembre-se:** Essas credenciais expiram em poucas horas. Você precisará repetir este processo sempre que expirarem.

---

## Passo 3: Testar o Claude Code no Terminal

Com as credenciais configuradas, você já pode testar o Claude Code via terminal.

### 3.1 Instalar o Claude Code (se necessário)

Caso ainda não tenha o Claude Code instalado, siga as instruções no link:

- <https://code.claude.com/docs/en/overview>

### 3.2 Configurar Variáveis de Ambiente para o Terminal

⚠️ **Importante:** Antes de executar o Claude Code pela primeira vez no terminal, você **DEVE** configurar as variáveis de ambiente. Caso contrário, o Claude Code tentará fazer login no Claude.ai, o que não funcionará com AWS Bedrock.

#### Opção A: Exportar Variáveis Temporariamente (para a sessão atual)

Se você usou o **Método 1 (SSO)**, execute:

```bash
export AWS_PROFILE=cpqd-sso
export AWS_REGION=sa-east-1
export CLAUDE_CODE_USE_BEDROCK=1
```

Se você usou o **Método 2 (Manual)**, execute:

```bash
export AWS_PROFILE=default
export AWS_REGION=sa-east-1
export CLAUDE_CODE_USE_BEDROCK=1
```

**Desvantagem:** Você precisará executar esses comandos toda vez que abrir um novo terminal.

#### Opção B: Configurar Permanentemente (Recomendado)

Para não precisar exportar as variáveis toda vez, adicione-as ao arquivo de configuração do seu shell.

**Para Bash** (edite o arquivo `~/.bashrc`):

```bash
echo 'export AWS_PROFILE=cpqd-sso' >> ~/.bashrc
echo 'export AWS_REGION=sa-east-1' >> ~/.bashrc
echo 'export CLAUDE_CODE_USE_BEDROCK=1' >> ~/.bashrc
source ~/.bashrc
```

**Para Zsh** (edite o arquivo `~/.zshrc`):

```bash
echo 'export AWS_PROFILE=cpqd-sso' >> ~/.zshrc
echo 'export AWS_REGION=sa-east-1' >> ~/.zshrc
echo 'export CLAUDE_CODE_USE_BEDROCK=1' >> ~/.zshrc
source ~/.zshrc
```

**Nota:** Se você usou o **Método 2 (Manual)**, substitua `cpqd-sso` por `default` nos comandos acima.

### 3.3 Executar o Claude Code

Após configurar as variáveis de ambiente, execute no terminal:

```bash
claude
```

Se tudo estiver configurado corretamente, o Claude Code será iniciado e estará pronto para uso **sem pedir login**.

---

## Passo 4: Integração com VS Code

### 4.1 Instalar a Extensão

1. Abra o VS Code
2. Acesse a aba de **Extensões** (ícone no menu lateral ou `Ctrl+Shift+X`)
3. Pesquise por **"Claude Code for VS Code"**
4. Clique em **Install** para instalar a extensão

### 4.2 Configurar a Extensão

1. Abra as **Configurações** do VS Code (`Ctrl+,`)
2. Pesquise por **"Claude Code: Environment Variables"**
3. Localize a opção que menciona variáveis de ambiente
4. Clique em **"Edit in settings.json"**

### 4.3 Adicionar as Configurações

Cole as seguintes configurações no arquivo `settings.json`:

#### Se você usou o Método 1 (SSO) - Recomendado:

```json
{
    "claudeCode.selectedModel": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "claudeCode.environmentVariables": [
        {
            "name": "AWS_PROFILE",
            "value": "cpqd-sso"
        },
        {
            "name": "AWS_REGION",
            "value": "sa-east-1"
        },
        {
            "name": "CLAUDE_CODE_USE_BEDROCK",
            "value": "1"
        }
    ],
    "claudeCode.disableLoginPrompt": true,
    "claudeCode.preferredLocation": "panel"
}
```

#### Se você usou o Método 2 (Manual):

```json
{
    "claudeCode.selectedModel": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "claudeCode.environmentVariables": [
        {
            "name": "AWS_PROFILE",
            "value": "default"
        },
        {
            "name": "AWS_REGION",
            "value": "sa-east-1"
        },
        {
            "name": "CLAUDE_CODE_USE_BEDROCK",
            "value": "1"
        }
    ],
    "claudeCode.disableLoginPrompt": true,
    "claudeCode.preferredLocation": "panel"
}
```

**Dica:** Para verificar o nome do seu perfil AWS CLI, execute no terminal:

```bash
aws configure list-profiles
```

### 4.4 Modelos Disponíveis

Você pode alterar o modelo conforme sua necessidade:

| Modelo | ID |
|--------|-----|
| Claude Sonnet 4.5 | `global.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| Claude Haiku 4.5 | `global.anthropic.claude-haiku-4-5-20251001-v1:0` |
| Claude Opus 4.5 | `global.anthropic.claude-opus-4-5-20251101-v1:0` |

### 4.5 Reiniciar o VS Code

Após salvar as configurações, reinicie o VS Code ou recarregue a janela:

- Pressione `Ctrl+Shift+P`
- Digite **"Developer: Reload Window"**
- Pressione Enter

---

## Pronto!

O Claude Code está configurado e integrado ao VS Code via AWS Bedrock. Para iniciar uma conversa, clique no ícone do Claude Code na barra lateral do VS Code.

### Dicas Importantes:

- **Se você usou o Método 1 (SSO):** Quando as credenciais expirarem, execute `aws sso login --profile cpqd-sso` no terminal
- **Se você usou o Método 2 (Manual):** Você precisará obter novas credenciais no portal AWS e exportá-las novamente toda vez que expirarem
- Recomendo usar o Método 1 (SSO) para maior praticidade e segurança

---

## Troubleshooting

### Problema: Claude Code funciona no VS Code mas não no terminal

**Sintoma:** O Claude Code funciona normalmente na extensão do VS Code, mas ao executar `claude` no terminal retorna erro de credenciais expiradas ou inválidas.

**Causa:** Se você testou tanto o Método 1 (SSO) quanto o Método 2 (Credenciais Manuais), pode haver variáveis de ambiente conflitantes no seu `~/.bashrc` ou `~/.zshrc`. As variáveis `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY` têm **precedência** sobre `AWS_PROFILE`, então mesmo com o perfil SSO configurado, o AWS CLI usará as credenciais hardcoded (que podem estar expiradas).

**Solução:**

1. Abra o arquivo de configuração do seu shell:

```bash
# Para Bash
nano ~/.bashrc

# Para Zsh
nano ~/.zshrc
```

2. Procure e **remova** as seguintes linhas (se existirem):

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
```

3. Certifique-se de que apenas as variáveis do SSO estejam configuradas:

```bash
# AWS Bedrock configuration for Claude Code (usando SSO)
export AWS_PROFILE="cpqd-sso"
export AWS_REGION="sa-east-1"
export CLAUDE_CODE_USE_BEDROCK=1
```

4. Recarregue o arquivo de configuração:

```bash
source ~/.bashrc  # ou source ~/.zshrc
```

5. Limpe as variáveis antigas da sessão atual (se não abrir novo terminal):

```bash
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
```

6. Teste novamente:

```bash
claude
```

---

### Problema: Erro "The provided model identifier is invalid"

**Sintoma:** Ao executar o Claude Code no terminal, aparece o erro:

```
API Error (us.anthropic.claude-sonnet-4-5-20250929-v1:0): 400 The provided model identifier is invalid.
```

**Causa:** O Claude Code está tentando usar um modelo com prefixo `us.` ao invés de `global.`. Isso acontece quando o modelo não está explicitamente configurado para o terminal.

**Solução:**

1. Adicione a variável `ANTHROPIC_MODEL` ao seu arquivo de configuração do shell:

```bash
# Para Bash
echo 'export ANTHROPIC_MODEL="global.anthropic.claude-sonnet-4-5-20250929-v1:0"' >> ~/.bashrc
source ~/.bashrc

# Para Zsh
echo 'export ANTHROPIC_MODEL="global.anthropic.claude-sonnet-4-5-20250929-v1:0"' >> ~/.zshrc
source ~/.zshrc
```

2. Ou edite manualmente o arquivo e adicione a linha junto com as outras variáveis AWS:

```bash
# AWS Bedrock configuration for Claude Code (usando SSO)
export AWS_PROFILE="cpqd-sso"
export AWS_REGION="sa-east-1"
export CLAUDE_CODE_USE_BEDROCK=1
export ANTHROPIC_MODEL="global.anthropic.claude-sonnet-4-5-20250929-v1:0"
```

3. Teste novamente:

```bash
claude
```

**Modelos disponíveis:**

| Modelo | Variável ANTHROPIC_MODEL |
|--------|--------------------------|
| Claude Sonnet 4.5 | `global.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| Claude Haiku 4.5 | `global.anthropic.claude-haiku-4-5-20251001-v1:0` |
| Claude Opus 4.5 | `global.anthropic.claude-opus-4-5-20251101-v1:0` |