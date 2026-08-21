# Guia Operacional — IA_Motos

Guia prático para operar o sistema no dia a dia. Baseado no comportamento real do [`../launcher_gui.py`](../launcher_gui.py), do [`../control_center.py`](../control_center.py) e dos scripts operacionais atuais.

## Como iniciar o sistema

1. Execute o Launcher (`launcher_gui.py`).
2. No Launcher, clique em **Iniciar Robô** para começar a coleta (OLX + Mercado Livre) em segundo plano.
3. Clique em **Abrir Control Center** para acompanhar missões, oportunidades e o histórico de decisões.

## Como parar

- No Launcher, clique em **Parar Robô**. O botão só encerra o processo depois de confirmar, pela linha de comando real do processo, que ele pertence de fato ao robô do IA_Motos — nunca encerra um PID não confirmado.
- Fechar a janela do Launcher **não** para o robô nem a sincronização AWS automaticamente; eles continuam rodando em segundo plano até serem parados explicitamente pelos botões correspondentes.

## Como verificar status

- **Robô**: botão **Status Robô** no Launcher, ou a tela "Robô" do Control Center.
- **Sincronização AWS**: o Launcher mantém um indicador de status na própria janela, atualizado automaticamente a cada 15 segundos.

## Como iniciar/parar o Sync AWS

- Botões **Iniciar Sync** / **Parar Sync** no Launcher. O mecanismo (`core/aws_sync_process.py`) identifica o processo de sincronização pela linha de comando do PowerShell em execução — nunca por suposição — antes de considerá-lo ativo ou de encerrá-lo.
- **Verificar AWS agora**: botão de checagem manual e pontual via SSH, que não repete automaticamente.

## Como abrir o Control Center

Botão **Abrir Control Center** no Launcher. As telas disponíveis no menu lateral são: Dashboard, Robô, Painel AWS, AWS SSH, VS Code, Agente IA (missões), Memória da IA (histórico de decisões), Agent Analytics, Calibração Financeira (observabilidade do shadow mode financeiro) e Configurações.

## Como abrir o painel AWS

Botão **Abrir Painel** no Launcher (ou item "Painel AWS" no Control Center) — abre o painel web (`interface_v2`) hospedado na instância AWS no navegador padrão.

## Como verificar a AWS manualmente

Botão **AWS SSH** / **Conectar AWS** no Launcher abre uma sessão SSH direta para a instância configurada, usando a chave privada configurada localmente. A checagem manual de status (sem abrir sessão interativa) fica disponível pelo botão dedicado descrito acima.

## Cuidados com perfis locais

O sistema usa perfis de navegador Playwright/Chrome persistentes para manter sessões de login (`ml_profile_stealth/`, `chrome_profile/`, entre outros conforme o script). Esses diretórios:

- **nunca devem ser versionados no Git** (já protegidos pelo `.gitignore`);
- contêm cookies e dados de sessão reais — não devem ser copiados entre máquinas nem compartilhados;
- podem exigir novo login manual se a sessão expirar (ver scripts em `scripts/manual/`).

## Webmotors e CAPTCHA

O Webmotors usa proteção PerimeterX contra automação. O script oficial para essa fonte é `teste_webmotors_motos.py` (depende de `teste_webmotors_stealth.py`), documentado em detalhe em [`../GUIA_BLOQUEIO.txt`](../GUIA_BLOQUEIO.txt). Resumo das opções lá descritas:

1. **Resolução manual** — rodar o script, resolver o CAPTCHA manualmente quando aparecer.
2. **Proxy** — configurar uma URL de proxy própria via variável de ambiente, para reduzir a chance de bloqueio.
3. **Sessão persistente** — o perfil de navegador local reduz a frequência de novos CAPTCHAs após o primeiro login.

Este script envia notificações reais ao Telegram e deve ser executado deliberadamente, nunca por engano.

## Scripts manuais (`scripts/manual/`)

Ferramentas de apoio que não fazem parte do pipeline automático do robô, usadas para diagnóstico e manutenção pontual:

- **`preview_mercado_livre.py`** — executa a integração real do Mercado Livre isoladamente e grava o resultado em um JSON de preview, sem afetar o histórico principal. Útil para conferir a integração sem rodar o robô inteiro.
- **`mercado_livre_login_manual.py`** — abre um navegador persistente no perfil usado pelo scraper do Mercado Livre, para renovar o login manualmente quando a sessão expirar.

Ambos exigem execução manual e deliberada; nenhum é chamado automaticamente pelo robô.

## Segurança e variáveis de ambiente

As credenciais (token do Telegram, IDs de destinatário) ficam exclusivamente em `.env`, nunca no código. Veja [`../.env.example`](../.env.example) para a lista de variáveis esperadas — o arquivo real nunca deve ser commitado (já protegido pelo `.gitignore`).
