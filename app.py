from flask import Flask, render_template
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from bs4 import BeautifulSoup 
import requests
from datetime import datetime
import plotly.express as px

#don't change this
matplotlib.use('Agg')
app = Flask(__name__) #do not change this


#insert the scraping process here
weblist = ['home', 'home/all-jobs', 'home/work_from_home/y', 'home?sort=Salary', 'home?sort=Freshness', 'home/i/it-and-software',
           'home/i/sales-and-marketing', 'home/i/accounting-and-finance',
           'home/w/500-director-or-executive', 'home/w/400-mid-senior-level-or-manager',
           'home/w/300-associate-or-supervisor', 'home/w/200-entry-level-or-junior-and-apprentice', 'home/w/100-internship-or-ojt',
           'home/t/contractual', 'home/t/freelance', 'home/t/part-time', 'home/t/full-time']

temp = []  # initiating a tuple
url_get = requests.get(f"https://kalibrr.com/id-ID/home")

for sites in weblist:
    url_get = requests.get(f"https://kalibrr.com/id-ID/{sites}")
    soup = BeautifulSoup(url_get.content, "html.parser")
    table = soup.find('div', attrs={'class': 'k-px-4 md:k-px-10 k-flex k-flex-col'})

    spans = table.find_all('span', attrs={'class': 'k-text-gray-500'})
    row = table.find_all('span', attrs={'class': 'k-inline-flex k-items-center k-mb-1'})
    row_length = len(row)

    # spans2 = table.find_all('p', attrs={'class': 'k-text-gray-500'})

    post_list = []

    for span in spans:
        if "Rekruter" in span.text:
            post_list.append(span)

    for i in range(1, row_length):

        # scraping process

        # title pekerjaan
        title = table.find_all('a', attrs={'class': 'k-text-black'})[i].text

        # perusahaan
        company = table.find_all('a', attrs={'class': 'k-text-subdued k-font-bold'})[i].text

        # lokasi
        location = table.find_all('span', attrs={'class': 'k-text-gray-500 k-block k-pointer-events-none'})[i].text

        # tanggal pekerjaan di post
        post_date = post_list[i].text

        # deadline submit permohonan
        deadline = table.find_all('span', attrs={'class': 'k-text-xs k-font-bold k-text-gray-600'})[i].text

        # pengalaman
        entry_level = table.find_all('a', attrs={'class': 'k-font-dm-sans k-text-xs k-font-bold k-text-gray-600'})[i].text

        # employ
        employment = table.find_all('span', attrs={'class': 'k-hidden'})[i].text

        temp.append((title, company, location, post_date,
                     deadline, entry_level, employment))

#change into dataframe
df = pd.DataFrame(temp, columns=['title','company','location','post_date','deadline','entry_level','employment'])
#insert data wrangling here
df_clean = df.drop_duplicates()
df_clean['company'] = df_clean['company'].astype('category')
df_clean['location'] = df_clean['location'].astype('category')
df_clean['entry_level'] = df_clean['entry_level'].astype('category')
df_clean['employment'] = df_clean['employment'].astype('category')

df_clean['deadline'] = df_clean['deadline'].str.replace('Apply before ','')
month_map = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
             'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
df_clean['day'] = df_clean['deadline'].str.extract('(\d+)').astype(int)
df_clean['month'] = df_clean['deadline'].str.extract('([a-zA-Z]+)')
df_clean['month'] = df_clean['month'].map(month_map)

df_clean_dec = df_clean[df_clean['deadline'].str.contains('Dec') & (df_clean['day'] > int(datetime.now().strftime('%d')))]
df_clean_not_dec = df_clean[df_clean['deadline'].str.contains('Dec')==False]


df_clean_dec['year'] = 2023
df_clean_not_dec['year'] = 2024

df_clean_dec['formatted_date'] = pd.to_datetime(df_clean_dec[['day', 'month', 'year']], format='%d%m%Y')
df_clean_not_dec['formatted_date'] = pd.to_datetime(df_clean_not_dec[['day', 'month', 'year']], format='%d%m%Y')
df_clean = pd.concat([df_clean_dec,df_clean_not_dec])
df_clean['deadline_day'] = df_clean['formatted_date'] - datetime.now()

