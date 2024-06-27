import streamlit as st
import pandas as pd
from pandas.tseries.offsets import BDay
import datetime as dt
from datetime import datetime
import numpy as np
import mysql.connector
from mysql.connector.cursor import MySQLCursor
import io
from io import StringIO, BytesIO
from dotenv import load_dotenv
import os
from streamlit.logger import get_logger
import matplotlib.pyplot as plt
import calendar
import requests
import base64
import html
from streamlit_authenticator import Authenticate
from sqlalchemy.orm import sessionmaker
import plotly.graph_objects as go
import numpy as np
from PIL import Image, ImageDraw, ImageFont
# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

st.set_page_config(
    page_title="Acompanhamento Metas",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ttl=240.0
# ttl=800.0
# ttl=600

@st.cache_data(ttl=3600000)
def buscaDadosSQL(tabela,equipe=None):
    global mesAtu

    config = {
    'host': '77.37.40.212',
    # 'host': 'localhost',
    'user': 'root',
    'port':'3306',
    'password': os.getenv('MYSQL_ROOT_PASSWORD'),
    'database': 'gestao_equipe'
    }
    mesAtu=dt.datetime.now().month
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        print("Conexão ao MySQL bem-sucedida!")
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        st.stop

    if tabela == 'Equipe_Completa':
        query=f"SELECT * FROM {tabela};"
        Base=pd.read_sql(query, conn)
        conn.close()
        return Base
    elif tabela=='metas_cobranca_geral':
        query=f"SELECT * FROM {tabela};"
        Base=pd.read_sql(query, conn)
        conn.close()
        return Base
    elif tabela=='Liquidado':
        query=f"""SELECT * FROM {tabela};"""
        Base=pd.read_sql(query, conn)
        Base=Base.drop_duplicates()
        conn.close()
        return Base
    else:
        query=f"SELECT * FROM {tabela};"
        Base=pd.read_sql(query, conn)
        conn.close()
        return Base
    
@st.cache_data(ttl=500.0)
def buscaDadosSQLMatual(tabela,mesAtu=None,equipe=None):
    config = {
    'host': '77.37.40.212',
    # 'host': 'localhost',
    'user': 'root',
    'port':'3306',
    'password': os.getenv('MYSQL_ROOT_PASSWORD'),
    'database': 'gestao_equipe'
    }

    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        print("Conexão ao MySQL bem-sucedida!")
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        st.stop
    if tabela != 'AtualizaBanco':
        if tabela=="Liquidado":
            query=f"""SELECT * FROM {tabela}
                    WHERE MONTH(`Data Liquidacao`) = {mesAtu};"""
            Base=pd.read_sql(query, conn)
            Base=Base.drop_duplicates()
            conn.close()
            return Base
        else:
            query=f"""SELECT * FROM {tabela}
                    WHERE MONTH(`Data Vencimento`) = {mesAtu};"""
            Base=pd.read_sql(query, conn)
            conn.close()
            return Base
    else:
        query=f"""SELECT * FROM {tabela}"""
        Base=pd.read_sql(query, conn)
        conn.close()
        return Base

def dias_uteis_no_mes(ano, mes):
    data_inicial = pd.Timestamp(f'{ano}-{mes}-01')
    data_final = pd.Timestamp(f'{ano}-{mes + 1}-01') - pd.DateOffset(days=1)
    
    datas = pd.date_range(start=data_inicial, end=data_final, freq=BDay())
    
    return len(datas)

def dias_uteis_que_faltam(mesNum):

    hoje = pd.Timestamp(datetime.now())
    
    mes=hoje.month
    if mesNum >= mes:
        # Encontrar o último dia do mês atual
        ultimo_dia_do_mes = hoje + pd.offsets.MonthEnd(0)
        
        # Calcular os dias úteis restantes
        datas = pd.date_range(start=hoje, end=ultimo_dia_do_mes, freq=BDay())
        return len(datas)
    else:
        datas=1
        return 1

def exibeEquipe(LiquidadoEquipeMerge,colaborador,eqp,rpt):
    if colaborador == 'TODOS':
        filtro_sit = LiquidadoEquipeMerge['Nome_Colaborador'].notnull()  # Qualquer valor diferente de NaN
    else:
        filtro_sit = LiquidadoEquipeMerge['Nome_Colaborador'] == colaborador
    if eqp == 'TODOS':
        filtro_eqp = LiquidadoEquipeMerge['EQUIPE'].notnull()  # Qualquer valor diferente de NaN
    else:
        filtro_eqp = LiquidadoEquipeMerge['EQUIPE'] == eqp
    if rpt == 'TODOS':
        filtro_rpt = LiquidadoEquipeMerge['REPORTE'].notnull()  # Qualquer valor diferente de NaN
    else:
        filtro_rpt = LiquidadoEquipeMerge['REPORTE'] == rpt

    DfEqpFiltro=LiquidadoEquipeMerge.loc[filtro_sit & filtro_eqp & filtro_rpt].reset_index(drop=True)
    qtdeColabs=len(DfEqpFiltro)
    return DfEqpFiltro,qtdeColabs

# Define uma função para criar um container personalizado com cor de fundo
def colored_metric(content, color):
    return f'<div style="display: flex;padding: 10px; background-color: rgb({color}/0.4); border: 2px solid white; border-radius: 5px;">{content}</div>'

def get_color(value):
    return "255 0 0" if value < 0 else "50 205 50"

#Relatório de Liquidação
def import_base(mesNum):
    mesAtu=mesNum
    BaseLiqAnt=buscaDadosSQL('Liquidado')
    BaseLiqAtu=buscaDadosSQLMatual('Liquidado',mesAtu,equipe=None)
    BaseLiq=pd.concat([BaseLiqAnt,BaseLiqAtu])
    BaseAliq=buscaDadosSQLMatual('Areceber',mesAtu)
    try:
        BaseLiq['Valor Liquidado']=BaseLiq['Valor Liquidado'].str.replace(",",".").astype(float)
        BaseAliq['Valor Original']=BaseAliq['Valor Original'].str.replace(",",".").astype(float)
    except:
        pass

    BaseLiq['Data Liquidacao']=pd.to_datetime(BaseLiq['Data Liquidacao'],dayfirst=True)
    BaseAliq['Data Vencimento']=pd.to_datetime(BaseAliq['Data Vencimento'],dayfirst=True)

    return BaseLiq,BaseAliq

def run(user_info):
    # Adicionar um botão de logout no dashboard

    st.sidebar.image('marca-uninter-horizontal.webp', width=200)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h1 style='text-align: left; font-size: 50px;'>ACOMPANHAMENTO DE METAS</h1>", unsafe_allow_html=True)
        st.write(f"Bem-vindo, {user_info[0]} - {user_info[1]} - {user_info[2]}!") 
        
            
    EquipeGeral=buscaDadosSQL('Equipe_Completa')
    atualizacao=buscaDadosSQLMatual('AtualizaBanco')
    atualizacaoData=atualizacao.iloc[-1,0].strftime("%d/%m/%Y")
    atualizacaoHora=atualizacao.iloc[-1,1]

    EquipeMetas=EquipeGeral[EquipeGeral['EQUIPE']!='MARCOS']
    colaborador=list(EquipeMetas['Nome_Colaborador'].unique())
    colaborador.insert(0,'TODOS')
    Equipe=list(EquipeMetas['EQUIPE'].unique())
    Equipe.insert(0,'TODOS')
    Reporte=list(EquipeMetas['REPORTE'].unique())
    Reporte.insert(0,'TODOS')

    # col1, col2,col3,col4,col5,col6,col7,col8, = st.columns([3,3,5,5,5,5,5,5])

    with st.sidebar:
        st.write(f"Última Atualização - Data:{atualizacaoData} Hora:{atualizacaoHora} ")
        meses={i:j for j,i in enumerate(calendar.month_abbr)}
        mesLiq = st.selectbox(
        'Mês',list(meses.keys())[1:])
        mesNum=meses[f"{mesLiq}"]

        anoInicio=2024
        anoFim=anoInicio+20
        anoLiq = st.selectbox(
        'Ano',range(anoInicio,anoFim))

    # with st.container(border=True):
    #     col1, col2, col3 = st.columns([5,5,5])

        # with col1:
        optionsEqp = st.selectbox(
        'Filtro por Equipe',
        Equipe)
        # with col2:
        optionsRpt = st.selectbox(
        'Filtro por Responsável',
        Reporte)

        # with col3:
        colaborador = st.selectbox(
        'Filtro por Colaborador',
        colaborador)
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            del st.session_state.user_info 
            st.experimental_rerun()
            
        BaseLiq,BaseAliq=import_base(mesNum)
        BaseLiq=BaseLiq.drop_duplicates()
        try:
            BaseAliq['Valor Original']=BaseAliq['Valor Original'].str.replace(",",".").astype(float)
        except:
            pass

        aliqcolabs=BaseAliq[BaseAliq['Parcela']==1]

        aliqcolabs=aliqcolabs.groupby('Criado Por',as_index=False)['Valor Original'].sum()

        aliqcolabs=aliqcolabs.rename(columns={'Valor Original':'A Receber'})

        BaseLiqmes=BaseLiq.loc[(BaseLiq['Data Liquidacao'].dt.month==mesNum) & (BaseLiq['Data Liquidacao'].dt.year==anoLiq)]

        BaseaLiqmes=BaseAliq[BaseAliq['Data Vencimento'].dt.month==mesNum]

        BaseAliqMetas=BaseaLiqmes[BaseaLiqmes['Parcela']==1]

        BaseAliqMetas=BaseAliqMetas.rename(columns={'Valor Original':'A Receber'})

        acordoOnline=BaseLiqmes[BaseLiqmes['Criado Por']=='Acordo Online']

        BaseLiqSemAO=BaseLiqmes[BaseLiqmes['Criado Por']!='Acordo Online']

        LiquidadoEquipe=BaseLiqSemAO[BaseLiqSemAO['Criado Por'].isin(EquipeGeral['Nome_Colaborador'])]

        LiquidadoEquipeMerge=BaseLiqSemAO.merge(EquipeGeral,left_on='Criado Por',right_on='Nome_Colaborador')

        LiquidadoEquipeMerge['valorPcolab']=LiquidadoEquipeMerge.groupby('Nome_Colaborador')['Valor Liquidado'].transform(sum)

        LiquidadoEquipeMerge=LiquidadoEquipeMerge.sort_values(by='valorPcolab',ascending=False)

        LiquidadoEquipeMerge['RANK'] = LiquidadoEquipeMerge['valorPcolab'].rank(method='dense', ascending=False).astype(int)

        cobranca_geral=LiquidadoEquipeMerge[LiquidadoEquipeMerge['EQUIPE']=='COBRANÇA_GERAL']

        telecobranca=LiquidadoEquipeMerge[LiquidadoEquipeMerge['EQUIPE']=='Telecobrança']

        Apoio=LiquidadoEquipeMerge[LiquidadoEquipeMerge['EQUIPE']=='MARCOS']

        ColabsExternos=BaseLiqSemAO[~BaseLiqSemAO['Criado Por'].isin(EquipeGeral['Nome_Colaborador'])]

        # cobranca_geral.columns
        # cobranca_geral.groupby(['REPORTE','Nome_Colaborador'],as_index=False)['Valor Liquidado'].sum()

        metas=buscaDadosSQL('metas_cobranca_geral',equipe=None)
        metas['Mes']=metas['Mês'].dt.month
        metas['Ano']=metas['Mês'].dt.year
        metasFiltro=metas.loc[(metas['Mes']==mesNum) & (metas['Ano']==anoLiq)]
        MetaLiq=list(metasFiltro['Meta_geral'])[0]
        MetaTele=list(metasFiltro['Meta_Tele'])[0]
        Metaindividual=list(metasFiltro['Meta_Individual'])[0]
        print(Metaindividual)
        MetaindividualTele=list(metasFiltro['Meta_Individual_Tele'])[0]
        print(MetaindividualTele)
        dias_uteis=dias_uteis_no_mes(anoLiq, mesNum)
        dias_uteis_falta=dias_uteis_que_faltam(mesNum)

        # token=os.getenv('token')
        token=os.getenv('token')
        r = requests.get(f'https://api.invertexto.com/v1/holidays/{anoLiq}?token={token}&state=PR',verify=False)
        feriados=r.json()

        feriadoNacionais=[data['date'] for data in feriados]

        feriadosDF=pd.DataFrame(feriadoNacionais,columns=["Data"])
        feriadosDF["Data"]=pd.to_datetime(feriadosDF["Data"])
        feriadosDF["DiaSemana"]=feriadosDF["Data"].dt.strftime("%A")
        feriadosDF["Mês"]=feriadosDF["Data"].dt.month
        domingo="Sunday"
        sabado="Saturday"
        feriadosDUtil=feriadosDF.loc[(feriadosDF['DiaSemana']!=domingo) & (feriadosDF['DiaSemana']!=sabado)]

        qtdeFeriados=feriadosDUtil.groupby('Mês',as_index=False)['Data'].count()
        qtdeFeriadosMes=qtdeFeriados[qtdeFeriados['Mês']==mesNum]

        try:
            nFer=list(qtdeFeriadosMes['Data'])[0]
            dias_uteis=dias_uteis-nFer
            dias_uteis_falta=dias_uteis_falta-nFer
        except:
            nFer=0
            dias_uteis=dias_uteis-nFer
            dias_uteis_falta=dias_uteis_falta-nFer

        diaHj=dt.datetime.now().day
        cobgeral=cobranca_geral['Valor Liquidado'].sum()
        tele=telecobranca['Valor Liquidado'].sum()
        acOn=acordoOnline['Valor Liquidado'].sum()
        totalLiq=BaseLiqmes['Valor Liquidado'].sum()
        liqDia=BaseLiqmes.loc[(BaseLiqmes['Data Liquidacao'].dt.day==diaHj),'Valor Liquidado'].sum()
        aLiquidar=BaseAliqMetas['A Receber'].sum()
        faltaMeta=totalLiq-MetaLiq
        faltaMetaTele=tele-MetaTele
        dados_dias_anteriores = BaseLiqmes[BaseLiqmes['Data Liquidacao'].dt.day < diaHj]

        media_por_colaborador_dia = dados_dias_anteriores.groupby('Criado Por',as_index=False)['Valor Liquidado'].mean()

        LiqPordia=BaseLiqmes.groupby('Data Liquidacao',as_index=False)['Valor Liquidado'].sum()
        dias = LiqPordia['Data Liquidacao']
        valores = LiqPordia['Valor Liquidado']
        percentual_falta = (((totalLiq - MetaLiq) / MetaLiq) * 100)
        percentual_atingido=(totalLiq/MetaLiq) * 100
        # Dados de exemplo: datas e valores de liquidação diária

        # Calcula a liquidação acumulada
        LiqPordia['Liquidação Acumulada'] = LiqPordia['Valor Liquidado'].cumsum()

    def criaImagem(valor,Delta,label,imagem,t=0,r=0,b=0,l=0,width=240,height=130):

        # Função para converter imagem local em base64
        def get_base64_of_bin_file(bin_file):
            with open(bin_file, 'rb') as f:
                data = f.read()
            return base64.b64encode(data).decode()

        # Caminho para a imagem local
        image_path = imagem
        image_base64 = get_base64_of_bin_file(image_path)

        # CSS para definir a imagem de fundo e o estilo da métrica
        st.markdown(
            f"""
            <style>
            .metric-container {{
                position: relative;
                width: f"{width}"px;
                height: f"{height}"px;
                background-image: url(data:image/jpeg;base64,{image_base64});
                background-size: cover;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 15px; /* Ajuste o valor para controlar a curvatura das bordas */
                box-shadow: 5px 5px 10px rgba(192,192,192, 0.3); 
                margin-bottom: 20px;
                # margin:f"{t}px {r}px {b}px {l}px";
            }}
            .metric-text {{
                font-size: 25px;
                color: white;
                # text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.7);
                text-align: center;
                margin:10px 0px 0px 0px;
            }}
            .metric-label {{
                font-size: 20px;
                display: block; /* Faz o texto ocupar uma linha inteira */
                # margin-bottom: -29px; /* Ajuste o valor negativo para controlar o espaçamento */
                margin:0px 0px -16px 0px;
            }}
            .metric-delta {{
                font-size: 20px;
                # text-align: center;
                color: rgb(0,255,0);
                display: block; /* Faz o texto ocupar uma linha inteira */
                margin:-16px 0px 0px 0px; /* Ajuste o valor negativo para controlar o espaçamento */
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        # HTML para criar a métrica com a imagem de fundo

        metrica=st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-text">
                <span class="metric-label">{label}</span>
                    {valor}
                <span class="metric-delta"><b>{Delta}</b></span>
                </div>
            </div>
            """.replace(',', '.'),
            unsafe_allow_html=True
        )
        return metrica

    tab1, tab2 = st.tabs(["GeraL", "Tele"])

    with tab1:
        col1, col2, col3, col4,col5,col6= st.columns([2,2,2,2,2,2])

        with col1:
            label="Dias de Trabalho"
            criaImagem(dias_uteis,f"Faltam {dias_uteis_falta} dias",label,"fundoAzul.jpeg")
                # st.metric(label="Dias Úteis", value=f"{dias_uteis}",delta=f"-faltam {dias_uteis_falta} dias",delta_color='inverse')            

        with col2:
            label="Meta Liquidado"
            M=f"R${MetaLiq:,.0f}".replace(',', '.')
            D=f"{percentual_falta:.0f}% {'Para meta' if percentual_falta<0 else 'Meta atingida'}"
            criaImagem(M,D,label,"fundoAzul.jpeg",b=20)
            # st.metric(label="Meta Liquidado", value=f"R${MetaLiq:,.0f}".replace(',', '.'), delta=f"{percentual_falta:.0f}% {'Para atingir meta' if percentual_falta<0 else 'Meta atingida'}")

        with col3:
            diaHj=dt.datetime.now().date().strftime("%d/%m/%Y")
            liq=f"R${totalLiq:,.0f}".replace(',', '.')
            D=f"{percentual_atingido:.0f}%"
            label="Total Liquidado"
            criaImagem(liq,D,label,"fundoAzul.jpeg",b=20)
            # with st.container(border=True): 
            # criaGrafico(dias,valores,color1,color2,totalLiq,percentual_atingido)
            # st.metric(label=f"Liquidado até {diaHj}", value=f"R${totalLiq:,.0f}".replace(',', '.'),delta=f"{percentual_atingido:.0f}% Atingido Meta")
                
        with col4:
            metaDia=MetaLiq/dias_uteis
            deltaMeta=f"{((totalLiq/dias_uteis)-metaDia)/metaDia:,.2f}%".replace(',', '.')
            valorDefSup=totalLiq-(MetaLiq/dias_uteis)*(dias_uteis-dias_uteis_falta)
            defsup=f"{valorDefSup:,.2f}".replace(",",";").replace(".",",").replace(";",".")
            label="Meta Diária"

            criaImagem(f"R${metaDia:,.0f}".replace(',', '.'),f"{deltaMeta}",label,"fundoAzul.jpeg",b=20)

            # with st.container(border=True): 
            #     st.metric(label="Meta Diária", value=f"R${metaDia:,.0f}".replace(',', '.'),delta=f"{deltaMeta}")

        with col5:
            metaDia=MetaLiq/dias_uteis
            deltaMeta=f"{((totalLiq/dias_uteis)-metaDia)/metaDia:,.2f}%".replace(',', '.')
            valorDefSup=totalLiq-(MetaLiq/dias_uteis)*(dias_uteis-dias_uteis_falta)
            defsup=f"{valorDefSup:,.2f}".replace(",",";").replace(".",",").replace(";",".")
            label="Déficit/Superávit"
            value=f"R${valorDefSup:,.0f}".replace(',', '.')
            delta=f"{'Superávit' if valorDefSup>0 else '-Déficit'}"
            criaImagem(value,delta,label,"fundoAzul.jpeg",b=20)

            # with st.container(border=True): 
            #     st.metric(label="Déficit/Superávit", value=f"R${valorDefSup:,.0f}".replace(',', '.'),delta=f"{'Superávit' if valorDefSup>0 else '-Déficit'}")
        with col6:
            Delta=(aLiquidar/MetaLiq)*100
            label=f"A Liquidar".replace(',', '.')
            criaImagem(f"R${aLiquidar:,.0f}",f"{Delta:.2f}%",label,"fundoAzul.jpeg",b=20)
        DfEqpFiltro,qtdeColabs = exibeEquipe(LiquidadoEquipeMerge,colaborador, optionsEqp, optionsRpt)

        if optionsEqp=='Telecobrança':
            cobranca_geral=DfEqpFiltro.query("CARGO=='ASSISTENTE_TELE'")
            meta=MetaindividualTele
        else:
            cobranca_geral=DfEqpFiltro.query("CARGO=='ASSISTENTE'")
            meta=Metaindividual

        grafCobGeral=(cobranca_geral.groupby(['Nome_Colaborador','REPORTE','SIT_ATUAL'],as_index=False)['Valor Liquidado'].sum()).sort_values(by='Valor Liquidado',ascending=False)
        # st.dataframe(BaseLiqmes, hide_index=True, height=800, width=1100,use_container_width=True)

        col1, col2 = st.columns([2,2])

        with col1:
            # with st.container(border=True):
            # Função para formatar números em formato curto
            def format_number_short(value):
                if value >= 1_000_000:
                    return f'{value / 1_000_000:.1f}M'
                elif value >= 1_000:
                    return f'{value / 1_000:.1f}k'
                else:
                    return str(value)
                
            x = LiqPordia['Data Liquidacao']
            y = LiqPordia['Liquidação Acumulada']
            labels = [format_number_short(value) for value in y]
            linha_meta = np.full(len(x), MetaLiq)
            
            #Gráfico de área
            fig = go.Figure(go.Scatter(x=x, y=y, name="Liquidado",
                                line_shape='linear',mode='lines+markers',fill='tozeroy', 
                                fillcolor='rgba(106,90,205, 0.2)'
                                ))
            # Adicione anotações para os rótulos de dados
            for i, txt in enumerate(y):
                fig.add_annotation(
                    x=x[i],
                    y=y[i],
                    text=str(format_number_short(txt)),  # Convertendo o valor para string, se necessário
                    showarrow=False,
                    textangle=-60,  # Ângulo de rotação do texto
                    xanchor='center',
                    yanchor='bottom',
                    font=dict(size=12, color="rgba(255,250,250, 0.5)")
                )
            #Linha de meta
            fig.add_trace(go.Scatter(x=x, y=linha_meta,mode='lines',
            line=dict(color='Red', width=2, dash='dashdot'),
            opacity=0.5,
            name='Meta Diaria'))
            
            fig.add_annotation(
                x=x.iloc[0],
                y=MetaLiq,
                text=f"{MetaLiq:,.0f} Meta".replace(",","."),
                showarrow=False,
                yshift=10,
                font=dict(
                    color="Red",
                    size=12
                )
            )
            
            fig.update_layout(title="Liquidação Acumulada por dia",height=350,margin=dict(l=60, r=20, t=80, b=60),plot_bgcolor="rgba(128,128,128,0.1)",paper_bgcolor="rgba(128,128,128,0.1)")

            st.plotly_chart(fig, use_container_width=True,meta=f"{metaDia}")

            # # Seu código para criar o gráfico
            # fig, ax = plt.subplots(figsize=(25  , 27))  # Ajuste os valores conforme necessário
            # colabs = grafCobGeral['Nome_Colaborador']
            # y_pos = range(len(colabs))
            # performance = grafCobGeral['Valor Liquidado']

            # bars=ax.barh(y_pos, performance, align='center')

            # for bar, val in zip(bars, performance):
            #     val=float(val)
            #     meta=float(meta)
            #     ax.text(bar.get_x() + bar.get_width(), bar.get_y() + bar.get_height() / 2, 
            #         f'{(val/meta)*100:,.2f}%'.replace(',', '.'), color='white', fontweight='bold', fontsize=20, va='center')

            # ax.vlines(x=meta, ymin=-1.5, ymax=len(colabs), color='red', linestyle='--', label='Meta')
            # ax.text(meta, -1.5, f'Meta: {meta:,.0f}'.replace(',', '.'), color='red', fontsize=30, ha='right')

            # ax.set_yticks(y_pos)
            # ax.set_yticklabels(colabs, color="white", fontsize=20,fontweight='bold')
            # ax.invert_yaxis()
            # ax.set_xlabel('Valor Liquidado')
            # ax.set_title('Liquidado por Colaborador')
            # ax.spines['top'].set_visible(False)
            # ax.spines['left'].set_visible(False)
            # ax.spines['right'].set_visible(False)
            # ax.set_facecolor(color="none")
            # fig.patch.set_alpha(0)
            
            # # Ajuste a largura da figura para acomodar os nomes completos
            # fig.tight_layout()

            # # Salvar a figura como BytesIO
            # image_stream = BytesIO()
            # fig.savefig(image_stream, format="png")
            # image_stream.seek(0)  # Voltar ao início do stream

            # # Exibir a imagem sem use_container_width
            # st.image(image_stream)

            # with st.container(border=True,height=750):

            cobranca_geral=cobranca_geral.merge(aliqcolabs,left_on='Nome_Colaborador',right_on='Criado Por',how='left')
            metaDiaria=round(float(meta)/dias_uteis)
            diasPassados=(dias_uteis-dias_uteis_falta)
            # agroupTab=cobranca_geral.groupby('REPORTE')[['Nome_Colaborador','Valor Liquidado']].agg({'Nome_Colaborador':'first','Valor Liquidado':'sum'})
            # cobranca_geral['RANK']=range(1,len(cobranca_geral['Nome_Colaborador'])+1)
            # mes=dt.datetime.now().month
            # if len(cobranca_geral[cobranca_geral['A Receber'].isna()])==len(cobranca_geral) or mesNum < mes:
            #     cobranca_geral['A Receber']=0
            # try:
            #     agroupTab = cobranca_geral.pivot_table(index=['RANK','REPORTE','Nome_Colaborador','A Receber'], values='Valor Liquidado', aggfunc='sum').reset_index().sort_values(by='Valor Liquidado',ascending=False)

            # except:
                
            #     agroupTab=cobranca_geral[['RANK','REPORTE','Nome_Colaborador','Valor Liquidado','A Receber']]
            #     print(agroupTab['A Receber'], 'Baixo')

            # agroupTab['% Atingido Meta']=agroupTab['Valor Liquidado'].apply(lambda x:f"{x/meta*100:.2f}%")

            # # agroupTab['RANK']=range(1,len(agroupTab['Nome_Colaborador'])+1)

            # agroupTab['Meta Diária']=f"R${metaDiaria:,.2f}".replace(",",";").replace(".",",").replace(";",".")

            # if diasPassados ==0:
            #     diasPassados=1

            # agroupTab['Realizado por Dia (Média)'] = (agroupTab['Valor Liquidado']-media_por_colaborador_dia['Valor Liquidado'])/(diasPassados-1)
            # agroupTab['Déficit/Superávit Diário']=agroupTab['Realizado por Dia (Média)'].apply(lambda x:f"R${(x-metaDiaria):,.2f}".replace(",",";").replace(".",",").replace(";","."))        
            # agroupTab['Realizado por Dia (Média)']=agroupTab['Realizado por Dia (Média)'].apply(lambda x: f"R${x:,.2f}".replace(",",";").replace(".",",").replace(";","."))

            # agroupTab['Realizado Total']=agroupTab['Valor Liquidado'].apply(lambda x: f"R${x:,.2f}".replace(",",";").replace(".",",").replace(";","."))

            # agroupTab['Falta']=agroupTab['Valor Liquidado'].apply(lambda x: f"R${x-meta:,.2f}".replace(",",";").replace(".",",").replace(";","."))

            # agroupTab['% Falta']=agroupTab['Valor Liquidado'].apply(lambda x:f"{(x/meta*100)-100:.2f}%")
            
            # agroupTab['Déficit/Superávit Total']=agroupTab['Déficit/Superávit Diário'].apply(lambda x: f"R${float(x.replace('R$','').replace('.','').replace(',','.'))*(diasPassados-1):,.2f}".replace(",",";").replace(".",",").replace(";","."))
            # agroupTab['Receber']=agroupTab['A Receber'].apply(lambda x: f"R${x:,.2f}".replace(",",";").replace(".",",").replace(";","."))
            # # agroupTab['PREVISÃO_META']=agroupTab['Realizado Total']+agroupTab['A Receber']
            # # Função para verificar se a meta foi batida
            # def verificar_meta(row):
            #     if row['Valor Liquidado'] >= meta:
            #         return 'Meta Batida'
            #     elif (row['Valor Liquidado']+ row['A Receber']) >= meta:
            #         return 'Pode Bater Meta'
            #     elif (row['Valor Liquidado']+ row['A Receber']+(dias_uteis_falta*metaDiaria)) >= meta:
            #         return 'Chance de bater a meta'
            #     else:
            #         return 'Não irá bater Meta'
                
            # agroupTab['Resultado']=agroupTab.apply(verificar_meta, axis=1)


            # agroupTab=agroupTab[['RANK','REPORTE','Nome_Colaborador','Realizado Total','% Atingido Meta','Falta','% Falta','Meta Diária','Realizado por Dia (Média)','Déficit/Superávit Diário','Déficit/Superávit Total','Receber','Resultado']]
            
            # # Função para definir a cor do texto com base no conteúdo da coluna 'Resultado'
            # def color_text(value):
            #     if value == 'Meta Batida':
            #         color = 'blue'
            #     elif value == 'Pode Bater Meta':
            #         color = 'lightblue'
            #     elif value == 'Chance de bater a meta':
            #         color = 'orange'
            #     elif value == 'Não irá bater Meta':
            #         color = 'red'
            #     else:
            #         color = 'black'  # Cor padrão para outros valores
            #     return f'color: {color};'

            # # agroupTab.set_index('RANK', inplace=True)
            # # Aplicando a formatação condicional à coluna 'Resultado'
            # styled_df = agroupTab.style.applymap(lambda x: color_text(x), subset=['Resultado'])

            # # Converte o DataFrame para HTML
            # # Converte o DataFrame para HTML, removendo o índice
            
            # # html_table = styled_df.to_html()
            # # html_table = html_table.replace('<table ', '<table class="table table-dark table-hover" ')

            # # components.html(
            # #     f"""
            # #     <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
            # #     <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
            # #     <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>

            # #     <iframe srcdoc="{html.escape(html_table)}" scrolling="auto" frameborder="0" style="width: 100%; height: 800px;"></iframe>
            # #     """,
            # #     height=800,
            # # )
            # # st.components.v1.html(html_table, height=500, scrolling=True)
            # # st.markdown(html_table, unsafe_allow_html=True)
            # # st.markdown(html_table_bot, unsafe_allow_html=True)
            # st.dataframe(styled_df, hide_index=True, height=800, width=1100,use_container_width=True)
            with col2:
                pass
        with tab2:        
            # Carrega a imagem
            image = Image.open("imagem_meta.jpg")
            draw = ImageDraw.Draw(image)

            # Desenha anotações (exemplo: um círculo e texto)
            draw.ellipse((100, 100, 200, 200), outline="red", width=2)
            font = ImageFont.truetype("arial.ttf", 24)  # Use uma fonte disponível
            draw.text((120, 150), "Anotação", fill="red", font=font)

            # Exibe a imagem no Streamlit
            st.image(image, caption="Imagem com Anotações")

