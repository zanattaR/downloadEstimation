import streamlit as st
import pandas as pd
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import seaborn as sns
import base64
from io import BytesIO
import locale
locale.setlocale(locale.LC_ALL, 'pt_pt.UTF-8')


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

# Função para adicionar valor nas barras ou linhas do gráfico
def add_value_labels(ax, typ, spacing=5):
    space = spacing
    va = 'bottom'

    if typ == 'bar':
        for i in ax.patches:
            y_value = i.get_height()
            x_value = i.get_x() + i.get_width() / 2

            label = "{:.0f}".format(y_value)
            ax.annotate(label,(x_value, y_value), xytext=(0, space), 
                    textcoords="offset points", ha='center', va=va)     
    if typ == 'line':
        line = ax.lines[0]
        for x_value, y_value in zip(line.get_xdata(), line.get_ydata()):
            label = "{:.2f}".format(y_value)
            ax.annotate(label,(x_value, y_value), xytext=(0, space), 
                textcoords="offset points", ha='center', va=va) 

# Título
# Imagem
img = Image. open('downest_logo.png')
st.image(img)

# Vídeo
st.markdown('## Tutorial')
video_file = open("tutorial_downest.mp4", "rb")
video_bytes = video_file.read()
st.video(video_bytes)



st.markdown('### Arquivos necessários para o inserir na ferramenta: ')
st.write('''
	1 - Arquivo .csv das novas instalações baixado do Google Play Console. (Apenas c/ o filtro de todos os países) \n
	2 - Arquivo .xlsx da Posição de Categoria baixado da Tool.\n
	3 - Dois Arquivos .xlsx de apps concorrentes baixados da Tool. (Data Export) \n''')

############## Upload datasets ##############

st.markdown("## Dados do cliente")
st.markdown("#### Instalações")

nome_cliente = st.text_input('Insira o nome do app:', value='Cliente')
data_cliente = st.file_uploader("Insira a base de dados aqui:", type='csv')

if data_cliente is not None:
	df_cliente = pd.read_csv(data_cliente, usecols=[0,1], dtype={1: object})
	df_cliente.columns.values[1] = "Installs"
	df_cliente['Installs'] = df_cliente['Installs'].str.replace(".","")
	df_cliente['Installs'] = df_cliente['Installs'].astype(int)
	df_cliente['Data'] = pd.to_datetime(df_cliente['Data'], format="%d de %b de %Y")
	df_cliente['App'] = nome_cliente
	df_cliente.rename(columns={"Data":"DATE"}, inplace=True)


########### Posição na Categoria ##########

st.markdown("#### Posição na Categoria")
data_cat = st.file_uploader("Insira a base de dados aqui:", type='xlsx')

if data_cat is not None:
	df_cat = pd.read_excel(data_cat, usecols=['FULL DATE','RANKING'])
	df_cat['FULL DATE'] = pd.to_datetime(df_cat['FULL DATE'], format='%d-%m-%Y')
	df_cat.sort_values(by=['FULL DATE'], inplace=True)
	df_cat.reset_index(drop=True,inplace=True)

########### Concorrente 1 ###########

st.markdown("## Dados dos Concorrentes")
st.markdown("#### Concorrente 1")

nome_comp_1 = st.text_input('Insira o nome do Concorrente 1:', value='Concorrente_1')
data_comp_1 = st.file_uploader("Insira a base do Concorrente 1:", type='xlsx')

if data_comp_1 is not None:
	df_comp_1 = pd.read_excel(data_comp_1, usecols=['MAX INSTALLS','DATE'])
	df_comp_1['DATE'] = pd.to_datetime(df_comp_1['DATE'], format='%d-%m-%Y')
	df_comp_1.sort_values(by=['DATE'], inplace=True)
	df_comp_1.reset_index(drop=True,inplace=True)
	df_comp_1['App'] = nome_comp_1
	
########### Concorrente 2 ###########

st.markdown("#### Concorrente 2")

nome_comp_2 = st.text_input('Insira o nome do Concorrente 2:', value='Concorrente_2')
data_comp_2 = st.file_uploader("Insira a base do Concorrente 2:", type='xlsx')

if data_comp_2 is not None:
	df_comp_2 = pd.read_excel(data_comp_2, usecols=['MAX INSTALLS','DATE'])
	df_comp_2['DATE'] = pd.to_datetime(df_comp_2['DATE'], format='%d-%m-%Y')
	df_comp_2.sort_values(by=['DATE'], inplace=True)
	df_comp_2.reset_index(drop=True,inplace=True)
	df_comp_2['App'] = nome_comp_2


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
comp_1_daily = diff_installs(df_comp_1)
comp_2_daily = diff_installs(df_comp_2)

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
comp_1_out_clean = outlierDetect(comp_1_daily)
comp_2_out_clean = outlierDetect(comp_2_daily)

