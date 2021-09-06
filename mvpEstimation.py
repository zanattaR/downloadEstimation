import streamlit as st
import pandas as pd
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import base64
from io import BytesIO


st.set_option('deprecation.showPyplotGlobalUse', False)

# Função para transformar df em excel
def to_excel(df):
	output = BytesIO()
	writer = pd.ExcelWriter(output, engine='xlsxwriter')
	df.to_excel(writer, sheet_name='Planilha1',index=False)
	writer.save()
	processed_data = output.getvalue()
	return processed_data
	
# Função para gerar link de download
def get_table_download_link(df):
	val = to_excel(df)
	b64 = base64.b64encode(val)
	return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="extract.xlsx">Download</a>'

# Título
st.markdown('## Download Estimation - MaxInstalls')
st.write("")

st.write('''Esta aplicação tem como objetivo estimar o volume de novas instalações de um aplicativo da Play Store.''')
st.markdown('### Como utilizar esta aplicação')
st.write('''
	1 - Na Tool, vá em Data Export e faça o download do arquivo Max Installs do app desejado. \n
	2 - Faça o upload do arquivo no local indicado abaixo.\n
	3 - Escolha como deseja visualizar os dados de estimativa de downloads: Diário/Semanal/Mensal.\n
	4 - Faça o download das estimativas.''')

####### Upload dataset #######
st.subheader('Dados')
data = st.file_uploader("Insira a base de dados", type='xlsx')

if data is not None:
	df = pd.read_excel(data, usecols=['MAX INSTALLS','DATE'])
	df['DATE'] = pd.to_datetime(df['DATE'], format='%d-%m-%Y')
	df.sort_values(by=['DATE'], inplace=True)
	df.reset_index(drop=True,inplace=True)
	
	st.write('Mostrando as 5 primeiras linhas da base de dados')
	
st.write(df.head())

####### Pré-processamento #######

# Calculando diferença entre dias
def diff_installs(df):
    
    diff_list = []
    for i in range(1, len(df['MAX INSTALLS'])):
        x = df['MAX INSTALLS'][i] - df['MAX INSTALLS'][i-1]
        diff_list.append(x)
    
    df_daily = df.iloc[1:].reset_index(drop=True)
    df_daily['Installs'] = diff_list
    
    return df_daily

# Aplicando função de diferença entre dias
df_daily = diff_installs(df)

# Função para identificar outliers e substitui-los 
def outlierDetect(df_daily):
    
    # Média e Desvio Padrão
    data_mean, data_std = np.mean(df_daily['Installs']), np.std(df_daily['Installs'])
    
    # Idendificando outliers
    cut_off = data_std * 3
    
    lower,upper = data_mean - cut_off, data_mean + cut_off
    
    # Substituindo outliers por 0
    df_daily['Installs'] = np.where(df_daily['Installs'] > upper, 0.0,df_daily['Installs']).tolist()
    df_daily['Installs'] = np.where(df_daily['Installs'] < lower, 0.0,df_daily['Installs']).tolist()
    
    ## Segunda substituição de outliers ##
    
    # Substituindo 0 por Nan
    df_daily['Installs'] = df_daily['Installs'].replace(0.0, np.nan)
    
    # Média e Desvio padrão 2
    data_mean_2, data_std_2 = np.mean(df_daily['Installs']), np.std(df_daily['Installs'])
    
    # Identificando os outliers 2
    lower_2, upper_2 = (data_mean_2 - (data_std_2 * 1)), (data_mean_2 + (data_std_2 * 1))
    
    # Substituindo outliers por 0
    df_daily['Installs'] = np.where(df_daily['Installs'] > upper_2, 0.0, df_daily['Installs']).tolist()
    df_daily['Installs'] = np.where(df_daily['Installs'] < lower_2, 0.0, df_daily['Installs']).tolist()
    
    # Substituindo 0 por Nan
    df_daily['Installs'] = df_daily['Installs'].replace(0.0, np.nan)
    
    return df_daily

# Aplicando função de detecção de outliers
df_out_clean = outlierDetect(df_daily)

# Condição caso a primeira linha seja NaN
while df_out_clean['Installs'].isnull()[0] == True:
    df_out_clean = df_out_clean.iloc[1:,:]
    df_out_clean.reset_index(drop=True, inplace=True)

