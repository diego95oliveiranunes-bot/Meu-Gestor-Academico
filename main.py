import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# 1. CONFIGURAÇÃO (MOBILE FRIENDLY)
st.set_page_config(page_title="Meu Gestor Acadêmico", layout="wide", initial_sidebar_state="expanded")


# 2. FUNÇÕES DE DADOS (COM LIMPEZA DE BUGS)
def load_data():
    try:
        tasks = pd.read_csv('tasks.csv')
        tasks['Prazo'] = pd.to_datetime(tasks['Prazo'], dayfirst=True, errors='coerce')
        if tasks['Status'].dtype == object:
            tasks['Status'] = tasks['Status'].replace(['Pendente', 'Concluído'], [0, 100])
            tasks['Status'] = pd.to_numeric(tasks['Status'], errors='coerce').fillna(0)
    except:
        tasks = pd.DataFrame(columns=['Disciplina', 'Atividade', 'Tipo', 'Conteudo', 'Prazo', 'Status'])

    try:
        disciplinas = pd.read_csv('disciplinas.csv')
    except:
        disciplinas = pd.DataFrame(columns=['Nome', 'Cor'])

    try:
        grades = pd.read_csv('grades.csv')
        grades['Nota'] = pd.to_numeric(grades['Nota'], errors='coerce').fillna(0.0)
        grades['Peso'] = pd.to_numeric(grades['Peso'], errors='coerce').fillna(0)
    except:
        grades = pd.DataFrame(columns=['Disciplina', 'Avaliação', 'Nota', 'Peso'])

    if 'Conteudo' not in tasks.columns: tasks['Conteudo'] = ""
    return tasks, disciplinas, grades


def save_data(t, d, g):
    t_save = t.copy()
    if not t_save.empty:
        t_save['Prazo'] = t_save['Prazo'].dt.strftime('%d/%m/%Y')
    t_save.to_csv('tasks.csv', index=False)
    d.to_csv('disciplinas.csv', index=False)
    g.to_csv('grades.csv', index=False)


tasks, disciplinas, grades = load_data()

# 3. POMODORO (SESSION STATE)
if 'pomodoro_tempo' not in st.session_state: st.session_state.pomodoro_tempo = 25 * 60
if 'pomodoro_rodando' not in st.session_state: st.session_state.pomodoro_rodando = False

# 4. BARRA LATERAL
st.sidebar.title("🎓 Menu")
aba = st.sidebar.radio("Navegação:", ["Início", "To-Do List", "Calendário", "Notas e Médias", "Gráficos"])

st.sidebar.divider()
st.sidebar.subheader("🍅 Pomodoro")
m, s = divmod(st.session_state.pomodoro_tempo, 60)
st.sidebar.markdown(f"<h1 style='text-align: center; color: #FF4B4B;'>{m:02d}:{s:02d}</h1>", unsafe_allow_html=True)
c1, c2 = st.sidebar.columns(2)
if c1.button("Play/Pause"): st.session_state.pomodoro_rodando = not st.session_state.pomodoro_rodando
if c2.button("Reset"):
    st.session_state.pomodoro_tempo, st.session_state.pomodoro_rodando = 25 * 60, False
    st.rerun()

if st.session_state.pomodoro_rodando and st.session_state.pomodoro_tempo > 0:
    time.sleep(1)
    st.session_state.pomodoro_tempo -= 1
    st.rerun()

# 5. EXECUÇÃO DAS ABAS
if aba == "Início":
    st.title("📚 Disciplinas")
    col_main, col_side = st.columns([2, 1])
    with col_side:
        st.subheader("Gerenciar")
        n_disc = st.text_input("Nova Disciplina")
        c_disc = st.color_picker("Cor", "#00F900")
        if st.button("Adicionar"):
            if n_disc:
                disciplinas = pd.concat([disciplinas, pd.DataFrame({'Nome': [n_disc], 'Cor': [c_disc]})],
                                        ignore_index=True)
                save_data(tasks, disciplinas, grades);
                st.rerun()
        exc_disc = st.selectbox("Remover", disciplinas['Nome'].tolist() if not disciplinas.empty else ["Nenhuma"])
        if st.button("Excluir"):
            disciplinas = disciplinas[disciplinas['Nome'] != exc_disc]
            save_data(tasks, disciplinas, grades);
            st.rerun()

    with col_main:
        if disciplinas.empty:
            st.info("Adicione disciplinas no painel ao lado.")
        else:
            for _, row in disciplinas.iterrows():
                t_filtro = tasks[tasks['Disciplina'] == row['Nome']]
                prog_val = t_filtro['Status'].mean() if not t_filtro.empty else 0
                st.markdown(f"""
                <div style="padding:15px; border-left: 10px solid {row['Cor']}; background-color: #FFFFFF; border-radius: 10px; margin-bottom: 10px; border: 1px solid #DDD;">
                    <h3 style="margin:0; color: #111;">{row['Nome']}</h3>
                    <p style="margin:0; color: #444;">Progresso: {prog_val:.0f}%</p>
                </div>
                """, unsafe_allow_html=True)
                st.progress(prog_val / 100)

