import os
import io
import csv
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# paramentros de busqueda
publisher = "Generalitat+de+Catalunya"
type_file = "CSV"
# Para mas palabras de busquedas incluir (+) en los espacios ejemplo covid+19
words_search = "covid"

# url de acceso para la realización del web-scraping
domain = "https://datos.gob.es"
url_list = "https://datos.gob.es/es/catalogo?theme_id=salud&publisher_display_name="+publisher+ \
           "&sort=metadata_created+desc&res_format_label="+type_file+ \
           "&q="+words_search+ \
           "&_publisher_display_name_limit=0"

# path de fichero csv
currentDir = os.path.dirname(__file__)
filename = "gob_dataset.csv"
filePath = os.path.join(currentDir, filename)

# cabecera del fichero csv
header_list = ['title', 'publish', 'entity', 'license_type', 'url_csv',\
               'tags', 'creation_date', 'update_date', 'insert_date_time']

# incluir cabecera descripcion corta y larga
# header_list = ['title', 'publish', 'desc_short', 'entity', 'license_type',\
# 'desc_long', 'url_csv', 'tags', 'creation_date', 'update_date', 'insert_date_time']


# función para la limpieza de salto de linea y espacios en blanco
def _clear_salto_linea(word):
    word = word.replace("\n", "")
    return word.strip()


# funcion de eliminación en url de dataset extraido
def _replace_word(word):
    return word.replace('?accessType=DOWNLOAD', '')


# función para la conexion con la url y extracción del html
def _connect_url_bs4(url_con):
    page = requests.get(url_con, verify=False)
    html_page = page.content
    bs = BeautifulSoup(html_page, features="html.parser")
    return bs


# función para la creación del fichero csv
def _write_file_csv(rows_all):
    with open(filePath, 'w', newline='\n') as csvFile:
        writer = csv.writer(csvFile, delimiter='|')
        writer.writerow(header_list)
        for line in rows_all:
            writer.writerow(line)


# función de lectura de fichero csv por medio de la libreria pandas
def _read_csv_pandas():
    return pd.read_csv(filePath, delimiter='|')


# función de lectura de fichero csv por medio de url
def _read_csv_pandas_url(url):
    s = requests.get(url).content
    return pd.read_csv(io.StringIO(s.decode('utf-8')))


# función de lectura de fichero csv
def _read_csv_test():
    print("\n TEST read CSV")
    with open(filePath, "r", newline='\n') as f:
        reader = csv.reader(f, delimiter='|')
        for line in reader:
            print(line)


# función de carga para realizar el web-scraping
def _load_web_scraping():
    soup = _connect_url_bs4(url_list)
    table = soup.findAll('li', attrs={'class': 'dataset-item dge-list--elm'})

    rows_all = []

    for row in table:
        list_of_rows = []
        titulo_r = row.find('strong', attrs={'class': 'dge-list__title dataset-heading'})
        titulo_text_r = _clear_salto_linea(titulo_r.get_text())
        list_of_rows.append(str(titulo_text_r))
        print("[title          ] "+titulo_text_r)

        titulo_ref_r = _clear_salto_linea(titulo_r.find('a', href=True)['href'])  # --
        publicado = row.find('span', attrs={'class': 'publisher-title'})
        publicado_text = _clear_salto_linea(publicado.get_text())
        list_of_rows.append(publicado_text)
        print("[publish       ]  " + publicado_text)

        desc_short = row.find('div', attrs={'class': 'dge-list__desc'})
        desc_short_text = desc_short.get_text()
        # list_of_rows.append(str(desc_short))
        # print("[desc_short      ]  " + desc_short_text)

        url_detail = domain+titulo_ref_r
        soup_detail = _connect_url_bs4(url_detail)
        detail = soup_detail.find('div', attrs={'class': 'module-content'})
        publicado_admin = detail.find('section', attrs={'class': 'publisher'})
        publicado_admin_l = publicado_admin.findAll('div', attrs={'class': 'dataset-metadata'})[1:]
        entity = _clear_salto_linea(publicado_admin_l[0].find('span').get_text())
        list_of_rows.append(entity)
        print("[entity ]  " + entity)

        license_type = detail.find('section', attrs={'class': 'license'})
        license_type_l = license_type.findAll('div', attrs={'class': 'dataset-metadata'})[0:]
        license_type_text = _clear_salto_linea(license_type_l[0].find('span').get_text())  # --
        list_of_rows.append(license_type_text)
        print("[license_type    ]  " + license_type_text)

        desc_long = detail.find('section', attrs={'class': 'description'})
        desc_long_text = desc_long.find('div', attrs={'class': 'notes embedded-content'}).get_text()
        # list_of_rows.append(str(desc_long_text))
        # print("[desc_long       ]  " + desc_long_text)

        file_csv = detail.find('section', attrs={'class': 'resources', 'id': 'dataset-resources'})
        file_csv_l = file_csv.findAll('ul', attrs={'class': 'resource-list'})
        for csvl in file_csv_l:
            files_link = csvl.findAll('li', attrs={'class': 'resource-item'})
            for csv_link in files_link:
                csv_link_button = csv_link.find('div', attrs={'class': 'btn-group'})
                csv_link_file = _replace_word(csv_link_button.find('a', href=True)['href'])
                csv_link_kind = csv_link.find('div', attrs={'class': 'resource-item format'}).get_text()
                if _clear_salto_linea(csv_link_kind) == type_file:  # --
                    list_of_rows.append(csv_link_file)
                    print("[url_csv    ] "+csv_link_file)

        tags = detail.find('section', attrs={'class': 'tags'})
        tags_l = tags.findAll('ul', attrs={'class': 'tag-list'})
        tags_name = []
        for tag in tags_l:
            t_name_g = tag.findAll('li')
            for n in t_name_g:
                t_name = _clear_salto_linea(n.find('a').get_text())  # --
                tags_name.append(t_name)
        list_of_rows.append(str(tags_name))
        print("[tags        ] "+str(tags_name))

        date_info_s = detail.find('section', attrs={'class': 'additional-info'})
        date_info_d = date_info_s.find('div', attrs={'class': 'additional-info__content'})
        date_info_t = date_info_d.find('table')
        date_info_tb = date_info_t.find('tbody')
        date_info_tr = date_info_tb.findAll('tr')
        creation_date = _clear_salto_linea(date_info_tr[0].find('td').get_text())
        list_of_rows.append(creation_date)
        print("[creation_date       ]" + creation_date)

        update_date = _clear_salto_linea(date_info_tr[1].find('td').get_text())
        list_of_rows.append(update_date)
        print("[update_date         ]" + update_date)

        now = datetime.now()
        insert_date_time = now.strftime("%m/%d/%Y-%H:%M:%S")
        list_of_rows.append(str(insert_date_time))
        print("[insert_date_time    ]" + insert_date_time)

        rows_all.append(list_of_rows)
    return rows_all

# llamada a la función de carga del web-scraping y creación del csv
_write_file_csv(_load_web_scraping())

# lectura del fichero de csv por pandas a dataframe
df = _read_csv_pandas()
print(df)
print(df.head())
print(df.tail())

# lectura de dataset extraido del csv del web-scarping
df_url = _read_csv_pandas_url(df.url_csv[0])
print(df_url)

_read_csv_test()
