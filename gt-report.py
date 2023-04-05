import ftplib
import os


ftp_host = os.environ['AG2_HOST']
ftp_user = os.environ['AG2_USER']
ftp_passwd = os.environ['AG2_PASS']

ftp_connection = ftplib.FTP(
    ftp_host,
    ftp_user,
    ftp_passwd,
)

ftp_connection.cwd('/descargas-rosario/gt')
available_files = ftp_connection.nlst()

if len(available_files) >= 1:
    files = []

    for file, facts in ftp_connection.mlsd():
        if not os.path.basename(file).startswith('.'):
            year = facts['modify'][:4]
            month = facts['modify'][4:6]
            day = facts['modify'][6:8]
            hour = int(facts['modify'][9:10]) - 3 # Set local timezone -> 3hs difference
            minute = facts['modify'][10:12]

            output_format = f'{file} - {day}/{month}/{year} 0{hour}:{minute}'

            files.append(output_format)

    print(f'Archivos en {ftp_user} /descargas-rosario/gt para ser cargados en la fuente 11510: {len(files)}\n')
    [print(x) for x in sorted(files, reverse=True)]

else:
    print(f'No hay archivos pendientes de carga.')

ftp_connection.close()
