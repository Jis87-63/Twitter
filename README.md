# X Panel (Termux)

Painel local, em português, para **organizar contas X que você já possui e está autorizado a administrar**. Ele guarda apenas metadados de inventário no SQLite local: handle, nome, estado, responsável e notas.

> Não cria contas, não contorna controles da plataforma, não automatiza login e não armazena senhas, cookies ou tokens. Use a API oficial do X e as permissões adequadas caso futuramente conecte dados da plataforma. O uso continua sujeito aos [Termos do X](https://x.com/tos) e às regras aplicáveis.

## Instalação no Termux

```sh
pkg update && pkg install python -y
git clone <URL_DO_SEU_REPOSITORIO> xpanel
cd xpanel
python xpanel.py --help
```

Não há dependências externas: Python 3 e SQLite (incluído no Python) bastam.

## Painel web para Vercel

O diretório `public/` é um painel estático responsivo que pode ser hospedado na Vercel. Ele não expõe o banco do Termux: seus registros de demonstração ficam somente no `localStorage` do navegador e podem ser exportados em JSON.

```sh
npm install
npx vercel --prod
```

`vercel.json` serve o painel sem configuração extra. Use `npm run dev` para vê-lo localmente. O ambiente hospedado não executa shell: os comandos abaixo devem ser rodados localmente no Termux.

O painel também oferece **Web Edit**, uma área para editar e pré-visualizar HTML no próprio navegador, um console seguro de eventos e um visualizador HTTPS em iframe isolado. Não há terminal web, `eval`, acesso ao banco do Termux nem edição de sites de terceiros: isso mantém o deploy Vercel estático e seguro.

## Uso

```sh
# Registre uma conta existente e autorizada
python xpanel.py add minha_conta --name "Marca Exemplo" --owner "Equipe social" --notes "Acesso revisado"

# Mostre o painel e as contas em uso
python xpanel.py dashboard
python xpanel.py list --status ativa

# Consulte dados não sensíveis e atualize o estado local
python xpanel.py show minha_conta
python xpanel.py status minha_conta pausada

# Gere uma cópia CSV local
python xpanel.py export ~/storage/downloads/xpanel-contas.csv
python xpanel.py audit --limit 20
python xpanel.py doctor
python xpanel.py backup ~/storage/downloads/xpanel-backup.db
```

Os estados são `ativa`, `pausada` e `arquivada`. O banco fica em `~/.xpanel/accounts.db`; para testes ou perfis separados, informe `--db /caminho/contas.db` antes do comando.

## Privacidade e operação responsável

* Não coloque segredos nas notas. O painel foi deliberadamente projetado para não receber credenciais.
* Proteja o telefone e o arquivo `~/.xpanel/accounts.db`, pois a lista de contas e responsáveis é informação operacional.
* O histórico local registra inclusões e mudanças de estado para auditoria simples.
* Não use esta ferramenta para criar contas em massa, evasão de banimento, coleta de credenciais ou ações não autorizadas.

## Verificação

```sh
python -m unittest -v
```
