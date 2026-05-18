# 🏍️ Sistema de Prospecção de Motos - IA_Motos

## 🔒 Segurança - Credenciais

As credenciais do Telegram agora estão protegidas no arquivo `.env` (NÃO COMPARTILHE!).

### 📝 Arquivo `.env`

```
TOKEN_TELEGRAM=seu_token_aqui
ID_DAVISON=seu_id_aqui
```

### ⚠️ IMPORTANTE

- **NUNCA commit o arquivo `.env` no Git**
- O `.gitignore` já está configurado para ignorar automaticamente
- Se as credenciais vazarem, regenere o token do bot no Telegram

### 🚀 Como usar

1. **Primeiro teste** - Verificar se as credenciais estão corretas:
   ```powershell
   python main.py
   ```

2. **Modo loop** - Sistema de monitoramento contínuo:
   ```powershell
   python main.py
   ```

## 📂 Estrutura de Arquivos

```
IA_Motos/
├── main.py                    # Scraper OLX com alertas Telegram
├── webmotors.py              # Scraper Webmotors (beta)
├── teste_webmotors_seguro.py # Teste seguro Webmotors
├── .env                       # Credenciais (NÃO COMPARTILHE!)
├── .gitignore                # Arquivos a ignorar
├── anuncios_vistos.json      # Memória OLX
└── README.md                  # Este arquivo
```

## 🔧 Melhorias Aplicadas

✅ Credenciais movidas para `.env`  
✅ Validação de credenciais ao iniciar  
✅ Timeout adicionado ao Telegram  
✅ Validação de `href` antes de usar  
✅ `.gitignore` criado para segurança  

## 📞 Contato

Sistema criado para Davison - Monitoramento de motos na OLX
