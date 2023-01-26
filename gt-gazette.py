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

ftp_connection.cwd('/descargas-rosario/gt')

# Get available docs in source
start_url = 'https://legal.dca.gob.gt/GestionDocumento/BusquedaDocumento'
start_date = '01/01/2023'
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

                # Delete file if present in FTP server
                try:
                    ftp_connection.delete(f'{document_date}.pdf')
                    print(f'{document_date}: deleted it from FTP server')
                except:
                    print(f'{document_date}: not present in FTP server')

            # If file is neither in vLex nor in FTP server
            elif f'{document_date}.pdf' not in ftp_connection.nlst():
                print(f'\n{document_date}: downloading it from source...')
                response = requests.get(f'https://legal.dca.gob.gt/GestionDocumento/DescargarPDFDocumento?idDocumento={document_id}').content
                temp = io.BytesIO(response)
                ftp_connection.storbinary(f'STOR {document_date}.pdf', temp)
                print(f'{document_date}: uploaded to FTP')

            # If file is already in FTP server but not in vLex
            elif f'{document_date}.pdf' in ftp_connection.nlst():
                print(f'\n{document_date}: already in FTP server but no processed')

f'\n{session.close()}'
f'\n{ftp_connection.close()}'
