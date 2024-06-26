import streamlit as st
import pandas as pd
from pandas.tseries.offsets import BDay
import datetime as dt
from dotenv import load_dotenv
import mysql.connector
from sqlalchemy import create_engine, text, select,MetaData # Corrigido
from sqlalchemy.orm import sessionmaker
import os
import calendar
import requests
import base64
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib

load_dotenv()

# Classe para gerenciar conexão com o banco de dados
class DbManager:
    def __init__(self):
        self.config = {
            'host': '77.37.40.212',
            'user': 'root',
            'port': '3306',
            'password': os.getenv('MYSQL_ROOT_PASSWORD'),
            'database': 'gestao_equipe'
        }

    def connect(self):
        try:
            self.conn = mysql.connector.connect(**self.config)
            self.cursor = self.conn.cursor()
            st.info("Conexão ao MySQL bem-sucedida!")
            return self.conn
        except mysql.connector.Error as err:
            st.error(f"Erro ao conectar ao MySQL: {err}")
            st.stop()
    
    def connectAlc(self):
        # Substitua pelos seus detalhes de conexão
        return create_engine(f'mysql+mysqlconnector://{self.config["user"]}:{self.config["password"]}@{self.config["host"]}/{self.config["database"]}')

    def disconnect(self):
        if self.conn:
            self.conn.close()

class Bases:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def importBases(self,tabela,mes=None,coluna=None,ano=None):
        if mes and coluna: 
            query = f"SELECT * FROM {tabela} WHERE MONTH(`{coluna}`) = {mes};"
            return pd.read_sql(query, self.db_manager) 
        elif ano and coluna:
            query = f"SELECT * FROM {tabela} WHERE YEAR(`{coluna}`) = {ano};"
            return pd.read_sql(query, self.db_manager) 
        else:
            query = f"SELECT * FROM {tabela};"
            return pd.read_sql(query, self.db_manager) 
        
class Login:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.engine = self.db_manager.connectAlc()
        self.Session = sessionmaker(bind=self.engine)

    def authenticate_user(self, email, password):
        session = self.Session()
        
        query = text("SELECT * FROM usuarios WHERE email = :email AND password = :password")
        result = session.execute(query, {"email": email, "password": password})
        user = result.fetchone()
        if user:
            return True, user[0]
        return False, None

    def create_user(self, email, password, name):
        session = self.Session()
        query = text("INSERT INTO usuarios (email, password, name) VALUES (:email, :password, :name)")
        session.execute(query, {
            "email": email,
            "password": generate_password_hash(password),
            "name": name
        })

    def get_user_info(self, user_id):
        session = self.Session()  # Usar connectAlc para obter o engine
        query = text("SELECT name, email,classe FROM usuarios WHERE id = :user_id")
        result = session.execute(query, {"user_id": user_id})
        user_info = result.fetchone()
        if user_info:
            return user_info
        return None


        

        