# Condição caso a primeira linha seja NaN
while comp_1_out_clean['Installs'].isnull()[0] == True:
    comp_1_out_clean = comp_1_out_clean.iloc[1:,:]
    comp_1_out_clean.reset_index(drop=True, inplace=True)

# Condição caso a primeira linha seja NaN
while comp_2_out_clean['Installs'].isnull()[0] == True:
    comp_2_out_clean = comp_2_out_clean.iloc[1:,:]
    comp_2_out_clean.reset_index(drop=True, inplace=True)


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
impute(comp_1_out_clean, 'Installs')
impute(comp_2_out_clean, 'Installs')

# Função para retroceder um dia na data
def day_back(df_out_clean):
    diario_real = df_out_clean['Installs'][1:]
    diario_real.reset_index(drop=True, inplace=True)
    df_out_clean.drop(df_out_clean.index[-1], inplace=True)
    df_out_clean['Installs'] = diario_real

# Aplicando função para retroceder um dia na data
day_back(comp_1_out_clean)
day_back(comp_2_out_clean)


########## GRÁFICOS #############

st.markdown('## Instalações X Posição')
st.markdown('''#### O gráfico abaixo apresenta a média de instalações do app por mês, sendo comparada à média da posição na categoria.''')
st.write("")

if st.checkbox('Gráfico Comparação Instalações x Posição na Categoria - Mensal'):

	# Juntando df's

	df_cat_real = df_cat.merge(df_cliente, how='inner', left_on='FULL DATE', right_on='DATE')
	df_cat_real.drop('FULL DATE',axis=1, inplace=True)
	df_cat_real.set_index('DATE', inplace=True)

	# Agrupando média mensal
	df_plot_1 = df_cat_real.groupby(pd.Grouper(freq='M')).mean()
	df_plot_1.index = df_plot_1.index.strftime('%B-%y')
	df_plot_1['RANKING'] = df_plot_1['RANKING'].astype(int)
	df_plot_1['Installs'] = df_plot_1['Installs'].astype(int)

	st.write(df_plot_1)

	fig = plt.figure(figsize=(10,6))

	ax1 = plt.subplot(1,1,1)
	ax1.bar(df_plot_1.index, df_plot_1['Installs'], color='#07b2cf', label="Média de Instalações diária")
	ax1.set_ylim(0, df_plot_1['Installs'].max() * 1.25)
	ax1.legend()

	ax2 = ax1.twinx()
	ax2.plot(df_plot_1.index, df_plot_1['RANKING'],'o-', color='black',label="Posição média na Categoria")
	ax2.set_ylim(df_plot_1['RANKING'].min() * 0.6, df_plot_1['RANKING'].max() * 1.20)
	ax2.legend(loc=(0.677, 0.86))
	ax2.invert_yaxis()

	plt.title('Média de Instalações mensais X Média da posição na categoria', fontsize=15)

	add_value_labels(ax1, typ='bar')
	add_value_labels(ax2, typ='line')

	st.pyplot()

	df_download_1 = df_plot_1.reset_index()
	st.write('Clique em Download para baixar os dados')
	st.markdown(get_table_download_link(df_download_1), unsafe_allow_html=True)


st.markdown('## Instalações por App')
st.markdown('''#### Os gráficos abaixo apresentam uma comparação de instalações entre o cliente e seus concorrentes individualmente.''')
st.write("")

if st.checkbox('Gráfico Comparação Instalações - Mensal'):

	fig = plt.figure(figsize=(18,6))

	comp_1_month = comp_1_out_clean.drop('MAX INSTALLS',axis=1)
	comp_2_month = comp_2_out_clean.drop('MAX INSTALLS',axis=1)

	df_all = pd.concat([df_cliente, comp_1_month, comp_2_month])
	df_all.reset_index(drop=True, inplace=True)
	df_all['month'] = df_all['DATE'].dt.strftime('%B-%y')

	df_plot_2 = df_all.groupby(['month','App']).mean()
	df_plot_2.reset_index(level=[1],inplace=True)
	df_plot_2.index = pd.to_datetime(df_plot_2.index, format='%B-%y')
	df_plot_2.sort_index(inplace=True)
	df_plot_2.index = df_plot_2.index.strftime('%B-%y')

	st.write(df_plot_2.head())
	sns.lineplot(data=df_plot_2, x=df_plot_2.index, y='Installs', hue='App', sort=False)

	ax1 = plt.axes()
	x_axis = ax1.xaxis
	x_axis.label.set_visible(False)
	y_axis = ax1.yaxis
	y_axis.label.set_visible(False)

	plt.legend(fontsize=12)
	plt.xticks(fontsize=14)
	plt.title('Comparação de Instalações Mensais', fontsize=20)

	st.pyplot()

	df_download_2 = df_plot_2.reset_index()
	st.write('Clique em Download para baixar os dados')
	st.markdown(get_table_download_link(df_download_2), unsafe_allow_html=True)


