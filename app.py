import streamlit as st
import pandas as pd

# Definir a configuração da página (DEVE SER A PRIMEIRA LINHA Streamlit)
st.set_page_config(layout="wide", page_title="Relatório de Recuperação de Recursos")

# Carregar os dados
file_path_vencimentos = "Analise de Recuperação - Financeira.xlsx"
df = pd.read_excel(file_path_vencimentos, sheet_name="Base Geral")

file_path_historico = "Movimentacao Financeira_Arruda.xlsx"
df_historico = pd.read_excel(file_path_historico, sheet_name=0)

# Ajustar os tipos de dados
df["Dt. Entrega"] = pd.to_datetime(df["Dt. Entrega"], errors="coerce")
df["Dt Venc"] = pd.to_datetime(df["Dt Venc"], errors="coerce")
df["Vlr Devolução"] = pd.to_numeric(df["Vlr Devolução"], errors="coerce")
df["Vlr Título"] = pd.to_numeric(df["Vlr Título"], errors="coerce")

# Ajustar datas no histórico de pagamentos
df_historico["Dt. Vencimento"] = pd.to_datetime(df_historico["Dt. Vencimento"], errors="coerce")
df_historico["Dt. Baixa"] = pd.to_datetime(df_historico["Dt. Baixa"], errors="coerce")

# Criar categorias de comportamento de pagamento
def classificar_cliente(row):
    if pd.isna(row["Dt. Baixa"]):
        return "🔴 Inadimplente"
    elif row["Dt. Baixa"] < row["Dt. Vencimento"]:
        return "🔵 Adimplente (Antecipado)"
    elif row["Dt. Baixa"] == row["Dt. Vencimento"]:
        return "🟢 Adimplente (No Dia)"
    elif (row["Dt. Baixa"] - row["Dt. Vencimento"]).days <= 15:
        return "🟡 Intermediário (Atraso Eventual)"
    else:
        return "🟠 Atrasado Crônico"

# Aplicar a categorização
df_historico["Categoria Cliente"] = df_historico.apply(classificar_cliente, axis=1)

# Adicionar Código do Parceiro ao Resumo
df_resumo_clientes = df_historico.groupby(["Cód. Parceiro", "Parceiro"])["Categoria Cliente"].value_counts().unstack().fillna(0).reset_index()

# Verificar se as colunas existem antes de usar
if "Parceiro" not in df_resumo_clientes.columns:
    df_resumo_clientes["Parceiro"] = "Desconhecido"

# Integrar a categoria ao Score de Recuperação
def ajustar_score(row):
    if row["Parceiro"] in df_resumo_clientes["Parceiro"].values:
        categoria = df_resumo_clientes.loc[df_resumo_clientes["Parceiro"] == row["Parceiro"], :].drop(columns=["Cód. Parceiro", "Parceiro"], errors='ignore').idxmax(axis=1).values[0]
    else:
        categoria = "Desconhecido"
    
    if categoria == "🔵 Adimplente (Antecipado)" or categoria == "🟢 Adimplente (No Dia)":
        return row["Score Recuperação"] + 3
    elif categoria == "🟡 Intermediário (Atraso Eventual)":
        return row["Score Recuperação"] + 1
    elif categoria == "🟠 Atrasado Crônico":
        return row["Score Recuperação"] - 2
    elif categoria == "🔴 Inadimplente":
        return row["Score Recuperação"] - 5
    else:
        return row["Score Recuperação"]

# Aplicar ajuste no Score de Recuperação
df["Score Recuperação"] = df.apply(ajustar_score, axis=1)

# Exibir gráficos baseados no histórico de pagamento
st.subheader("📊 Distribuição das Categorias de Pagamento dos Clientes")
st.bar_chart(df_historico["Categoria Cliente"].value_counts())

# Exibir resumo das categorias de clientes
st.subheader("📌 Resumo do Comportamento de Pagamento por Cliente")
st.dataframe(df_resumo_clientes)

# Atualizar métricas principais considerando o novo Score de Recuperação
st.title("📊 Relatório de Recuperação de Recursos")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Clientes", df["Parceiro"].nunique())
valor_total_pendente = df["Vlr Título"].sum()
col2.metric("Valor Total Pendente", f"R$ {valor_total_pendente:,.2f}")
col3.metric("Média de Score", round(df["Score Recuperação"].mean(), 2))
col4.metric("Média do Tempo da Dívida (dias)", round(df["Tempo da Dívida"].mean(), 2))

# Exibir dados detalhados
st.subheader("📌 Dados Detalhados")
st.dataframe(df)

# Opção de Download dos Dados
st.sidebar.subheader("📥 Baixar Dados Filtrados")
st.sidebar.download_button("Baixar CSV", df.to_csv(index=False), file_name="relatorio_recuperacao.csv", mime="text/csv")

st.sidebar.info("Agora a recuperação de recursos leva em conta o histórico de pagamento dos clientes para uma análise mais precisa!")