# Função para aplicar média dos últimos 7 dias nos campos NA
def impute(df_out_clean, col_name):
    
    while df_out_clean[col_name].isna().any().any():
        
        # If there are multiple NA values in a row, identify just the first one
        first_na = df_out_clean[col_name].isna().diff() & df_out_clean[col_name].isna()
        
        # Compute mean of previous 7 values
        imputed = df_out_clean.rolling(7, min_periods=1).mean().shift()[col_name]
        
        # Replace NA values with mean if they are very first NA value in run of NA values
        df_out_clean.loc[first_na, col_name] = imputed

# Aplicando função de preenchimento de valores nulos
impute(df_out_clean, 'Installs')

# Função para retroceder um dia na data
def day_back(df_out_clean):
    diario_real = df_out_clean['Installs'][1:]
    diario_real.reset_index(drop=True, inplace=True)
    df_out_clean.drop(df_out_clean.index[-1], inplace=True)
    df_out_clean['Installs'] = diario_real

# Aplicando função para retroceder um dia na data
day_back(df_out_clean)


if st.checkbox('Gráfico diário'):

	# Criando df final para plot
	df_final = df_out_clean[['DATE','Installs']]
	df_final['DATE'] = pd.to_datetime(df_final['DATE']).dt.date
	df_final.set_index('DATE',inplace=True)

	df_final['limit sup'] = df_final['Installs'] * 1.30
	df_final['limit inf'] = df_final['Installs'] * .70

	plt.figure(figsize=(16,7))
	plt.title('Estimativa Diária - Intervalo de Confiança: 30%')

	plt.plot(df_final['Installs'])
	plt.fill_between(df_final.index,df_final['limit inf'],df_final['limit sup'], color='b', alpha=.1)
	st.pyplot()

	# Preparando para download
	df_download = df_out_clean[['DATE','Installs']]
	df_download['DATE'] = pd.to_datetime(df_download['DATE']).dt.date
	df_download['Installs'] = df_download['Installs'].astype(int)

	st.write('Clique em Download para baixar os dados')
	st.markdown(get_table_download_link(df_download), unsafe_allow_html=True)

if st.checkbox('Gráfico Semanal'):

	# Criando df final para plot
	df_final = df_out_clean[['DATE','Installs']]
	df_final_weekly = df_final.groupby(df_final['DATE'].dt.to_period('W-SAT')).sum()
	df_final_weekly.index = df_final_weekly.index.astype(str)

	df_final_weekly['limit sup'] = df_final_weekly['Installs'] * 1.15
	df_final_weekly['limit inf'] = df_final_weekly['Installs'] * .85

	plt.figure(figsize=(16,7))
	plt.title('Estimativa de instalações no período')
	
	plt.plot(df_final_weekly['Installs'])
	plt.xticks(rotation=45)
	plt.title('Estimativa Semanal - Intervalo de Confiança: 15% ')
	plt.fill_between(df_final_weekly.index,df_final_weekly['limit inf'],df_final_weekly['limit sup'], color='b', alpha=.1)
	st.pyplot()

	# Preparando para download
	df_download = df_final_weekly.reset_index()
	df_download['Installs'] = df_download['Installs'].astype(int)
	df_download['limit sup'] = df_download['limit sup'].astype(int)
	df_download['limit inf'] = df_download['limit inf'].astype(int)

	st.write('Clique em Download para baixar os dados')
	st.markdown(get_table_download_link(df_download), unsafe_allow_html=True)

if st.checkbox('Gráfico Mensal'):

	# Criando df final para plot
	df_final = df_out_clean[['DATE','Installs']]
	df_final_monthly = df_final.groupby(df_final['DATE'].dt.to_period('M')).sum()
	df_final_monthly.index = df_final_monthly.index.astype(str)

	df_final_monthly['limit sup'] = df_final_monthly['Installs'] * 1.13
	df_final_monthly['limit inf'] = df_final_monthly['Installs'] * .87

	plt.figure(figsize=(16,7))
	plt.title('Estimativa de instalações no período')
	
	plt.plot(df_final_monthly['Installs'])
	plt.xticks(rotation=45)
	plt.title('Estimativa Mensal - Intervalo de Confiança: 13% ')
	plt.fill_between(df_final_monthly.index,df_final_monthly['limit inf'],df_final_monthly['limit sup'], color='b', alpha=.1)
	st.pyplot()

	# Preparando para download
	df_download = df_final_monthly.reset_index()
	df_download['Installs'] = df_download['Installs'].astype(int)
	df_download['limit sup'] = df_download['limit sup'].astype(int)
	df_download['limit inf'] = df_download['limit inf'].astype(int)

	st.write('Clique em Download para baixar os dados')
	st.markdown(get_table_download_link(df_download), unsafe_allow_html=True)