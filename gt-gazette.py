import os
import io
import ftplib
from datetime import date
from re import sub
import requests


# Connect to FTP to verify if file has been downloaded but not processed, or upload new file
ftp_connection = ftplib.FTP(
    host=os.environ['AG2_HOST'],
    user=os.environ['AG2_USER'],
    passwd=os.environ['AG2_PASS'],
)

print(ftp_connection.getwelcome())

ftp_connection.cwd(os.environ['GT_FTP_PATH'])

# Current issue's date
day = date.today().strftime("%d")
month = date.today().strftime("%m")
year = date.today().strftime("%Y")
ymd_format = f'{year}{month}{day}'

'''print(f'\n***** Checking for latest issue: {year}/{month}/{day} *****')
try:
    r = requests.get(f'https://api.vlex.com/v1/sources/11510/issues/{year}-{month}-{day}/children.json').json()["results"]

    # If issue is in vLex
    if  r != []:
        print(f'\n{ymd_format}: available at {r[0]["children"][0]["public_url"]}')

        # Delete file if present in FTP
        try:
            ftp_connection.delete(f'{ymd_format}.pdf')
            print(f'{ymd_format}: deleted it from FTP {os.environ["GT_FTP_PATH"]}')
        except:
            print(f'{ymd_format}: not present in FTP {os.environ["GT_FTP_PATH"]}')

    # If file is neither in vLex nor in FTP
    elif f'{ymd_format}.pdf' not in ftp_connection.nlst():
        print(f'\n{ymd_format}: downloading it from source...')
        current_issue = requests.get('https://legal.dca.gob.gt/Content/PDF/DocumentoDelDiaPdf.pdf').content
        temp = io.BytesIO(current_issue)
        ftp_connection.storbinary(f'STOR {ymd_format}.pdf', temp)
        print(f'{ymd_format}: uploaded to FTP')

except:
    print(f'Could not download current issue at this execution')
'''

# Historic analysis
# Get available docs in source
start_url = 'https://legal.dca.gob.gt/GestionDocumento/BusquedaDocumento'
start_date = '01/01/2022'
end_date = date.today().strftime("%d/%m/%Y")

print(f'\n***** Running data extraction from {start_date} to {end_date} *****')

payload = {
    'categoria': 'VI',
    'fechaPublicacionInicial': start_date,
    'fechaPublicacionFinal': end_date,
    'busquedaAvanzada': 'false',
}

# Main POST request
session = requests.Session()
documents = session.post(
    url=start_url,
    data=payload,
)

# Main response is paginated and each page contains a maximum of 8 elements,
# this is then passed to 'BusquedaDocumentoAsync'
# Get total number of pages from response
total_pagination = documents.json()['last']

# Get documents from each page in pagination
for page_number in range(1, total_pagination+1):
    page_content = session.get(f'https://legal.dca.gob.gt/GestionDocumento/BusquedaDocumentoAsync?page={page_number}')

    for document in page_content.json()['documentos']:
        document_date = sub(r'(\d{2})/(\d{2})/(\d{4}) 00:00:00', r'\3\2\1', document['FechaPublicacion'])

        # Some documents might have 00010101 as date, ignore them
        # TODO: handle documents with 00010101 as date
        if document_date != '00010101':
            document_id = document["DocumentID"]

            # If issue is in vLex
            vlex_date = sub(r'(\d{2})/(\d{2})/(\d{4}) 00:00:00', r'\3-\2-\1', document['FechaPublicacion'])
            vlex_issue = session.get(f'https://api.vlex.com/v1/sources/11510/issues/{vlex_date}/children.json').json()["results"]

            if  vlex_issue != []:
                print(f'\n{document_date}: available at {vlex_issue[0]["children"][0]["public_url"]}')

                # Delete file if present in FTP
                try:
                    ftp_connection.delete(f'{document_date}.pdf')
                    print(f'{document_date}: deleted it from FTP {os.environ["GT_FTP_PATH"]}')
                except:
                    print(f'{document_date}: not present in FTP {os.environ["GT_FTP_PATH"]}')

            # If file is neither in vLex nor in FTP
            elif f'{document_date}.pdf' not in ftp_connection.nlst():
                print(f'\n{document_date}: downloading it from source...')
                response = requests.get(f'https://legal.dca.gob.gt/GestionDocumento/DescargarPDFDocumento?idDocumento={document_id}').content
                temp = io.BytesIO(response)
                ftp_connection.storbinary(f'STOR {document_date}.pdf', temp)
                print(f'{document_date}: uploaded to FTP')

f'\n{session.close()}'
f'\n{ftp_connection.close()}'
