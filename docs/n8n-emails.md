# Emails da loja via n8n

O site **não envia SMTP em produção** (Railway bloqueia a porta 587).  
Em vez disso, o Django faz `POST` para um **webhook n8n** com o HTML já montado; o n8n envia o email (ex.: nó **Gmail**).

## Variáveis no Railway / `.env`

```env
N8N_WEBHOOK_URL=https://SEU-N8N/webhook/mesa-brasileira-email
N8N_WEBHOOK_SECRET=uma-chave-secreta
N8N_HEADER_USERNAME=o-name-do-header-auth-no-n8n
DEFAULT_FROM_EMAIL=Mesa Brasileira <seu@gmail.com>
CONTATO_EMAIL=contacto@mesabrasileira.pt
SITE_URL=https://mesabrasileira.pt
```

Em **local**, pode omitir `N8N_WEBHOOK_URL` e usar Gmail SMTP no `.env` como até agora.

## Payload JSON (POST)

O Django envia:

```json
{
  "evento": "email_transacional",
  "de": "Mesa Brasileira <email@dominio.pt>",
  "para": ["cliente@exemplo.com"],
  "assunto": "Confirme o seu pedido MB-20260603-XXXX — Mesa Brasileira",
  "texto": "versão texto simples...",
  "html": "<!DOCTYPE html>...",
  "cc": [],
  "bcc": [],
  "reply_to": []
}
```

Header Auth no n8n (nó Webhook):

- **Name** = valor de `N8N_HEADER_USERNAME`
- **Value** = valor de `N8N_WEBHOOK_SECRET`

O Django envia o cabeçalho `{N8N_HEADER_USERNAME}: {N8N_WEBHOOK_SECRET}`.

Autenticação **Basic Auth** no webhook:

```env
N8N_WEBHOOK_BASIC_USER=utilizador
N8N_WEBHOOK_BASIC_PASSWORD=palavra-passe
```

Cabeçalho ou valor diferentes do padrão:

```env
N8N_WEBHOOK_AUTH_HEADER=Authorization
N8N_WEBHOOK_AUTH_VALUE=Bearer o-seu-token
```

## Workflow n8n (exemplo)

1. **Webhook** — método POST, path `mesa-brasileira-email`
2. **IF** (opcional) — `{{ $json.headers['x-webhook-secret'] }}` igual ao secret
3. **Gmail** (ou SMTP) — enviar email:
   - **To:** `{{ $json.body.para[0] }}` (ou loop se vários)
   - **Subject:** `{{ $json.body.assunto }}`
   - **Email Type:** HTML
   - **Message:** `{{ $json.body.html }}`
4. **Respond to Webhook** — `{ "ok": true }`

### Testar o webhook

```bash
python manage.py testar_email seu@email.com
```

Com `N8N_WEBHOOK_URL` definido, o comando dispara o n8n em vez do SMTP.

### Teste manual (curl)

```bash
curl -X POST "$N8N_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: sua-chave" \
  -d '{
    "evento": "email_transacional",
    "de": "Mesa Brasileira <teste@gmail.com>",
    "para": ["destino@exemplo.com"],
    "assunto": "Teste n8n",
    "texto": "Corpo texto",
    "html": "<p>Corpo <strong>HTML</strong></p>"
  }'
```

## Emails que o site dispara

| Momento | Template Django | Assunto (exemplo) |
|---------|-----------------|-------------------|
| Após checkout | `confirmar_pedido` | Confirme o seu pedido MB-… |
| Admin marca pago | `pagamento_confirmado` | Pagamento recebido — pedido MB-… |
| Comando teste | `testar_email` | Teste de email — Mesa Brasileira |

O HTML inclui logo e cores da marca (`home/templates/home/emails/`).

## n8n sem custos

- **Self-hosted** n8n no Railway, VPS ou máquina local (tunnel ngrok para testes)
- Plano cloud gratuito do n8n (limites mensais) só para webhooks leves

O Gmail no n8n usa a **sua conta Google** (OAuth), sem Resend nem API paga.
