# Streamlit Cloud

O dashboard pode rodar no Streamlit Community Cloud sem a FastAPI local. Quando `COMMERCEPULSE_API_URL` nao responde, o app usa `dashboard/sample_data.json`, um snapshot agregado dos dados finais do projeto.

## Configuracao

- Repository: `Wwerneck/commercepulse-brasil`
- Branch: `main`
- Main file path: `streamlit_app.py`
- Python version: `3.11`
- Secrets: nenhum obrigatorio para o modo demonstracao.

## Modo Completo

Para usar a API em vez do snapshot, configure `COMMERCEPULSE_API_URL` nos secrets do Streamlit Cloud apontando para uma FastAPI publicada separadamente.
