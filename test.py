# Prueba de las funciones de los script de 01 a 09

# import os
# os.getcwd()
# path = 'C:\\Users\\SHSANCHE\\OneDrive - Proteccion S.A\\Procesos Actuaría\Practicante\\2023-01\\Proyecto IBNR\\'
# os.chdir(path)

import IBNR

# s01_simular_siniestros.py

n_años, n_años_desarrollo = 10, 10

IBNR.simular_siniestros(n_años,n_años_desarrollo,
                        parametros = {'p' : 0.1,
                                      'shape' : 200,
                                      'rate' : 5,
                                      'E(#siniestros)' : 8000})

df_siniestros = IBNR.simular_siniestros(n_años,n_años_desarrollo,
                                        seed = 2,
                                        parametros = {'p' : 0.2,
                                                      'shape' : 200,
                                                      'rate' : 5,
                                                      'E(#siniestros)' : 1000000})
df_siniestros.head()

# s02_crear_triangulos.py

IBNR.Triangulo(df_siniestros,'Fecha Siniestro','Fecha Desarrollo','Valor Siniestro')
tr = IBNR.Triangulo(df_siniestros,'Fecha Siniestro','Fecha Desarrollo')

tr

tr.formato_largo()

# Aplicar función
import numpy as np
tr.apply(np.log) #logaritmo natural
tr.apply(lambda x: 2*x) # duplicar

# exportar a excel
type(tr)
type(tr.to_DataFrame())
tr.to_excel('triangulo_simulado.xlsx')
tr.to_excel('triangulo_simulado.xlsx',startrow = 3)

## grafico
tr.heat_plot()
tr.line_plot()
tr.acumular().line_plot()


# Chain ladder

tr.acumular()

tr.factores_desarrollo()

tr.fill()
tr.fill().line_plot()
tr.fill().to_excel('triangulo_lleno.xlsx')

tr.totales_año_siniestro()


# Métodos estocásticos

## Residuales
res_tr = tr.residuales(retornar_triangulo=True)
res_tr.heat_plot()
res_tr.line_plot()
res = tr.residuales()
res

import matplotlib.pyplot as plt
import seaborn as sns
sns.kdeplot(res)
plt.grid()
plt.title('Estimación de la función de densidad de los residuales')
plt.ylabel('Densidad')
plt.show()

plt.plot(res)
plt.show()


## Bootstrap


samps = tr.bootstrap(n_reps=500,retornar_muestras=True)
import numpy as np
np.vstack((np.mean(samps,axis = 0),
tr.totales_año_siniestro(retornar_series=False))).T



tr.bootstrap(n_reps=500)
tr.bootstrap(n_reps=500,suavizado=True)
tr.bootstrap(n_reps=500,parametrico=True)
tr.bootstrap(n_reps=500,parametrico=True,distribucion_parametrica='t')

## Mack


#-----------------------------------------------------------------------
## Tabla 1: Mack (1993) https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=c449e39e64fd29b9aac7dd9266b841aa7ebc17ac

import IBNR
import numpy as np
import pandas as pd


tab1 = [
[357848, 1124788, 1735330, 2218270, 2745596, 3319994, 3466336, 3606286, 3833515, 3901463],
[352118, 1236139, 2170033, 3353322, 3799067, 4120063, 4647867, 4914039, 5339085, 0],
[290507, 1292306, 2218525, 3235179, 3985995, 4132918, 4628910, 4909315, 0, 0],
[310608, 1418858, 2195047, 3757447, 4029929, 4381982, 4588268, 0, 0, 0],
[443160, 1136350, 2128333, 2897821, 3402672, 3873311, 0, 0, 0, 0],
[396132, 1333217, 2180715, 2985752, 3691712, 0, 0, 0, 0, 0],
[440832, 1288463, 2419861, 3483130, 0, 0, 0, 0, 0, 0],
[359480, 1421128, 2864498, 0, 0, 0, 0, 0, 0, 0],
[376686, 1363294, 0, 0, 0, 0, 0, 0, 0, 0],
[344014, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

tr_acumulado = IBNR.Triangulo(triangulo = np.array(tab1),
                              años_desarrollo=range(1,11),
                              años_siniestro=range(1,11),tipo='Conteos')

tr = tr_acumulado.desacumular()

tr.heat_plot()
tr.line_plot()

tr.factores_desarrollo()
np.array(tr.varianzas())/1000

tr.totales_año_siniestro()

reserva = tr.totales_año_siniestro() - np.sum(tr.array,axis = 1)
reserva/1000
np.sum(reserva)/1000

samps = tr.bootstrap(retornar_muestras=True)
(np.std(samps,axis = 0,ddof = 1)/reserva)*100

tr.fill().acumular(limpiar_tri_inferior=False).array[:,9]**2

tr.limite_superior_totales()/1000000
tr.bootstrap()/1000000
tr.bootstrap(parametrico=True,distribucion_parametrica='Normal')/1000000

tr.reserva(metodo='Mack')

np.array(tr.limite_superior_totales())[:-1]/reserva


np.array(tr.varianzas())/np.array(tr.factores_desarrollo())**2




