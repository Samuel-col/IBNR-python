# Crear triangulo de siniestros de IBNR

# librerías
import pandas as pd
import numpy as np
import plotnine as p9
import copy as cp
import scipy.stats as st

class Triangulo:

    # Creación
    def __init__(self,df,col_f_siniestro,
                col_f_desarrollo,col_valor = None):

        # Año de siniestro
        df['Año Siniestro'] = pd.to_datetime(
            df[col_f_siniestro]
        ).dt.year

        # Año de desarrollo
        df['Año Desarrollo'] = np.floor(pd.to_timedelta(
            df[col_f_desarrollo] - df[col_f_siniestro]
        ).dt.days/364.242).astype('int')

        # Crear tabla de contingencia
        if col_valor is None:
            self.tipo = 'Conteos'
            tab = pd.crosstab(df['Año Siniestro'],
                df['Año Desarrollo'])
        else:
            self.tipo = 'Costos'
            tab = pd.crosstab(df['Año Siniestro'],
                df['Año Desarrollo'],
                values = df[col_valor],
                aggfunc = 'sum')
            tab.replace(np.nan,0,inplace = True)
        
        self.df = tab
        self.años_siniestro = list(tab.index)
        self.años_desarrollo = list(tab.columns)
        self.array = np.array(tab)
    
    # Visualización
    def __str__(self):
        return self.df.__str__()
    
    def __repr__(self):
        return self.df.__repr__()

    # Actualizar atributos con base en df
    def __update(self):
        self.años_siniestro = list(self.df.index)
        self.años_desarrollo = list(self.df.columns)
        self.array = np.array(self.df)

    # Actualizar df con los demás atributos
    def __update_df(self):
        indices = pd.Index(self.años_siniestro,dtype = np.int32,name = 'Año Siniestro')
        columnas = pd.Index(self.años_desarrollo,dtype = np.int32, name = 'Año Desarrollo')
        self.df = pd.DataFrame(data = self.array,
                               index = indices,
                               columns = columnas)

    # Limpiar triangulo inferior
    def __limpiar_tri_inf(self):
        n, m = self.array.shape
        for i in range(m):
            self.array[(n-i):,i] = 0
        self.__update_df()

    # Indexar triángulo observado
    def __indexar_observado(self,diagonal = True):
        indices_r = []
        indices_c = []
        n, m = self.array.shape
        adj = 0 if diagonal else 1
        for i in range(m - 1):
            indices_r += list(range(n - i - adj))
            indices_c += [i]*(n - i - adj)
        indices = (np.array(indices_r),np.array(indices_c))
        return indices

    # Formato tabla
    def formato_largo(self):
        return self.df.stack().reset_index().rename(columns = {0 : self.tipo})
    
    # Gráficos
    def heat_plot(self,titulo = "Triángulo de Siniestros",separacion = 0.05):
        return p9.ggplot(self.formato_largo()) + p9.aes(
    'Año Desarrollo','Año Siniestro',fill = self.tipo) + p9.geom_tile(
        p9.aes(width= 1 - separacion, height= 1 - separacion)) + p9.scale_y_reverse() + p9.theme_light() + p9.labs(
            title = titulo)
    
    def line_plot(self,titulo = "Evolución de los Siniestros"):
        tmp_tab = self.formato_largo().copy()
        tmp_tab['Año Desarrollo'] += tmp_tab['Año Siniestro']
        tmp_tab['Año Siniestro'] = pd.Categorical(tmp_tab['Año Siniestro'])
        return p9.ggplot(tmp_tab) + p9.aes(
        'Año Desarrollo',self.tipo,color = 'Año Siniestro',
        group = 'Año Siniestro') + p9.geom_line() + p9.labs(
            title = titulo) + p9.theme_light()

    # Acumular
    def acumular(self,limpiar_tri_inferior = True):
        t = cp.deepcopy(self)
        for i in t.años_desarrollo[1:]:
            t.df[i] += t.df[i-1]
        t.__update()
        if limpiar_tri_inferior:
            t.__limpiar_tri_inf()
        return t
    
    # Desacumular
    def desacumular(self,limpiar_tri_inferior = True):
        t = cp.deepcopy(self)
        for i in t.años_desarrollo[1:]:
            j = max(t.años_desarrollo) - i
            t.df[j+1] -= t.df[j]
        t.__update()
        if limpiar_tri_inferior:
            t.__limpiar_tri_inf()
        return t

    # Factores de desarrollo: https://actuaries.asn.au/Library/accomp04papergerigk.pdf
    def factores_desarrollo(self):
        t_accu = self.acumular()
        a = t_accu.array
        n, m = a.shape
        factores = [np.sum(a[:(n-i),i])/np.sum(a[:(n-i),i-1]) for i in range(1,m)]
        return factores
    
    # Varianzas: https://actuaries.asn.au/Library/accomp04papergerigk.pdf
    def __varianzas(self):
        factores = self.factores_desarrollo()
        t_accu = self.acumular()
        a = t_accu.array
        n, m = a.shape
        sigmas = [np.sum((a[:(n-i),i-1]*(a[:(n-i),i]/a[:(n-i),i-1]) - factores[i-1])**2)/(n-i) for i in range(1,m)]
        return sigmas

    # Llenar triangulo
    def fill(self):
        factores = self.factores_desarrollo()
        S = self.acumular()
        n, m = S.array.shape
        for i in range(1,m):
            S.array[(n-i):,i] = factores[i-1]*S.array[(n-i):,i-1]
        S.__update_df()
        return S.desacumular(limpiar_tri_inferior = False)
    
    def totales_año_siniestro(self,return_series = True):
        S_filled = self.fill().array
        tots = np.sum(S_filled,axis = 1)
        if return_series:
            indice = pd.Index(self.años_siniestro, 
                              dtype = np.int32, 
                              name = 'Año Siniestro')
            return pd.Series(tots,index = indice)
        else:
            return tots

    # Ajustar triangulo
    def fit(self): 
        factores = self.factores_desarrollo()
        S = self.fill().acumular()
        n, m = S.array.shape
        for i in range(m-1):
            S.array[:(n-i-1),i] = S.array[:(n-i-1),i+1]/factores[i]
        S = S.desacumular()
        S.__update_df()
        return S

    # Extraer residuales
    def residuales(self):
        # Ajustar Chain Ladder
        S_fit = self.fit()
        # indexar observaciones estimadas
        indices = self.__indexar_observado(diagonal=False)
        # Extrar observado y predicho
        s_vals = self.array[indices]
        s_fits = S_fit.array[indices]
        # Calcular residuales
        res = (s_vals - s_fits)/np.sqrt(s_fits)
        return res

    # Bootstrap
    def bootstrap(self,n_reps = 5000,parametric = False,
                  parametric_distribution = 'Normal',
                  smoothed = True, alpha = 0.05,
                  ancho_barra = 50,seed = 1):
        
        # Ajustar triángulo
        S_fitted = self.fit()

        # Extraer residuales
        residuales = self.residuales()
        n_res = len(residuales)

        # Indexar observado
        indices_observado = self.__indexar_observado()

        # Crear muestreador
        if parametric:
            res_mean, res_std = np.mean(residuales), np.std(residuales,ddof = 1)
            if parametric_distribution == 'Normal': # Bootstrap paramétrico normal
                def sampler():
                    return st.norm.rvs(loc = res_mean, scale = res_std, size = n_res)
            elif parametric_distribution == 't': # Bootstrap parametrico t
                def sampler():
                    return st.t.rvs(df = n_res - 1, size = n_res)*res_std + res_mean
            else:
                print('Sólo se soportan las distribuciones Normal y t.')
                ValueError
        else:
            if smoothed: # Bootstrap no paramétrico suavizado
                def sampler():
                    smooth_degree = (np.max(residuales) - np.min(residuales))/(n_res*2)
                    new_res = np.random.choice(residuales,size = n_res,replace = True)
                    new_res += np.random.random(size = n_res)*smooth_degree - 0.5*smooth_degree
                    return  new_res
                        
            else: # Bootstrap no paramétrico
                def sampler():
                    return np.random.choice(residuales,size = n_res,replace = True)
        
        # Iterar
        muestras = []
        np.random.seed(seed)
        for b in range(n_reps):
            # Remuestrear
            new_S = cp.deepcopy(S_fitted)
            new_res = sampler()
            new_S.array[indices_observado] += new_res*np.sqrt(new_S.array[indices_observado])
            new_S.__update_df()
            # Calcular y guardar totales
            tots = new_S.totales_año_siniestro(return_series = False)
            muestras += [tots]
            # Reportar progreso
            eq_fill = np.floor(ancho_barra*(b+1)/n_reps)
            print('[',''.join(['=']*int(eq_fill)),''.join([' ']*int(ancho_barra - eq_fill)),'] ',b+1,'/',n_reps,end = '\r',sep = '')
        
        # Muestras
        muestras = np.array(muestras)
        totales = np.sum(muestras,axis = 1)

        # Calcular cuantiles 1-alpha
        uppers = np.quantile(muestras,q = 1-alpha,
                             axis = 1)
        upper_total = np.quantile(totales,q = 1-alpha)

        # Organizar resultados
        est_puntual = list(self.totales_año_siniestro(return_series=False))
        est_puntual += [sum(est_puntual)]
        est_superior = list(uppers) + [upper_total]
        indice = pd.Index(self.años_siniestro + ['Total'],dtype = str,name = 'Año Siniestro')
        resultados = pd.DataFrame({'Estimación Puntual' : est_puntual,
                                   'Límite Superior' : est_superior},
                                   index = indice)
        
        return resultados


    
    # Mack: https://actuaries.asn.au/Library/accomp04papergerigk.pdf
    def mack(self,alpha = 0.05):
        return 0

        