elif aba == "To-Do List":
    st.title("📝 Lista de Atividades")
    with st.expander("➕ Nova Atividade"):
        with st.form("f_new"):
            d_sel = st.selectbox("Disciplina", disciplinas['Nome'].tolist() if not disciplinas.empty else [])
            at_tit = st.text_input("Título")
            at_tip = st.selectbox("Tipo", ["Prova", "Exercício", "Avaliação", "Trabalho", "Leitura"])
            at_cont = st.text_area("Conteúdo/Detalhes")
            at_pz = st.date_input("Prazo", format="DD/MM/YYYY")
            if st.form_submit_button("Salvar"):
                nova = pd.DataFrame(
                    {'Disciplina': [d_sel], 'Atividade': [at_tit], 'Tipo': [at_tip], 'Conteudo': [at_cont],
                     'Prazo': [pd.to_datetime(at_pz)], 'Status': [0]})
                tasks = pd.concat([tasks, nova], ignore_index=True)
                save_data(tasks, disciplinas, grades);
                st.rerun()

    for i, row in tasks.iterrows():
        with st.container():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            c1.markdown(f"**{row['Disciplina']}**<br>{row['Tipo']}: {row['Atividade']}", unsafe_allow_html=True)
            new_s = c2.select_slider("Status %", options=[0, 25, 50, 75, 100], value=int(row['Status']), key=f"sl_{i}")
            if new_s != row['Status']:
                tasks.at[i, 'Status'] = new_s
                save_data(tasks, disciplinas, grades);
                st.rerun()
            c3.write(f"📅 {row['Prazo'].strftime('%d/%m/%Y') if pd.notnull(row['Prazo']) else 'S/Data'}")
            if c4.button("🗑️", key=f"del_{i}"):
                tasks = tasks.drop(i).reset_index(drop=True)
                save_data(tasks, disciplinas, grades);
                st.rerun()
            if row['Conteudo']: st.caption(f"📖 {row['Conteudo']}")
            st.divider()

elif aba == "Calendário":
    st.title("📅 Calendário de Entregas")
    if tasks.empty:
        st.info("Nenhuma atividade com prazo cadastrada.")
    else:
        # Filtro de Mês para facilitar no mobile
        meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        mes_sel = st.selectbox("Filtrar por Mês", range(1, 13), index=datetime.now().month - 1,
                               format_func=lambda x: meses[x - 1])

        df_mes = tasks[tasks['Prazo'].dt.month == mes_sel].sort_values('Prazo')

        if df_mes.empty:
            st.warning("Sem atividades para este mês.")
        else:
            for data, gp in df_mes.groupby(df_mes['Prazo'].dt.date):
                st.markdown(f"#### 📅 {data.strftime('%d/%m/%Y')}")
                for _, t in gp.iterrows():
                    cor = disciplinas[disciplinas['Nome'] == t['Disciplina']]['Cor'].values[0] if t['Disciplina'] in \
                                                                                                  disciplinas[
                                                                                                      'Nome'].values else "#888"
                    st.markdown(f"""
                    <div style="padding:10px; border-left: 5px solid {cor}; background-color: #FFFFFF; color: #111; border-radius: 5px; margin-bottom: 5px; border: 1px solid #EEE;">
                        <b>{t['Disciplina']}</b>: {t['Atividade']} ({t['Status']}%)
                    </div>
                    """, unsafe_allow_html=True)

elif aba == "Notas e Médias":
    st.title("⚖️ Notas")
    m_ap = st.number_input("Média Aprovação", value=6.0)
    with st.expander("➕ Lançar Nota"):
        with st.form("fn"):
            dn = st.selectbox("Disciplina", disciplinas['Nome'].tolist() if not disciplinas.empty else [])
            av = st.text_input("Avaliação")
            nt = st.number_input("Nota", 0.0, 10.0, step=0.1)
            ps = st.number_input("Peso %", 0, 100, step=5)
            if st.form_submit_button("Salvar Nota"):
                grades = pd.concat(
                    [grades, pd.DataFrame({'Disciplina': [dn], 'Avaliação': [av], 'Nota': [nt], 'Peso': [ps]})],
                    ignore_index=True)
                save_data(tasks, disciplinas, grades);
                st.rerun()

    for d in disciplinas['Nome']:
        n_d = grades[grades['Disciplina'] == d]
        if not n_d.empty:
            st.subheader(f"📖 {d}")
            for idx, r in n_d.iterrows():
                ci, cd = st.columns([5, 1])
                ci.write(f"• {r['Avaliação']}: **{r['Nota']}** (Peso {r['Peso']}%)")
                if cd.button("🗑️", key=f"gn_{idx}"):
                    grades = grades.drop(idx).reset_index(drop=True)
                    save_data(tasks, disciplinas, grades);
                    st.rerun()
            s_p = n_d['Peso'].sum()
            med = (n_d['Nota'] * n_d['Peso']).sum() / s_p if s_p > 0 else 0
            st.metric("Média Atual", f"{med:.2f}")
            st.divider()

elif aba == "Gráficos":
    st.title("📊 Estatísticas")
    if not tasks.empty:
        st.plotly_chart(px.bar(tasks.groupby('Disciplina')['Status'].mean().reset_index(), x='Disciplina', y='Status',
                               title="Progresso Médio %"))