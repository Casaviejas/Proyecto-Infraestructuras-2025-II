import requests
import matplotlib.pyplot as plt

DATA_URL = "http://aggregator:5000/aggregate"

data = requests.get(DATA_URL).json()

dates = [d["date"] for d in data]
news = [d["news"] for d in data]
colcap = [d["colcap"] for d in data]

plt.figure()
plt.plot(dates, news)
plt.plot(dates, colcap)
plt.xlabel("Fecha")
plt.ylabel("Valor")
plt.title("Noticias vs COLCAP")
plt.savefig("/tmp/result.png")

print("Gráfico generado en /tmp/result.png")