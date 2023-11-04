# Simulación de data frame con siniestros para el IBNR

# librerías
import numpy as np
import pandas as pd
import scipy.stats as st
import datetime as dt
import numbers as nb

def _fecha_aleatoria(año):
    day_number = np.random.randint(1,366)
    if isinstance(año,nb.Number):
        fecha = dt.date(año,1,1)
    elif type(año) == dt.date:
        fecha = año
    else:
        ValueError
    return fecha + dt.timedelta(day_number)

def simular_siniestros(n_años,
                       n_años_desarrollo,seed = 1,
                       parametros = {'p' : 0.15,
                                     'shape' : 250,
                                     'rate' : 4,
                                     'E(#siniestros)' : 10000}):
    
    np.random.seed(seed)
    # Cantidad final de siniestros
    n_siniestros = np.random.poisson(parametros['E(#siniestros)'])

    # Años de siniestro
    hoy = dt.date.today()
    años_siniestros = np.sort([hoy.year - i for i in range(n_años)])
    
    # Simulación
    int_años_siniestros = np.random.choice(años_siniestros,size = n_siniestros)
    col_fechas_siniestros = [_fecha_aleatoria(int_años_siniestros[i]) for i in range(n_siniestros)]
    int_años_desarrollo = np.random.binomial(n_años_desarrollo,parametros['p'],size = n_siniestros)
    col_fechas_desarrollo = [_fecha_aleatoria(col_fechas_siniestros[i] + dt.timedelta(int(365.242*int_años_desarrollo[i]))) for i in range(n_siniestros)]
    col_valor_siniestro = st.gamma.rvs(a = parametros['shape'], scale = 1/parametros['rate'], size = n_siniestros)

    # Crear dataframe
    df = pd.DataFrame({'Fecha Siniestro' : col_fechas_siniestros,
                       'Fecha Desarrollo' : col_fechas_desarrollo,
                       'Valor Siniestro' : col_valor_siniestro})
    
    # Filtrar triangulo
    df = df[df['Fecha Desarrollo'] <= hoy]
    
    return df