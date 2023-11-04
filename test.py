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

## grafico

tr.heat_plot()
tr.line_plot()


# Chain ladder

tr.acumular()

tr.factores_desarrollo()

tr.fill()
tr.fill().line_plot()

tr.totales_año_siniestro()

tr.fit()
tr.fit().heat_plot()


# Métodos estocásticos

## Residuales
res = tr.residuales()
res

import matplotlib.pyplot as plt
import seaborn as sns
sns.kdeplot(res)
plt.grid()
plt.title('Estimación de la función de densidad de los residuales')
plt.ylabel('Densidad')
plt.show()


## Bootstrap


## Mack



