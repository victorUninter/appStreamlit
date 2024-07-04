import streamlit as st
import pandas as pd
from pandas.tseries.offsets import BDay
import datetime as dt
from datetime import datetime
import numpy as np
from dotenv import load_dotenv
import os
from streamlit.logger import get_logger
import matplotlib.pyplot as plt
import calendar
import requests
import base64
from streamlit_authenticator import Authenticate
from sqlalchemy.orm import sessionmaker
import plotly.graph_objects as go
from PIL import Image, ImageDraw, ImageFont
from classe import DbManager
from sqlalchemy import create_engine, text, select,MetaData # Corrigido
import mysql.connector
import io
import plotly.express as px

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

st.set_page_config(
    page_title="Acompanhamento Metas",
    layout="wide",
    initial_sidebar_state="expanded"
)

def connect():
    config = {
            'host': '77.37.40.212',
            'user': 'root',
            'port': 3306,
            'password': os.getenv('MYSQL_ROOT_PASSWORD'),
            'database': 'gestao_equipe'
        }
    try:
        conn = mysql.connector.connect(**config)
        # self.cursormysql.connector = self.conn.cursor()
        # st.info("Conexão ao MySQL bem-sucedida!")
        return conn
    except ConnectionError as err:
        st.error(f"Erro ao conectar ao MySQL: {err}")
        st.stop()
        
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
    if eqp=='COBRANÇA_GERAL':
        filtro_eqp = LiquidadoEquipeMerge['EQUIPE'] != "Telecobrança"
        if colaborador == 'TODOS':
            filtro_sit = LiquidadoEquipeMerge['colaborador'].notnull()  # Qualquer valor diferente de NaN
        else:
            filtro_sit = LiquidadoEquipeMerge['colaborador'] == colaborador
    # if eqp == 'TODOS':
    #     filtro_eqp = LiquidadoEquipeMerge['EQUIPE'].notnull()  # Qualquer valor diferente de NaN
    else:
        filtro_eqp = LiquidadoEquipeMerge['EQUIPE'] == "Telecobrança"
        if colaborador == 'TODOS':
            filtro_sit = LiquidadoEquipeMerge['colaborador'].notnull()  # Qualquer valor diferente de NaN
        else:
            filtro_sit = LiquidadoEquipeMerge['colaborador'] == colaborador
            
    if rpt == 'TODOS':
        filtro_rpt = LiquidadoEquipeMerge['REPORTE'].notnull()  # Qualquer valor diferente de NaN
    else:
        filtro_rpt = LiquidadoEquipeMerge['REPORTE'] == rpt

    DfEqpFiltro=LiquidadoEquipeMerge.loc[filtro_sit & filtro_eqp & filtro_rpt].reset_index(drop=True)
    qtdeColabs=len(DfEqpFiltro)
    return DfEqpFiltro,qtdeColabs

def import_bases(tabela, mes=None, coluna=None, ano=None):
    conn=connect()
    with conn:
        try:
            # Construir a consulta SQL usando parâmetros nomeados
            if mes and coluna:
                query = f"SELECT * FROM {tabela} WHERE MONTH({coluna}) = {mes}"
                
            elif ano and coluna:
                query = f"SELECT * FROM {tabela} WHERE YEAR({coluna}) = {ano}"
            
            else:
                query = f"SELECT * FROM {tabela}"

            return pd.read_sql(query, conn)  # Passe os parâmetros à consulta
        except Exception as e:
            print(f"Error: {e}")


