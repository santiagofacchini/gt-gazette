import os
import re
from datetime import date
import requests
import PyPDF2


# Download directory
download_directory = '/usr/src/app/downloads/'

# Set start url
start_url = 'https://legal.dca.gob.gt/GestionDocumento/BusquedaDocumento'

# Start-end dates
start_date = '17/12/2018' # As defined in website
end_date = date.today().strftime("%d/%m/%Y")

# Payload for POST request
payload = {
    'categoria': 'VI',
    'fechaPublicacionInicial': start_date,
    'fechaPublicacionFinal': end_date,
    'busquedaAvanzada': 'false',
}

# Session
session = requests.Session()

# Make main POST request
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

    # Get each document
    for document in page_content.json()['documentos']:

        # Metadata
        document_date = re.sub(r'(\d{2})/(\d{2})/(\d{4}) 00:00:00', r'\1\2\3', document['FechaPublicacion'])
        document_id = document["DocumentID"]

        # Skip files already downloaded
        if os.path.isfile(f'{download_directory}{document_id}_{document_date}.pdf' ):
            print(f'{document_id}_{document_date}.pdf already in files. Skipping')

        # Download files not present in local directory
        else:
            print(f'Downloading PDF with id {document_id}...')

            # Response in bytes
            response = requests.get(f'https://legal.dca.gob.gt/GestionDocumento/DescargarPDFDocumento?idDocumento={document_id}')

            # Write response content to PDF file
            with open(f'{download_directory}{document_id}_{document_date}.pdf', 'wb') as pdf_file:
                pdf_file.write(response.content)

            # Get PDF file page count
            page_count = PyPDF2.PdfFileReader(f'{download_directory}{document_id}_{document_date}.pdf').getNumPages()

            # Date
            csv_date = document["FechaPublicacion"].replace(' 00:00:00', '')

            # Create CSV file
            with open(f'{download_directory}{document_id}_{document_date}.csv', 'w') as csv_file:
                csv_file.write(f'Diario Oficial de Guatemala del {csv_date} (contenido completo)||Contenido Completo|{csv_date}|1|{page_count}')
            print('OK')

# Close requests session
session.close()