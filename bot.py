from apscheduler.schedulers.blocking import BlockingScheduler
import requests
from PIL import Image, ImageDraw, ImageFont, ImageColor
import sqlite3
import time
import datetime as dt

sched = BlockingScheduler(timezone='America/Santiago')

@sched.scheduled_job('interval', id='send_welcome', seconds = 10)
def send_testplebiscito():
    r = requests.get('https://servelelecciones.cl/data/elecciones_constitucion/computo/global/19001.json')
    d = r.json()
    mesasescrutadas = d['mesasEscrutadas']
    totalmesaspercent = d['totalMesasPorcent']
    totalmesas = d['totalMesas']
    a_porcentaje = d['data'][0]['d']
    r_porcentaje = d['data'][1]['d']
    votosA = d['data'][0]['c']
    votosB = d['data'][1]['c']

    #Create DB
    with sqlite3.connect('data.db') as conn:
        c = conn.cursor()
        
        c.execute("""CREATE TABLE IF NOT EXISTS compare_data(
                        datetime TEXT,
                        a_porcentaje INTEGER,
                        votosA INTEGER)
                """)

                
        c.execute("""CREATE TABLE IF NOT EXISTS mesas_data(
                        datetime TEXT,
                        mesasescrutadas INTEGER,
                        totalmesaspercent INTEGER,
                        totalmesas INTEGER)
                """)    



    with sqlite3.connect('data.db') as conn:
        c = conn.cursor()
        for x in range(1):
            now = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute("INSERT INTO compare_data(datetime, a_porcentaje, votosA) VALUES (?, ?, ?)", (now, a_porcentaje, votosA))
            c.execute("INSERT INTO mesas_data(datetime, mesasescrutadas, totalmesaspercent, totalmesas) VALUES (?, ?, ?, ?)", (now, mesasescrutadas, totalmesaspercent, totalmesas))            
            conn.commit()
            time.sleep(1)

        sqlite_select_query = """SELECT * from mesas_data ORDER BY datetime DESC LIMIT 2"""

        mesas_percent = []
        for row in c.execute(sqlite_select_query):
            mesas_percent.append(row[2])
        c.close()

    if mesas_percent[0] == mesas_percent[1]:
        print('.')
    else:
        print('Hay nueva computo!: ' + now)
        label = ["", ""]
        val = [50,50]
        label.append("")
        val.append(sum(val))

        img = Image.open("media/plantillaplebiscito.png")
        d = ImageDraw.Draw(img)

        color = ImageColor.getrgb('#ffffff')
        colorA = ImageColor.getrgb('#a83232')
        colorR = ImageColor.getrgb('#3269a8')
        votos = ImageColor.getrgb('#000000')

        font = ImageFont.truetype('font/calibri-bold.ttf', size=170)
        fontlow = ImageFont.truetype('font/calibri-bold.ttf', size=50)
        fontvotos = ImageFont.truetype('font/calibri-bold.ttf', size=40)

        d.text((200, 620), a_porcentaje, font=font, fill=colorA)
        d.text((1300, 620), r_porcentaje, font=font, fill=colorR)
        d.text((100, 1300), 'Mesas escrutadas: '+ mesasescrutadas + ' ('+totalmesaspercent+')' + '\nmesas totales: ' + totalmesas, font=fontlow, fill=color)
        d.text((200, 780), votosA + ' votos', font=fontvotos, fill=votos)
        d.text((1300, 780), votosB + ' votos', font=fontvotos, fill=votos)
        d.text((1600, 1350), 'Fuente: SERVEL' , font=fontlow, fill=color)

        img.save('resultados.png')    
sched.start()