def run(user_info):
    # Adicionar um botão de logout no dashboard

    st.sidebar.image('marca-uninter-horizontal.webp', width=200)

    col1, col2 = st.columns([3, 1])
    # with col1:
    #     st.markdown("<h1 style='text-align: left; font-size: 50px;'>ACOMPANHAMENTO DE METAS</h1>", unsafe_allow_html=True)
    st.write(f"Bem-vindo, {user_info[0]} - {user_info[1]} - {user_info[2]}!") 
        
    EquipeGeral = import_bases('Equipe_Completa')
    # conn=bd.connect()
    # EquipeGeral=bases.importBases('Equipe_Completa')
 
    atualizacao=import_bases('AtualizaBanco')
        
    atualizacaoData=atualizacao.iloc[-1,0].strftime("%d/%m/%Y")
    atualizacaoHora=atualizacao.iloc[-1,1]

    EquipeMetas=EquipeGeral[EquipeGeral['EQUIPE']!='MARCOS']
    
    colaborador=list(EquipeMetas['Nome_Colaborador'].unique())
    colaborador.insert(0,'TODOS')
    Equipe=list(EquipeMetas['EQUIPE'].unique())
    # Equipe.insert(0,'TODOS')
    Reporte=list(EquipeMetas['REPORTE'].unique())
    Reporte.insert(0,'TODOS')

    # col1, col2,col3,col4,col5,col6,col7,col8, = st.columns([3,3,5,5,5,5,5,5])

    with st.sidebar:
        if st.button("Logout"):
            st.session_state.authenticated = False
            del st.session_state.user_info 
            st.experimental_rerun()

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
      
        BaseLiq=import_bases('view_CobrancaGeral',mesNum,coluna='data_liquidacao')
        BaseAliq=import_bases('view_receberCompleta')
        metas=import_bases('metas_cobranca_geral')
        feriadosDF=import_bases('feriados')

        BaseLiq=BaseLiq.drop_duplicates()
        
        try:
            BaseAliq['Valor_Atualizado']=BaseAliq['Valor_Atualizado'].str.replace(",",".").astype(float)
        except:
            pass
        
        BaseAliq['Data_Vencimento']=pd.to_datetime(BaseAliq['Data_Vencimento'],dayfirst=True)
        
        # LiquidadoEquipeMerge=BaseLiq.groupby('colaborador',as_index=False).agg({'valor_liquidado':'sum','EQUIPE':'first', 'REPORTE':'first'})

        # LiquidadoEquipeMerge=LiquidadoEquipeMerge.sort_values(by='valor_liquidado',ascending=False)

        # LiquidadoEquipeMerge['RANK'] = LiquidadoEquipeMerge['valor_liquidado'].rank(method='dense', ascending=False).astype(int)

        metas['Mes']=metas['Mês'].dt.month
        metas['Ano']=metas['Mês'].dt.year
        metasFiltro=metas.loc[(metas['Mes']==mesNum) & (metas['Ano']==anoLiq)]

        MetaLiq=list(metasFiltro['Meta_geral'])[0]
        MetaTele=list(metasFiltro['Meta_Tele'])[0]
        Metaindividual=list(metasFiltro['Meta_Individual'])[0]
        MetaindividualTele=list(metasFiltro['Meta_Individual_Tele'])[0]
   
        dias_uteis=dias_uteis_no_mes(anoLiq, mesNum)
        dias_uteis_falta=dias_uteis_que_faltam(mesNum)

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
        
        DfEqpFiltro,qtdeColabs = exibeEquipe(BaseLiq,colaborador, optionsEqp, optionsRpt)
        
        totalLiq=DfEqpFiltro['valor_liquidado'].sum()

        percentual_falta = (((totalLiq - MetaLiq) / MetaLiq) * 100)
        percentual_atingido=(totalLiq/MetaLiq) * 100
        # Dados de exemplo: datas e valores de liquidação diária

        BaseAliqEquipe=BaseAliq.loc[(BaseAliq['EQUIPE']==optionsEqp)]
        aLiquidar=BaseAliqEquipe['Valor_Original'].sum()

    if optionsEqp=='Telecobrança':
        MetaLiq=MetaTele
        percentual_falta = (((totalLiq - MetaLiq) / MetaLiq) * 100)
        percentual_atingido=(totalLiq/MetaLiq) * 100
        Metaindividual=MetaindividualTele

    def criaImagem(valor,label,imagem,Delta=0,t=0,r=0,b=0,l=0,width=250,height=160):

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
                font-size: 20px;
                color: rgb(204, 186, 186);
                # text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.7);
                text-align: center;
                margin:10px 0px 0px 0px;
            }}
            .metric-label {{
                font-size: 15px;
                display: block; /* Faz o texto ocupar uma linha inteira */
                # margin-bottom: -29px; /* Ajuste o valor negativo para controlar o espaçamento */
                margin:5px 0px -14px 0px;
            }}
            .metric-delta {{
                font-size: 15px;
                # text-align: center;
                color: rgb(0,255,0);
                display: block; /* Faz o texto ocupar uma linha inteira */
                margin:-14px 0px 5px 0px; /* Ajuste o valor negativo para controlar o espaçamento */
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

    if user_info[2]=="ADMIN":
        tab1, tab2,tab3 = st.tabs(["Home", "Equipe","Adm. Equipe"])
    else:
        tab1, tab2 = st.tabs(["Home", "Equipe"])

    with tab1:
        col1, col2, col3, col4,col5,col6= st.columns([2,2,2,2,2,2])

        with col1:
            label="Dias de Trabalho"
            criaImagem(dias_uteis,label,"fundoAzul.jpeg",f"Faltam {dias_uteis_falta} dias")
                # st.metric(label="Dias Úteis", value=f"{dias_uteis}",delta=f"-faltam {dias_uteis_falta} dias",delta_color='inverse')            

        with col2:
            label="Meta Liquidado"
            M=f"R${MetaLiq:,.0f}".replace(',', '.')
            D=f"{percentual_falta:.2f}% {'' if percentual_falta<0 else 'Meta atingida'}"
            criaImagem(M,label,"fundoAzul.jpeg",D,b=20)
            # st.metric(label="Meta Liquidado", value=f"R${MetaLiq:,.0f}".replace(',', '.'), delta=f"{percentual_falta:.0f}% {'Para atingir meta' if percentual_falta<0 else 'Meta atingida'}")

        with col3:
            diaHj=dt.datetime.now().date().strftime("%d/%m/%Y")
            liq=f"R${totalLiq:,.0f}".replace(',', '.')
            D=f"{percentual_atingido:.0f}%"
            label="Total Liquidado"
            criaImagem(liq,label,"fundoAzul.jpeg",D,b=20)
            # with st.container(border=True): 
            # criaGrafico(dias,valores,color1,color2,totalLiq,percentual_atingido)
            # st.metric(label=f"Liquidado até {diaHj}", value=f"R${totalLiq:,.0f}".replace(',', '.'),delta=f"{percentual_atingido:.0f}% Atingido Meta")
                
        with col4:
            metaDia=MetaLiq/dias_uteis
            deltaMeta=f"{((totalLiq/dias_uteis)-metaDia)/metaDia:,.2f}%".replace(',', '.')
            valorDefSup=totalLiq-(MetaLiq/dias_uteis)*(dias_uteis-dias_uteis_falta)
            defsup=f"{valorDefSup:,.2f}".replace(",",";").replace(".",",").replace(";",".")
            label="Meta Diária"

            criaImagem(f"R${metaDia:,.0f}".replace(',', '.'),label,"fundoAzul.jpeg",f"{deltaMeta}",b=20)

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
            criaImagem(value,label,"fundoAzul.jpeg",delta,b=20)

            # with st.container(border=True): 
            #     st.metric(label="Déficit/Superávit", value=f"R${valorDefSup:,.0f}".replace(',', '.'),delta=f"{'Superávit' if valorDefSup>0 else '-Déficit'}")
        with col6:

            Delta=(aLiquidar/MetaLiq)*100
            label=f"A Liquidar".replace(',', '.')
            criaImagem(f"R${aLiquidar:,.0f}",label,"fundoAzul.jpeg",f"{Delta:.2f}%",b=20)

        col1, col2 = st.columns([2,2])
        with col1:
            #GRÁFICO PARA MOSTRAR LIQUIDADO POR DIA
            # Calcula a liquidação acumulada
            LiqPordia=DfEqpFiltro.groupby(['data_liquidacao'],as_index=False).agg({'valor_liquidado':'sum'})
            LiqPordia['Liquidação Acumulada'] = LiqPordia['valor_liquidado'].cumsum()

            # with st.container(border=True):
            # Função para formatar números em formato curto
            def format_number_short(value):
                if value >= 1_000_000:
                    return f'{value / 1_000_000:.1f}M'
                elif value >= 1_000:
                    return f'{value / 1_000:.1f}k'
                else:
                    return str(value)
                
            x = LiqPordia['data_liquidacao']
            y = LiqPordia['valor_liquidado']
            
            labels = [format_number_short(value) for value in y]
            linha_meta = np.full(len(x), metaDia)
            
            #Gráfico de área
            fig = go.Figure(go.Scatter(x=x, y=y, name="Liquidado",
                                line_shape='linear',mode='lines+markers',fill='tozeroy', 
                                fillcolor='rgba(106,90,205, 0.2)',showlegend=False
                                ))
            # Adicione anotações para os rótulos de dados
            for i, txt in enumerate(y):
                fig.add_annotation(
                    x=x[i],
                    y=y[i],
                    text=str(format_number_short(txt)),  # Convertendo o valor para string, se necessário
                    showarrow=False,
                    textangle=-70,  # Ângulo de rotação do texto
                    xanchor='center',
                    yanchor='bottom',
                    font=dict(size=12, color="rgba(255,250,250, 0.5)")
                )
            #Linha de meta
            fig.add_trace(go.Scatter(x=x, y=linha_meta,mode='lines',
            line=dict(color='Red', width=2, dash='dashdot'),
            opacity=0.5,
            name='Meta Diaria'),
            )
            
            fig.add_annotation(
                x=x.iloc[0],
                y=metaDia,
                text=f"{metaDia:,.2f}".replace(",","."),
                showarrow=False,
                yshift=10,
                font=dict(
                    color="Red",
                    size=12
                )
            )
            
            fig.update_layout(title="Liquidação por dia X Meta Dia",height=350,margin=dict(l=60, r=20, t=80, b=60),plot_bgcolor="rgba(128,128,128,0.1)",paper_bgcolor="rgba(128,128,128,0.1)",showlegend=False)

            st.plotly_chart(fig, use_container_width=True,meta=f"{metaDia}")

        with col2:
            
            #GRÁFICO PARA MOSTRAR LIQUIDADO POR EQUIPE
            LiqPorEquipe=DfEqpFiltro.query("@DfEqpFiltro['REPORTE']!='MARCOS'")
            LiqPorEquipe=LiqPorEquipe.groupby(['REPORTE'],as_index=False).agg({'valor_liquidado':'sum'}).sort_values(by='valor_liquidado',ascending=False)

            # Função para formatar números em formato curto
            
            def format_number_short(value):
                if value >= 1_000_000:
                    return f'{value / 1_000_000:.1f}M'
                elif value >= 1_000:
                    return f'{value / 1_000:.1f}k'
                else:
                    return str(value)

            x = LiqPorEquipe['REPORTE']
            y = LiqPorEquipe['valor_liquidado']
            labels = [format_number_short(value) for value in y]
            # linha_meta = np.full(len(x), MetaLiq)

            # x2 = LiqPordiaOn['data_liquidacao']
            # y2 = LiqPordiaOn['Liquidação Acumulada']
            # labels = [format_number_short(value) for value in y]

            # Criação dos traços do gráfico
            data = [
                go.Bar(x=x, y=y, name="Liquidado Equipe"),
            ]
            
            # Layout do gráfico
            layout = go.Layout(
                title="Liquidação Por Equipe",
                height=350,
                margin=dict(l=60, r=20, t=80, b=60),
                plot_bgcolor="rgba(128,128,128,0.1)",
                paper_bgcolor="rgba(128,128,128,0.1)",
                showlegend=False,
            )

            #Gráfico de área
            fig = go.Figure(data=data, layout=layout)

            # # Adicione anotações para os rótulos de dados
            for i, txt in enumerate(y):
                fig.add_annotation(
                    print(y.index),
                    x=x[i],
                    y=y[i],
                    text=str(format_number_short(txt)), 
                    showarrow=False,
                    textangle=-70,
                    xanchor='center',
                    yanchor='bottom',
                    # yshift=35,
                    font=dict(size=12, color="rgba(255,250,250, 0.5)")
                )

            st.plotly_chart(fig, use_container_width=True,meta=f"{metaDia}")
        
        col1,col2=st.columns([6,3])

        with col1:
            #GRÁFICO PARA MOSTRAR LIQUIDADO ACUMULADO POR DIA
            LiqPordiaGer=DfEqpFiltro.query("@DfEqpFiltro['colaborador']!='Acordo Online'").groupby(['data_liquidacao'],as_index=False).agg({'valor_liquidado':'sum'})
            LiqPordiaGer['Liquidação Acumulada']=LiqPordiaGer['valor_liquidado'].cumsum()
            LiqPordiaOn=BaseLiq.query("@BaseLiq['colaborador']=='Acordo Online'").groupby(['data_liquidacao'],as_index=False).agg({'valor_liquidado':'sum'})
            LiqPordiaOn['Liquidação Acumulada']=LiqPordiaOn['valor_liquidado'].cumsum()
            # with st.container(border=True):
            # Função para formatar números em formato curto

            def format_number_short(value):
                if value >= 1_000_000:
                    return f'{value / 1_000_000:.1f}M'
                elif value >= 1_000:
                    return f'{value / 1_000:.1f}k'
                else:
                    return str(value)

            x = LiqPordiaGer['data_liquidacao']
            y = LiqPordiaGer['Liquidação Acumulada']
            labels = [format_number_short(value) for value in y]
            linha_meta = np.full(len(x), MetaLiq)

            x2 = LiqPordiaOn['data_liquidacao']
            y2 = LiqPordiaOn['Liquidação Acumulada']
            labels = [format_number_short(value) for value in y]

            # Criação dos traços do gráfico
            if optionsEqp!='Telecobrança':
                data = [
                    go.Bar(x=x, y=y, name="Liquidado Equipe"),
                    go.Bar(name='Acordo Online', x=x2, y=y2),
                ]
            else:
                data = [
                    go.Bar(x=x, y=y, name="Liquidado Equipe"),
                ]
            
            # Layout do gráfico
            layout = go.Layout(
                title="Liquidação Acumulada por dia",
                height=350,
                margin=dict(l=60, r=20, t=80, b=60),
                plot_bgcolor="rgba(128,128,128,0.1)",
                paper_bgcolor="rgba(128,128,128,0.1)",
                showlegend=True,
                barmode='stack',
            )

            # st.plotly_chart(fig, use_container_width=True,meta=f"{metaDia}")

            #Gráfico de área
            fig = go.Figure(data=data, layout=layout)

            try:
                if optionsEqp!='Telecobrança':
                    # Adicione anotações para os rótulos de dados
                    for i, txt in enumerate(y+y2):
                        fig.add_annotation(
                            x=x2[i],
                            y=y[i]+y2[i],
                            text=str(format_number_short(txt)), 
                            showarrow=False,
                            textangle=-70,
                            xanchor='center',
                            yanchor='top',
                            yshift=35,
                            font=dict(size=12, color="rgba(255,250,250, 0.5)")
                        )
                else:
                    for i, txt in enumerate(y):
                        fig.add_annotation(
                            x=x2[i],
                            y=y[i],
                            text=str(format_number_short(txt)), 
                            showarrow=False,
                            textangle=-70,
                            xanchor='center',
                            yanchor='top',
                            yshift=35,
                            font=dict(size=12, color="rgba(255,250,250, 0.5)")
                        )
            except:              
                for i, txt in enumerate(y):
                    fig.add_annotation(
                        x=x[i],
                        y=y[i],
                        text=str(format_number_short(txt)), 
                        showarrow=False,
                        textangle=-70,
                        xanchor='center',
                        yanchor='top',
                        yshift=35,
                        font=dict(size=12, color="rgba(255,250,250, 0.5)")
                    )
            fig.add_trace(go.Scatter(x=x, y=linha_meta,mode='lines',
            line=dict(color='Red', width=2, dash='dashdot'),
            opacity=0.5,
            name='Meta'),
            )

            fig.add_annotation(
                x=x.iloc[0],
                y=MetaLiq,
                text=f"{MetaLiq:,.0f}".replace(",","."),
                showarrow=False,
                yshift=10,
                font=dict(
                    color="Red",
                    size=12
                )
            )

            st.plotly_chart(fig, use_container_width=True,meta=f"{MetaLiq}")

        with col2:
            labels = ['Liquidado', 'A_Liquidar', 'Falta_Meta']
            values = [DfEqpFiltro['valor_liquidado'].sum(), BaseAliqEquipe['Valor_Original'].sum(), MetaLiq - DfEqpFiltro['valor_liquidado'].sum()]

            color_discrete_map = {
                'Liquidado': 'lightgreen',
                'A_Liquidar': 'gold',
                'Falta_Meta': 'red'
            }

            # Create a list of colors based on the mapping
            colors = [color_discrete_map[label] for label in labels]

            fig = go.Figure(data=[go.Pie(
                labels=labels, 
                values=values, 
                hole=.3,
                marker_colors=colors,
                opacity=0.9,
                marker=dict(
                line=dict(color='white', width=2)
            )  # Pass the list of colors here
            )])

            st.plotly_chart(fig, use_container_width=True)
            
    with tab2:

        col1, col2, col3, col4,col5,col6= st.columns([2,2,2,2,2,2])

        with col1:
            label="Dias de Trabalho"
            criaImagem(dias_uteis,label,"fundoAzul.jpeg",f"Faltam {dias_uteis_falta} dias")

        with col2:
            label="Meta Liquidado"
            M=f"R${float(Metaindividual):,.0f}".replace(',', '.')
            # D=f"{percentual_falta:.2f}% {'' if percentual_falta<0 else 'Meta atingida'}"
            criaImagem(M,label,"fundoAzul.jpeg",b=20)

        col1,col2,col3=st.columns([3,4,1])
        
        with col1:
            liqColab=DfEqpFiltro.query("@DfEqpFiltro['colaborador']!='Acordo Online' and @DfEqpFiltro['SIT_ATUAL']!='INATIVO' and (@DfEqpFiltro['CARGO']=='ASSISTENTE' or @DfEqpFiltro['CARGO']=='ASSISTENTE_TELE')").groupby(['colaborador'],as_index=False).agg({'valor_liquidado':'sum'})

            receberColab=BaseAliqEquipe.query("@BaseAliqEquipe['Criado_Por']!='Acordo Online' and @BaseAliqEquipe['Parcela']!=1 and @BaseAliqEquipe['SIT_ATUAL']!='INATIVO' and (@BaseAliqEquipe['CARGO']=='ASSISTENTE' or @BaseAliqEquipe['CARGO']=='ASSISTENTE_TELE')").groupby(['Criado_Por'],as_index=False).agg({'Valor_Original':'sum'})

            liqEquipeMerge=liqColab.merge(receberColab,left_on='colaborador',right_on='Criado_Por',how='left').sort_values(by='valor_liquidado',ascending=True)
            # st.dataframe(liqEquipeMerge)

            linha_meta = np.full(len(x), Metaindividual)
            # Carrega a imagem
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=liqEquipeMerge['colaborador'],
                x=liqEquipeMerge['valor_liquidado'],
                orientation='h',
                name="Liquidado",
                marker=dict(
                    color='rgba(0,0,255, 0.6)',
                    line=dict(color='rgba(0,0,255, 1.0)', width=2)
                )
            ))
            fig.add_trace(go.Bar(
                y=liqEquipeMerge['colaborador'],
                x=liqEquipeMerge['Valor_Original'],
                orientation='h',
                name="A_Liquidar",
                marker=dict(
                    color='rgba(58, 71, 80, 0.6)',
                    line=dict(color='rgba(58, 71, 80, 1.0)', width=2)
                )
            ))

            fig.update_layout(barmode='stack',height=900,
                              width=1200,
                              margin=dict(l=50, r=50, t=100, b=100),
                              shapes=[
                                    dict(
                                        type='line',
                                        yref='paper', y0=0, y1=1,  
                                        xref='x', x0=Metaindividual, x1=Metaindividual,
                                        line=dict(color="Red", width=2, dash="dash")
                                    )
                                ],
                                annotations=[
                                            dict(
                                                x=Metaindividual,
                                                y=1.00,  # Ajuste a posição vertical da anotação
                                                xref="x",
                                                yref="paper",
                                                text=f"Meta: {float(Metaindividual):.2f}",  # Texto da anotação
                                                showarrow=True,
                                                arrowhead=7,
                                                ax=0,
                                                ay=-40  # Ajuste o comprimento da seta
                                            )
            ])

            st.plotly_chart(fig, use_container_width=True)
        with col2:
            
            tabelaLiq=DfEqpFiltro.query("@DfEqpFiltro['colaborador']!='Acordo Online' and @DfEqpFiltro['SIT_ATUAL']!='INATIVO' and (@DfEqpFiltro['CARGO']=='ASSISTENTE' or @DfEqpFiltro['CARGO']=='ASSISTENTE_TELE')").groupby('colaborador',as_index=False)['valor_liquidado'].sum()

            tabelaAliq=BaseAliqEquipe.query("@BaseAliqEquipe['Criado_Por']!='Acordo Online' and @BaseAliqEquipe['Parcela']!=1 and @BaseAliqEquipe['SIT_ATUAL']!='INATIVO' and (@BaseAliqEquipe['CARGO']=='ASSISTENTE' or @BaseAliqEquipe['CARGO']=='ASSISTENTE_TELE')").groupby('Criado_Por',as_index=False)['Valor_Original'].sum()

            cobranca_geral=tabelaLiq.merge(tabelaAliq,left_on='colaborador',right_on='Criado_Por',how='left').drop(columns='Criado_Por')
            
            cobranca_geral['RANK'] = cobranca_geral['valor_liquidado'].rank(method='dense', ascending=False).astype(int)

            cobranca_geral=cobranca_geral[['RANK','colaborador','valor_liquidado','Valor_Original']]
            # metaDiaria=metaDia
            # diasPassados=(dias_uteis-dias_uteis_falta)

            # cobranca_geral['valorPcolab']=cobranca_geral.groupby('colaborador')['valor_liquidado'].transform(sum)

            # cobranca_geral['RANK'] = cobranca_geral['valorPcolab'].rank(method='dense', ascending=False).astype(int)
            # # st.dataframe(cobranca_geral)

            # # agroupTab=cobranca_geral.groupby('REPORTE')[['Nome_Colaborador','Valor Liquidado']].agg({'Nome_Colaborador':'first','Valor Liquidado':'sum'})
            # # cobranca_geral['RANK']=range(1,len(cobranca_geral['Nome_Colaborador'])+1)
            # mes=dt.datetime.now().month
            # if len(cobranca_geral[cobranca_geral['Valor_Original'].isna()])==len(cobranca_geral) or mesNum < mes:
            #     cobranca_geral['Valor_Original']=0
            # try:
            #     agroupTab = cobranca_geral.pivot_table(index=['RANK','REPORTE','colaborador','Valor_Original'], values='valor_liquidado', aggfunc='sum').reset_index().sort_values(by='valor_liquidado',ascending=False)

            # except:
                
            #     agroupTab=cobranca_geral[['RANK','REPORTE','colaborador','valor_liquidado','Valor_Original']]
            #     print(agroupTab['Valor_Original'], 'Baixo')

            # agroupTab['% Atingido Meta']=agroupTab['valor_liquidado'].apply(lambda x:f"{x/Metaindividual*100:.2f}%")

            # # agroupTab['RANK']=range(1,len(agroupTab['Nome_Colaborador'])+1)

            # agroupTab['Meta Diária']=f"R${metaDiaria:,.2f}".replace(",",";").replace(".",",").replace(";",".")

            # if diasPassados ==0:
            #     diasPassados=1

            # dados_dias_anteriores = liqEquipeMerge[liqEquipeMerge['data_liquidacao'].dt.day < diaHj]

            # media_por_colaborador_dia = dados_dias_anteriores.groupby('colaborador',as_index=False)['valor_liquidado'].mean()
    
            # agroupTab['Realizado por Dia (Média)'] = (agroupTab['valor_liquidado']-media_por_colaborador_dia['valor_liquidado'])/(diasPassados-1)

            # agroupTab['Déficit/Superávit Diário']=agroupTab['Realizado por Dia (Média)'].apply(lambda x:f"R${(x-metaDiaria):,.2f}".replace(",",";").replace(".",",").replace(";","."))  

            # agroupTab['Realizado por Dia (Média)']=agroupTab['Realizado por Dia (Média)'].apply(lambda x: f"R${x:,.2f}".replace(",",";").replace(".",",").replace(";","."))

            # agroupTab['Realizado Total']=agroupTab['valor_liquidado'].apply(lambda x: f"R${x:,.2f}".replace(",",";").replace(".",",").replace(";","."))

            # agroupTab['Falta']=agroupTab['valor_liquidado'].apply(lambda x: f"R${x-Metaindividual:,.2f}".replace(",",";").replace(".",",").replace(";","."))

            # agroupTab['% Falta']=agroupTab['valor_liquidado'].apply(lambda x:f"{(x/Metaindividual*100)-100:.2f}%")
            
            # agroupTab['Déficit/Superávit Total']=agroupTab['Déficit/Superávit Diário'].apply(lambda x: f"R${float(x.replace('R$','').replace('.','').replace(',','.'))*(diasPassados-1):,.2f}".replace(",",";").replace(".",",").replace(";","."))

            # agroupTab['Receber']=agroupTab['Valor_Original'].apply(lambda x: f"R${x:,.2f}".replace(",",";").replace(".",",").replace(";","."))
            # # agroupTab['PREVISÃO_META']=agroupTab['Realizado Total']+agroupTab['A Receber']
            # # Função para verificar se a meta foi batida
            # def verificar_meta(row):
            #     if row['valor_liquidado'] >= Metaindividual:
            #         return 'Meta Batida'
            #     elif (row['valor_liquidado']+ row['Valor_Original']) >= Metaindividual:
            #         return 'Pode Bater Meta'
            #     elif (row['valor_liquidado']+ row['Valor_Original']+(dias_uteis_falta*metaDiaria)) >= Metaindividual:
            #         return 'Chance de bater a meta'
            #     else:
            #         return 'Não irá bater Meta'
                
            # agroupTab['Resultado']=agroupTab.apply(verificar_meta, axis=1)


            # agroupTab=agroupTab[['RANK','REPORTE','colaborador','Realizado Total','% Atingido Meta','Falta','% Falta','Meta Diária','Realizado por Dia (Média)','Déficit/Superávit Diário','Déficit/Superávit Total','Receber','Resultado']]
            
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
            st.dataframe(cobranca_geral, hide_index=True, height=800, width=1100,use_container_width=True)

    if user_info[2]=="ADMIN":
        with tab3:
            def inserir_dados(Ru, nome,email, cargo,avancado, equipe,matricula=None,img_byte_arr=None):
                try:
                    conn = connect()
                    cursor = conn.cursor()
                    sql = "INSERT INTO sua_tabela (ru, matricula, nome, email, cargo, avancado, equipe, foto) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                    val = (Ru, matricula, nome, email, cargo, avancado, equipe, img_byte_arr)
                    cursor.execute(sql, val)
                    conn.commit()
                    st.success("Dados inseridos com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao inserir dados: {e}")
                finally:
                    conn.close()

            col1,col3 =st.columns([4,4])

            with col1:
                st.title("Cadastro de Colaborador")

                # Formulário
                with st.form(key="form_cadastro"):
                    col1, col2 = st.columns(2)  # Divide o formulário em duas colunas

                    with col1:
                        Ru = st.text_input("RU")
                        matricula = st.text_input("Matrícula")
                        nome = st.text_input("Nome Colaborador")
                        email = st.text_input("E-mail")
                        cargo = st.selectbox("Cargo", ['ADVOGADO', 'ANALISTA', 'ASSISTENTE', 'ASSISTENTE_TELE', 'AVANÇADO', 'AVANÇADO TELE', 'GESTOR', 'MONITOR'])
                        avancado = st.selectbox('Responsável', Reporte)
                        equipe = st.selectbox('Equipe', Equipe)

                    with col2:
                        uploaded_file = st.file_uploader("Escolha uma imagem...", type=["jpg", "jpeg", "png"])
                        if uploaded_file is not None:
                            image = Image.open(uploaded_file)
                            # Redimensionando a imagem (opcional)
                                        # Pré-visualização da imagem
                            max_width = 300  # Largura máxima para a foto do perfil
                            max_height = 300  # Altura máxima para a foto do perfil
                            image.thumbnail((max_width, max_height))
                            st.image(image, caption='Imagem Redimensionada', use_column_width=True)

                    if st.form_submit_button("Cadastrar"):
                        # Convertendo a imagem para BLOB (se houver imagem)
                        img_byte_arr = None
                        if uploaded_file:
                            img_byte_arr = io.BytesIO()
                            image.save(img_byte_arr, format=image.format)
                            img_byte_arr = img_byte_arr.getvalue()

                        inserir_dados(Ru, nome,email, cargo,avancado, equipe,matricula,img_byte_arr)  # Passa a imagem como argumento
            with col3:
                st.title("Atualizar Colaborador")
                def atualizar_registros(conn, df_original, df_editado):
                    cursor = conn.cursor()

                    # Iterar sobre os registros e comparar os dados editados com os dados originais
                    for index, row_editado in df_editado.iterrows():
                        row_original = df_original.loc[index]
                        if not row_editado.equals(row_original):
                            
                            # Se os dados editados forem diferentes dos dados originais, atualizar o registro no banco de dados
                            sql1 = f"""
                            UPDATE Equipe_Completa
                            SET SIT_ATUAL = %s
                            WHERE RU = %s  -- Substitua "RU" pela chave primária da sua tabela
                            """
                            values = (row_editado['SIT_ATUAL'], row_editado['RU'])  # Ajuste conforme suas colunas
                            cursor.execute(sql1, values)
                            conn.commit()

                            sql2 = f"""
                            UPDATE Equipe_Completa
                            SET DATA_RETORNO = %s
                            WHERE RU = %s  -- Substitua "RU" pela chave primária da sua tabela
                            """
                            values = (row_editado['DATA_RETORNO'], row_editado['RU'])  # Ajuste conforme suas colunas
                            cursor.execute(sql2, values)
                            conn.commit()

                            sql3 = f"""
                            UPDATE Equipe_Completa
                            SET CARGO = %s
                            WHERE RU = %s  -- Substitua "RU" pela chave primária da sua tabela
                            """
                            values = (row_editado['CARGO'], row_editado['RU'])  # Ajuste conforme suas colunas
                            cursor.execute(sql3, values)
                            conn.commit()

                            sql4 = f"""
                            UPDATE Equipe_Completa
                            SET REPORTE = %s
                            WHERE RU = %s  -- Substitua "RU" pela chave primária da sua tabela
                            """
                            values = (row_editado['REPORTE'], row_editado['RU'])  # Ajuste conforme suas colunas
                            cursor.execute(sql4, values)
                            conn.commit()

                            sql5 = f"""
                            UPDATE Equipe_Completa
                            SET EQUIPE = %s
                            WHERE RU = %s  -- Substitua "RU" pela chave primária da sua tabela
                            """
                            values = (row_editado['EQUIPE'], row_editado['RU'])  # Ajuste conforme suas colunas
                            cursor.execute(sql5, values)
                            conn.commit()

                # Função para carregar os dados do banco de dados
                def load_data(conn):
                    query = 'SELECT RU,MATRICULA, Nome_Colaborador, CARGO, REPORTE, EQUIPE, SIT_ATUAL, DATA_RETORNO,ANIVERSARIO,EMAIL FROM Equipe_Completa'
                    return pd.read_sql(query, conn)

                # Função principal
                def run():
                    # Conectar ao banco de dados
                    conn = connect()

                    # Carregar dados do banco de dados
                    baseCompleta = load_data(conn)

                    Situacao=['ATIVO','ATESTADO','FÉRIAS','FOLGA','FOLGA_ANIVERSÁRIO','AFASTADO','FALTOU','INATIVO','TREINAMENTO']
                    Situacao.insert(0,'TODOS')
                    Equipe=list(baseCompleta['EQUIPE'].unique())
                    Equipe.insert(0,'TODOS')
                    Reporte=list(baseCompleta['REPORTE'].unique())
                    Reporte.insert(0,'TODOS')
                    # Exibir barra lateral para seleção de filtros
                    if tab3.select:
                        optionsSit = st.sidebar.selectbox('Selecione a Situação desejada', Situacao)

                        # Filtrar dados conforme seleção
                        DfEqpFiltro = baseCompleta.copy()
                        if optionsSit != 'TODOS':
                            DfEqpFiltro = DfEqpFiltro[DfEqpFiltro['SIT_ATUAL'] == optionsSit]
                        if optionsEqp != 'TODOS':
                            DfEqpFiltro = DfEqpFiltro[DfEqpFiltro['EQUIPE'] == optionsEqp]
                        if optionsRpt != 'TODOS':
                            DfEqpFiltro = DfEqpFiltro[DfEqpFiltro['REPORTE'] == optionsRpt]
                    
                        qtdeColabs=len(DfEqpFiltro)

                        DfEqpFiltro = DfEqpFiltro.query("SIT_ATUAL != 'INATIVO'")
                        qtdAtivos = len(DfEqpFiltro[DfEqpFiltro['SIT_ATUAL'] == 'ATIVO'])
                        dif = qtdAtivos - qtdeColabs
                        total_colab_metric = st.sidebar.metric("Total de Colaboradores", qtdeColabs, dif)
                        ativos_metric = st.sidebar.metric("Ativos", value=qtdAtivos)

                        # col1,col2,col3=st.columns([2,7,1])
                        # with col2:
                        with st.container(height=660):
                            edited_df=st.data_editor(DfEqpFiltro[['RU','Nome_Colaborador','CARGO','REPORTE','EQUIPE','SIT_ATUAL','DATA_RETORNO']],
                                                        hide_index=True,
                                                        column_config={
                                                            "SIT_ATUAL": st.column_config.SelectboxColumn(
                                                                "SIT. ATUAL",
                                                                help="Situação do Colaborador",
                                                                width="900px",
                                                                options=Situacao[1:],
                                                                required=True,
                                                            )        
                                                        },height=550

                                                        )
                        
                            atualizar = st.button('ATUALIZAR',type="primary")

                        if atualizar and len(edited_df)>0:
                            # Carregar dados originais novamente
                            baseCompleta_original = load_data(conn)

                            # Atualizar registros modificados
                            atualizar_registros(conn, baseCompleta_original, edited_df)

                            # Fechar conexão
                            conn.close()
                            st.success('Atualizado com sucesso!', icon="✅")
                    else:
                        pass
                run()
    else:
        pass    # image = Image.open("imagem_meta.jpg")
        # draw = ImageDraw.Draw(image)

        # # Desenha anotações (exemplo: um círculo e texto)
        # draw.ellipse((100, 100, 200, 200), outline="red", width=2)
        # font = ImageFont.truetype("arial.ttf", 24)  # Use uma fonte disponível
        # draw.text((120, 150), "Anotação", fill="red", font=font)

        # # Exibe a imagem no Streamlit
        # st.image(image, caption="Imagem com Anotações")

