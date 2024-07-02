import streamlit as st
from classe import Login, DbManager
from werkzeug.security import generate_password_hash
import metas  # Importe o módulo do seu dashboard

# Inicializar o gerenciador de sessão
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def main():

    # Criar uma instância do DbManager como cache_resource
    @st.cache_resource
    def init_db_manager():
        return DbManager()
    db_manager = init_db_manager()

    login_manager = Login(db_manager)

    if st.session_state.authenticated:
        # Executa o dashboard passando as informações do usuário
        metas.run(st.session_state.user_info)  
    else:
        col1,col2,col3 = st.columns([5,2,5])
        with col2:
            # Formulário de login
            st.title("Login")
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")

            if st.button("Login"):
                authenticated, user_id = login_manager.authenticate_user(email, password)

                if authenticated:
                    st.session_state['authenticated'] = True  
                    st.session_state['user_info'] = login_manager.get_user_info(user_id)
                    st.rerun() # Recarrega a página para exibir o dashboard
                else:
                    st.error("Email ou senha incorretos!")

        # with st.expander("Criar Novo Usuário"):
        #     new_email = st.text_input("Novo Email")
        #     new_password = st.text_input("Nova Senha", type="password")
        #     new_name = st.text_input("Nome")

        #     if st.button("Criar Usuário"):
        #         login_manager.create_user(new_email, new_password, new_name)
        #         st.success("Usuário criado com sucesso!")

if __name__ == "__main__":
    main()
