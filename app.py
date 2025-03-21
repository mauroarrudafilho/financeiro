import streamlit as st
import pandas as pd

# Definir a configuração da página (DEVE SER A PRIMEIRA LINHA Streamlit)
st.set_page_config(layout="wide", page_title="Relatório de Recuperação de Recursos")

# Carregar os dados
file_path = "Analise de Recuperação - Financeira.xlsx"
df = pd.read_excel(file_path, sheet_name="Base Geral")

# Ajustar os tipos de dados
df["Dt. Entrega"] = pd.to_datetime(df["Dt. Entrega"], errors="coerce")
df["Dt Venc"] = pd.to_datetime(df["Dt Venc"], errors="coerce")
df["Vlr Devolução"] = pd.to_numeric(df["Vlr Devolução"], errors="coerce")
df["Vlr Título"] = pd.to_numeric(df["Vlr Título"], errors="coerce")

# Criar score de recuperação diretamente
df["Score Recuperação"] = (
    (df["Outras parc. pagas"] == "Sim").astype(int) * 3 +
    (df["Teve Devolução?"] == "Não").astype(int) * 2 +
    (df["Vlr Devolução"] == 0).astype(int) * 1 +
    ((pd.Timestamp.today() - df["Dt. Entrega"]).dt.days < 90).astype(int) * 2 +
    ((df["Teve Devolução?"] == "Sim") & (df["Vlr Devolução"] < df["Vlr Título"])).astype(int) * 3
)

# Criar coluna de tempo da dívida (dias desde o vencimento)
df["Tempo da Dívida"] = (pd.Timestamp.today() - df["Dt Venc"]).dt.days

# Remover valores não vencidos (onde Tempo da Dívida é negativo)
df = df[df["Tempo da Dívida"] >= 0]

# Criar faixas de tempo da dívida
def categorize_debt_days(days):
    if days <= 15:
        return "1 - 15 dias"
    elif days <= 45:
        return "15 - 45 dias"
    elif days <= 90:
        return "46 - 90 dias"
    else:
        return "Acima de 91 dias"

df["Faixa de Dívida"] = df["Tempo da Dívida"].apply(categorize_debt_days)

# Aplicação dos filtros
df_filtered = df.copy()
responsavel = st.sidebar.multiselect("Filtrar por Responsável", df["Responsável"].unique())
banco = st.sidebar.multiselect("Filtrar por Banco", df["Banco"].unique())
score = st.sidebar.slider("Filtrar por Score de Recuperação", int(df["Score Recuperação"].min()), int(df["Score Recuperação"].max()), (int(df["Score Recuperação"].min()), int(df["Score Recuperação"].max())))
min_dias, max_dias = int(df["Tempo da Dívida"].min()), int(df["Tempo da Dívida"].max())
intervalo_tempo = st.sidebar.slider("Filtrar por Tempo da Dívida (dias)", min_dias, max_dias, (min_dias, max_dias))

if responsavel:
    df_filtered = df_filtered[df_filtered["Responsável"].isin(responsavel)]
if banco:
    df_filtered = df_filtered[df_filtered["Banco"].isin(banco)]
df_filtered = df_filtered[(df_filtered["Score Recuperação"] >= score[0]) & (df_filtered["Score Recuperação"] <= score[1])]
df_filtered = df_filtered[(df_filtered["Tempo da Dívida"] >= intervalo_tempo[0]) & (df_filtered["Tempo da Dívida"] <= intervalo_tempo[1])]

# Criar resumo por cliente baseado nos filtros
df_clientes = df_filtered.groupby("Cliente").agg({
    "Vlr Título": ["sum", "mean"],
    "NFe": "count",
    "Tempo da Dívida": "mean",
    "Score Recuperação": "mean",
    "Banco": lambda x: x.value_counts().idxmax(),
    "Teve Devolução?": lambda x: "Sim" if "Sim" in x.values else "Não"
}).reset_index()

df_clientes.columns = ["Cliente", "Soma Total de Valores em Aberto", "Valor Médio por Título", "Qtd. Títulos em Aberto", "Média de Atraso (dias)", "Score Médio de Recuperação", "Banco", "Teve Devolução?"]

# Exibir métricas principais
st.title("📊 Relatório de Recuperação de Recursos")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Clientes", df_filtered["Cliente"].nunique())
valor_total_pendente = df_filtered["Vlr Título"].sum()
col2.metric("Valor Total Pendente", f"R$ {valor_total_pendente:,.2f}")
col3.metric("Média de Score", round(df_filtered["Score Recuperação"].mean(), 2))
col4.metric("Média do Tempo da Dívida (dias)", round(df_filtered["Tempo da Dívida"].mean(), 2))

# Gráficos
st.subheader("📊 Distribuição do Score de Recuperação")
st.bar_chart(df_filtered["Score Recuperação"].value_counts().sort_index())

st.subheader("🏦 Valor Total Pendente por Banco")
bank_summary = df_filtered.groupby("Banco")["Vlr Título"].sum().sort_values(ascending=False)
st.bar_chart(bank_summary)

st.subheader("🕒 Distribuição por Faixa de Dívida")
st.bar_chart(df_filtered["Faixa de Dívida"].value_counts())

# Exibir tabelas baseadas nos filtros
st.subheader("📌 Valores Pendentes por Cliente")
st.dataframe(df_clientes)
st.subheader("📌 Dados Detalhados")
st.dataframe(df_filtered)

# Opção de Download dos Dados
st.sidebar.subheader("📥 Baixar Dados Filtrados")
st.sidebar.download_button("Baixar CSV", df_filtered.to_csv(index=False), file_name="relatorio_recuperacao.csv", mime="text/csv")

st.sidebar.info("Use os filtros para segmentar os dados e analisar melhor a recuperação de recursos.")
