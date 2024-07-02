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
      
        BaseLiq=import_bases('view_CobrancaGeral',mesNum,coluna='data_liquidacao')
        BaseAliq=import_bases('Areceber',mes=mesNum)
        
        BaseLiq=BaseLiq.drop_duplicates()
        
        try:
            BaseAliq['Valor Original']=BaseAliq['Valor Original'].str.replace(",",".").astype(float)
        except:
            pass
        
        BaseAliq['Data Vencimento']=pd.to_datetime(BaseAliq['Data Vencimento'],dayfirst=True)

        aliqcolabs=BaseAliq[BaseAliq['Parcela']==1]

        aliqcolabs=aliqcolabs.groupby('Criado Por',as_index=False)['Valor Original'].sum()

        aliqcolabs=aliqcolabs.rename(columns={'Valor Original':'A Receber'})
        
        BaseaLiqmes=BaseAliq[BaseAliq['Data Vencimento'].dt.month==mesNum]

        BaseAliqMetas=BaseaLiqmes[BaseaLiqmes['Parcela']==1]

        BaseAliqMetas=BaseAliqMetas.rename(columns={'Valor Original':'A Receber'})
        
        LiquidadoEquipeMerge=BaseLiq.groupby('colaborador',as_index=False).agg({'valor_liquidado':'sum','EQUIPE':'first', 'REPORTE':'first'})

        LiquidadoEquipeMerge=LiquidadoEquipeMerge.sort_values(by='valor_liquidado',ascending=False)

        LiquidadoEquipeMerge['RANK'] = LiquidadoEquipeMerge['valor_liquidado'].rank(method='dense', ascending=False).astype(int)

        metas=import_bases('metas_cobranca_geral')
        metas['Mes']=metas['Mês'].dt.month
        metas['Ano']=metas['Mês'].dt.year
        metasFiltro=metas.loc[(metas['Mes']==mesNum) & (metas['Ano']==anoLiq)]
        MetaLiq=list(metasFiltro['Meta_geral'])[0]
        MetaTele=list(metasFiltro['Meta_Tele'])[0]
        Metaindividual=list(metasFiltro['Meta_Individual'])[0]
 
        MetaindividualTele=list(metasFiltro['Meta_Individual_Tele'])[0]
   
        dias_uteis=dias_uteis_no_mes(anoLiq, mesNum)
        dias_uteis_falta=dias_uteis_que_faltam(mesNum)

        feriadosDF=import_bases('feriados')

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

        aLiquidar=BaseAliqMetas['A Receber'].sum()
        
        LiqPordia=DfEqpFiltro.groupby(['data_liquidacao'],as_index=False).agg({'valor_liquidado':'sum'})

        percentual_falta = (((totalLiq - MetaLiq) / MetaLiq) * 100)
        percentual_atingido=(totalLiq/MetaLiq) * 100
        # Dados de exemplo: datas e valores de liquidação diária

        # Calcula a liquidação acumulada
        LiqPordia['Liquidação Acumulada'] = LiqPordia['valor_liquidado'].cumsum()
        
    if optionsEqp=='Telecobrança':
        MetaLiq=MetaTele
        percentual_falta = (((totalLiq - MetaLiq) / MetaLiq) * 100)
        percentual_atingido=(totalLiq/MetaLiq) * 100
    def criaImagem(valor,Delta,label,imagem,t=0,r=0,b=0,l=0,width=250,height=160):

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

    tab1, tab2 = st.tabs(["Home", "Tele"])

    with tab1:
        col1, col2, col3, col4,col5,col6= st.columns([2,2,2,2,2,2])

        with col1:
            label="Dias de Trabalho"
            criaImagem(dias_uteis,f"Faltam {dias_uteis_falta} dias",label,"fundoAzul.jpeg")
                # st.metric(label="Dias Úteis", value=f"{dias_uteis}",delta=f"-faltam {dias_uteis_falta} dias",delta_color='inverse')            

        with col2:
            label="Meta Liquidado"
            M=f"R${MetaLiq:,.0f}".replace(',', '.')
            D=f"{percentual_falta:.2f}% {'' if percentual_falta<0 else 'Meta atingida'}"
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

        col1, col2 = st.columns([2,2])
        with col1:
            #GRÁFICO PARA MOSTRAR LIQUIDADO POR DIA

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
            # LiqPorEquipe=LiqPorEquipe.query("@LiqPorEquipe['REPORTE']!='MARCOS'")
            # LiqPorEquipe=LiqPorEquipe.loc[LiqPorEquipe['REPORTE']!='MARCOS']
            # LiqPorEquipe['Liquidação Acumulada']=LiqPorEquipe.groupby('colaborador')['valor_liquidado'].cumsum()
            # with st.container(border=True):
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

            # # x2 = LiqPordiaOn['data_liquidacao']
            # # y2 = LiqPordiaOn['Liquidação Acumulada']
            # # labels = [format_number_short(value) for value in y]

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
            LiqPordiaOn=DfEqpFiltro.query("@DfEqpFiltro['colaborador']=='Acordo Online'").groupby(['data_liquidacao'],as_index=False).agg({'valor_liquidado':'sum'})
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
            data = [
                go.Bar(x=x, y=y, name="Liquidado Equipe"),
                go.Bar(name='Acordo Online', x=x2, y=y2)
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

            #Gráfico de área
            fig = go.Figure(data=data, layout=layout)

            try:
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

            st.plotly_chart(fig, use_container_width=True,meta=f"{metaDia}")
        with col2:
            labels = ['Liquidado','A_Liquidar']
            values = [DfEqpFiltro['valor_liquidado'].sum(), BaseAliq['Valor Original'].sum()]

            # Use `hole` to create a donut-like pie chart
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
            st.plotly_chart(fig, use_container_width=True)
            
    with tab2:        
        # Carrega a imagem
        pass
        # image = Image.open("imagem_meta.jpg")
        # draw = ImageDraw.Draw(image)

        # # Desenha anotações (exemplo: um círculo e texto)
        # draw.ellipse((100, 100, 200, 200), outline="red", width=2)
        # font = ImageFont.truetype("arial.ttf", 24)  # Use uma fonte disponível
        # draw.text((120, 150), "Anotação", fill="red", font=font)

        # # Exibe a imagem no Streamlit
        # st.image(image, caption="Imagem com Anotações")

