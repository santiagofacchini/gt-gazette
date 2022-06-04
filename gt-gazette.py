import re
from datetime import date
import requests


# Set start url
start_url = 'https://legal.dca.gob.gt/GestionDocumento/BusquedaDocumento'

# Start-end dates
start_date = '17/12/2018' # As defined in website
end_date = date.today().strftime("%d/%m/%Y")

# Payload for POST request
payload = {
    'categoria': 'VI',
    'tipo': '',
    'subtipo': '',
    'texto': '',
    'fechaPublicacionInicial': start_date,
    'fechaPublicacionFinal': end_date,
    'numeroTomo': '',
    'numeroPagina': '',
    'numeroEdicion': '',
    'numeroAnuncio': '',
    'tituloPublicacion': '',
    'numeroReciboPago': '',
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
        print(f'Downloading PDF with id {document["DocumentID"]}')
        
        # Metadata
        document_date = re.sub(r'(\d{2})/(\d{2})/(\d{4}) 00:00:00', r'\1\2\3', document['FechaPublicacion'])
        document_id = document["DocumentID"]

        # Get PDF content
        response = requests.get(f'https://legal.dca.gob.gt/GestionDocumento/DescargarPDFDocumento?idDocumento={document_id}')
        
        with open(f'/Users/santiagofacchini/Downloads/gt/{document_id}_{document_date}.pdf', 'wb') as pdf_file:
            pdf_file.write(response.content)