#Sesuaikan Nilai Jakarta
df_jakarta = df_clean[df_clean['location'].str.contains('Jakarta')==True]
df_nonjkt = df_clean[df_clean['location'].str.contains('Jakarta')==False]
df_jakarta.loc[:,['location']] = 'Jakarta, Indonesia'
df_clean = pd.concat([df_jakarta,df_nonjkt])

#Sesuaikan Nilai Filipina
df_filipina = df_clean[df_clean['location'].str.contains('Philippines')==True]
df_nonfilipina = df_clean[df_clean['location'].str.contains('Philippines')==False]
df_filipina.loc[:,['location']] = 'Phillippines'
df_clean = pd.concat([df_filipina,df_nonfilipina])
df_tangerang = df_clean[df_clean['location'].str.contains('Tangerang')==True]

#Sesuaikan Nilai Tangerang
df_nontangerang = df_clean[df_clean['location'].str.contains('Tangerang')==False]
df_tangerang.loc[:,['location']] = 'Tangerang, Indonesia'
df_clean = pd.concat([df_tangerang,df_nontangerang])

df_clean = df_clean.sort_values(by='deadline_day').loc[:, ['title', 'company', 'location', 'post_date', 'entry_level', 'employment', 'deadline_day', 'formatted_date']]
df_clean = df_clean.reset_index()

# move from def index2(): filter and pivot the dataframe
df_pivot = df_clean[df_clean['location'].isin(['Tangerang, Indonesia', 'Phillippines', 'Jakarta, Indonesia'])].pivot_table(columns='location', index='entry_level', values='title', aggfunc='count').fillna(0)
df_clean['location'] = df_clean['location'].str.replace(', Indonesia','')
df_clean['deadline_day'] = df_clean['deadline_day']// pd.Timedelta('24h')
df_clean['deadline_day'] = df_clean['deadline_day'].astype('int64')

#end of data wranggling 

@app.route("/")
def index(): 
	
    card_data = f'{pd.crosstab(index=df_clean["location"], columns="Total")["Total"].sum()}'
   
    # generate first plot
    plt.subplots(figsize=(18,6))
    pd.crosstab(index=df_clean['location'], columns='Total').sort_values(by='Total').plot(kind='barh', ylabel='Lokasi', xlabel='Jumlah Lowongan', legend=False)
    figfile = BytesIO()
    plt.tight_layout()
    plt.savefig(figfile, format='png', transparent=True, dpi=100)
    plt.close()

    #set max width
    max_width = 800
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue()).decode('utf-8')
    plot_result = figdata_png
    #plt.close(plot_result)  # Close the figure to free memory
    
    
    # generate second plot
    plt.subplots(figsize=(18,6))
    df_pivot.plot(kind='barh', ylabel='Jabatan', xlabel='Jumlah Lowongan')
    figfile2 = BytesIO()
    plt.tight_layout()
    plt.savefig(figfile2, format='png', transparent=True,dpi=100)
    plt.close()

    #set max width
    max_width = 800
    figfile2.seek(0)
    figdata_png2 = base64.b64encode(figfile2.getvalue()).decode('utf-8')
    plot_result2 = figdata_png2
    #plt.close(plot_result2)  # Close the figure to free memory

    # generate third plot
    plt.subplots(figsize=(18,6))
    pd.crosstab(index=df_clean['company'],columns='Total',colnames=' ').sort_values(by='Total').tail(10).plot(kind='barh', ylabel='Perusahaan',xlabel = 'Jumlah Lowongan', legend=False)
    figfile3 = BytesIO()
    plt.tight_layout()
    plt.savefig(figfile3, format='png', transparent=True,dpi=100)
    plt.close()

    #set max width
    max_width = 800
    figfile3.seek(0)
    figdata_png3 = base64.b64encode(figfile3.getvalue()).decode('utf-8')
    plot_result3 = figdata_png3

    #show table 
    
    deadline_table = df_clean[df_clean['deadline_day'] <= 60 ].sort_values(by = 'deadline_day')

    deadline_table_list = deadline_table.to_dict(orient='records')

    # render to template
    return render_template('index.html',
                           card_data=card_data, 
                           plot_result=plot_result,
                           plot_result2=plot_result2,
                           plot_result3=plot_result3,
                           deadline_table = deadline_table_list)


if __name__ == "__main__": 
    app.run(debug=True)