if st.checkbox('Gráfico Comparação Instalações - Diário'):
	
	fig = plt.figure(figsize=(18,6))
	
	comp_1_day = comp_1_out_clean.drop('MAX INSTALLS',axis=1)
	comp_2_day = comp_2_out_clean.drop('MAX INSTALLS',axis=1)

	df_plot_3 = pd.concat([df_cliente, comp_1_day, comp_2_day])
	df_plot_3.reset_index(drop=True, inplace=True)
	df_plot_3.set_index('DATE', inplace=True)

	st.write(df_plot_3.head())
	sns.lineplot(data=df_plot_3, x=df_plot_3.index, y='Installs', hue='App')

	ax1 = plt.axes()
	x_axis = ax1.xaxis
	x_axis.label.set_visible(False)
	y_axis = ax1.yaxis
	y_axis.label.set_visible(False)

	plt.legend(fontsize=12)
	plt.xticks(fontsize=14)
	plt.title('Comparação de Instalações Diárias', fontsize=20)

	st.pyplot()

	df_download_3 = df_plot_3.reset_index()
	st.write('Clique em Download para baixar os dados')
	st.markdown(get_table_download_link(df_download_3), unsafe_allow_html=True)


st.markdown('## Instalações por App X Benchmark')
st.markdown('''#### Os gráficos abaixo apresentam uma comparação de instalações entre o cliente e seus concorrentes de forma agregada.''')
st.write("")

if st.checkbox('Gráfico Comparação Concorrentes - Mensal'):

	fig = plt.figure(figsize=(14,7))
	
	comp_1_day = comp_1_out_clean.drop('MAX INSTALLS',axis=1)
	comp_2_day = comp_2_out_clean.drop('MAX INSTALLS',axis=1)

	df_comp_all = pd.concat([comp_1_day, comp_2_day])
	df_comp_all['App'] = 'Média Concorrentes'

	df_cliente_comp = pd.concat([df_cliente, df_comp_all])
	df_cliente_comp.reset_index(drop=True, inplace=True)
	df_cliente_comp['month'] = df_cliente_comp['DATE'].dt.strftime('%B-%y')

	df_plot_4 = df_cliente_comp.groupby(['month','App']).mean()
	df_plot_4.reset_index(level=[1],inplace=True)
	df_plot_4.index = pd.to_datetime(df_plot_4.index, format='%B-%y')
	df_plot_4.sort_index(inplace=True)
	df_plot_4.index = df_plot_4.index.strftime('%B-%y')

	st.write(df_plot_4.head())

	sns_ax = sns.barplot(data=df_plot_4, x=df_plot_4.index, y='Installs', hue='App', palette=['#00daff','#666666'])

	ax1 = plt.axes()
	ax1.set_ylim(0, df_plot_4['Installs'].max() * 1.25)
	x_axis = ax1.xaxis
	x_axis.label.set_visible(False)
	y_axis = ax1.yaxis
	y_axis.label.set_visible(False)

	plt.legend(fontsize=12)
	plt.xticks(fontsize=14)
	plt.title('Média de Instalações {} X Concorrentes'.format(nome_cliente), fontsize=20)

	add_value_labels(sns_ax, typ='bar')
	
	st.pyplot()

	df_download_4 = df_plot_4.reset_index()
	st.write('Clique em Download para baixar os dados')
	st.markdown(get_table_download_link(df_download_4), unsafe_allow_html=True)


if st.checkbox('Gráfico Comparação Concorrentes - Diário'):

	fig = plt.figure(figsize=(18,6))
	
	comp_1_day_all = comp_1_out_clean.drop('MAX INSTALLS',axis=1)
	comp_2_day_all = comp_2_out_clean.drop('MAX INSTALLS',axis=1)

	df_comp_daily_all = pd.concat([comp_1_day_all, comp_2_day_all])

	df_comp_daily_all['App'] = 'Média Concorrentes'

	df_cliente_comp_daily = pd.concat([df_cliente, df_comp_daily_all])
	df_cliente_comp_daily.reset_index(drop=True, inplace=True)

	df_plot_5 = df_cliente_comp_daily.groupby(['DATE','App']).mean()
	df_plot_5.reset_index(level=[1],inplace=True)

	sns.lineplot(data=df_plot_5, x=df_plot_5.index, y='Installs', hue='App')

	st.write(df_plot_5.head())

	ax1 = plt.axes()
	x_axis = ax1.xaxis
	x_axis.label.set_visible(False)
	y_axis = ax1.yaxis
	y_axis.label.set_visible(False)

	plt.legend(fontsize=12)
	plt.xticks(fontsize=14)
	plt.title('Média de Instalações {} X Concorrentes'.format(nome_cliente), fontsize=20)

	st.pyplot()

	df_download_5 = df_plot_5.reset_index()
	st.write('Clique em Download para baixar os dados')
	st.markdown(get_table_download_link(df_download_5), unsafe_allow_html=True)
