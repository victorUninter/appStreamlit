import streamlit as st
import pandas as pd
from pandas.tseries.offsets import BDay
import datetime as dt
from datetime import datetime
import numpy as np
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
from classe import Bases, DbManager

def main():
    # Crie uma instância do DatabaseManager
    db_manager = DbManager()
    ImportB=Bases(db_manager.connect())
    
    # Crie instâncias das classes de dados
    equipe_data = ImportB.importBases('view_Equipes')
    st.write("Equipe de Cobrança Geral:")
    st.dataframe(equipe_data)
    
    liquidado_data = ImportB.importBases('Liquidado',6,'Data Liquidacao')
    st.write("Liquidado de Cobrança Geral:")
    st.dataframe(liquidado_data)
    
    metas_cobranca = ImportB.importBases('metas_cobranca_geral',6)
    st.write("Metas de Cobrança Geral:")
    st.dataframe(metas_cobranca)
    
    aReceber = ImportB.importBases('Areceber') 
    st.write("Dados de aReceber:")
    st.dataframe(aReceber)
    
    feriados=ImportB.importBases('feriados')
    st.write("Feriados:")
    st.dataframe(feriados)
    
    # # Teste da classe LiquidadoData
    # base_liq, base_aliq = liquidado_data.import_base(6)  # Importa dados de liquidação para o mês 6
    # st.write("Base de Liquidação:")
    # st.dataframe(base_liq)
    # st.write("Base de A Liquidar:")
    # st.dataframe(base_aliq)

# feriados = get_feriados(2024)
# st.write("Feriados:")
# st.dataframe(feriados)

if __name__ == "__main__":
    main()
