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
tr.bootstrap(n_reps=500,parametric=True)
tr.bootstrap(n_reps=500,parametric=True,parametric_distribution='t')

## Mack



