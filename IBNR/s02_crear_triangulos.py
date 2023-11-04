# Crear triangulo de siniestros de IBNR

# librerías
import pandas as pd
import numpy as np
import plotnine as p9
import copy as cp
import scipy.stats as st

class Triangulo: # https://alejandria.poligran.edu.co/bitstream/handle/10823/651/METODOLOGIAS%20DE%20CALCULO%20DE.....%20%28IBNR%29.pdf?sequence=2&isAllowed=y

    # --------------------------------------------------------
    # Creación -----------------------------------------------
    # --------------------------------------------------------

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
    
    # --------------------------------------------------------
    # Funciones internas -------------------------------------
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Utilidades generales -----------------------------------
    # --------------------------------------------------------

    # Formato tabla
    def formato_largo(self):
        return self.df.stack().reset_index().rename(columns = {0 : self.tipo})
    
    # Exportar a excel
    def to_excel(self,file_name,sheet_name = 'Hoja1',**kwargs):
        self.df.to_excel(file_name,sheet_name=sheet_name,
                         **kwargs)
    
    # Convertir a dataframe
    def to_DataFrame(self):
        return self.df

    # Aplicar función a las entradas del triangulo
    def apply(self,f,limpiar_tri_inferior = True):
        S = cp.deepcopy(self)
        S.array = f(S.array)
        S.__update_df()
        if limpiar_tri_inferior:
            S.__limpiar_tri_inf()
        return S

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

    # --------------------------------------------------------
    # Chain-Ladder y Mack ------------------------------------
    # --------------------------------------------------------

    # Factores de desarrollo: https://actuaries.asn.au/Library/accomp04papergerigk.pdf
    def factores_desarrollo(self):
        C = self.acumular()
        a = C.array
        n, m = a.shape
        factores = [np.sum(a[:(n-i),i])/np.sum(a[:(n-i),i-1]) for i in range(1,m)]
        return factores
    
    # Varianzas: 
    # * Gerigk: https://actuaries.asn.au/Library/accomp04papergerigk.pdf
    # * MatLab: https://www.mathworks.com/help/risk/bootstrap-using-chain-ladder-method.html
    # * Mack: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=c449e39e64fd29b9aac7dd9266b841aa7ebc17ac
    def varianzas(self):
        factores = self.factores_desarrollo()
        C = self.acumular()
        a = C.array
        n, m = a.shape
        sigmas = [np.sum(a[:(n-k-1),k]*(a[:(n-k-1),k+1]/a[:(n-k-1),k] - factores[k])**2)/(n-k-2) for k in range(m-1)]
        # sigmas += [min(sigmas[m-3]**2/sigmas[m-4], sigmas[m-3], sigmas[m-4])]
        return sigmas

    # Llenar triangulo
    def fill(self):
        factores = self.factores_desarrollo()
        C = self.acumular()
        n, m = C.array.shape
        for i in range(1,m):
            C.array[(n-i):,i] = factores[i-1]*C.array[(n-i):,i-1]
        C.__update_df()
        return C.desacumular(limpiar_tri_inferior = False)
    
    # Totales
    def totales_año_siniestro(self,retornar_series = True):
        S_filled = self.fill().array
        tots = np.sum(S_filled,axis = 1)
        if retornar_series:
            indice = pd.Index(self.años_siniestro, 
                              dtype = np.int32, 
                              name = 'Año Siniestro')
            return pd.Series(tots,index = indice,name = self.tipo)
        else:
            return tots
        
    # Mack: https://actuaries.asn.au/Library/accomp04papergerigk.pdf
    def mack(self,alpha = 0.05): # PENDIENTE
        return 0
    
    # --------------------------------------------------------
    # Bootstrap ----------------------------------------------
    # --------------------------------------------------------

    # Residuales
    def residuales(self,retornar_triangulo = False):
        # Variables necesarias
        n, m = self.array.shape
        factores = self.factores_desarrollo()
        sigmas2 = self.varianzas()
        indices = self.__indexar_observado(diagonal = False)
        C = self.acumular()
        e_tri = np.zeros((n,m-1))
        # Calcular residuales
        for i in range(1,m):
            j = m - i
            e_tri[:(n-j),j-1] = (C.array[:(n-j),j] - C.array[:(n-j),j-1]*factores[j-1])/(np.sqrt(C.array[:(n-j),j-1]*sigmas2[j-1]))
        # Extraer residuales
        if retornar_triangulo:
            e_triangulo = cp.deepcopy(self)
            e_triangulo.array = e_tri
            e_triangulo.años_desarrollo = self.años_desarrollo[1:]
            e_triangulo.__update_df()
            return e_triangulo
        else:
            return e_tri[indices]


    # Bootstrap: https://www.mathworks.com/help/risk/bootstrap-using-chain-ladder-method.html
    def bootstrap(self,n_reps = 5000,parametrico = False,
                  distribucion_parametrica = 'Normal',
                  suavizado = True, alpha = 0.05,
                  ancho_barra = 50,seed = 1,
                  retornar_muestras = False):
        
        n, m = self.array.shape
        # Ajustar triángulo
        factores = self.factores_desarrollo()
        sigmas2 = self.varianzas()

        # Extraer residuales
        residuales = self.residuales()
        n_res = len(residuales)

        # Indexar observado
        indices_observado = self.__indexar_observado(diagonal=False)

        # Crear muestreador
        if parametrico:
            res_mean, res_std = np.mean(residuales), np.std(residuales,ddof = 1)
            if distribucion_parametrica == 'Normal': # Bootstrap paramétrico normal
                def sampler():
                    return st.norm.rvs(loc = res_mean, scale = res_std, size = n_res)
            elif distribucion_parametrica == 't': # Bootstrap parametrico t
                def sampler():
                    return st.t.rvs(df = n_res - 1, size = n_res)*res_std + res_mean
            else:
                print('Sólo se soportan las distribuciones Normal y t.')
                ValueError
        else:
            if suavizado: # Bootstrap no paramétrico suavizado: https://www.math.wustl.edu/~kuffner/AlastairYoung/DeAngelisYoung1992b.pdf
                def sampler():
                    cantidad_de_suavizado = st.gaussian_kde(residuales).silverman_factor()
                    new_res = np.random.choice(residuales,size = n_res,replace = True)
                    new_res += np.random.normal(size = n_res)*cantidad_de_suavizado
                    return  new_res
                        
            else: # Bootstrap no paramétrico
                def sampler():
                    return np.random.choice(residuales,size = n_res,replace = True)
        
        # Iterar
        muestras = []
        e_tri = np.zeros((n,m-1)) # Triangulo de residuales
        np.random.seed(seed)
        for b in range(n_reps):
            # Remuestrear
            new_C = self.acumular()
            e_tri[indices_observado] = sampler()
            for j in range(1,m):
                if any(new_C.array[:(n-j),j-1] < 0):
                    print('NEGATIVO!!')
                new_C.array[:(n-j),j] = factores[j-1]*new_C.array[:(n-j),j-1] + np.sqrt(new_C.array[:(n-j),j-1]*sigmas2[j-1])*e_tri[:(n-j),j-1]
            # new_S.array[indices_observado] += new_res*np.sqrt(new_S.array[indices_observado]*sigmas2[indices_observado[1]])
            new_C.__update_df()
            # Calcular y guardar totales
            tots = new_C.totales_año_siniestro(retornar_series = False)
            muestras += [tots]
            # Reportar progreso
            eq_fill = np.floor(ancho_barra*(b+1)/n_reps)
            print('[',''.join(['=']*int(eq_fill)),''.join([' ']*int(ancho_barra - eq_fill)),'] ',b+1,'/',n_reps,end = '\r',sep = '')
        
        print()

        if retornar_muestras:
            return np.array(muestras)
        else:
            muestras = np.array(muestras)
            totales = np.sum(muestras,axis = 1)
            # Calcular cuantiles 1-alpha
            uppers = np.quantile(muestras,q = 1-alpha,
                                axis = 0)
            upper_total = np.quantile(totales,q = 1-alpha)

            # Organizar resultados
            est_puntual = list(self.totales_año_siniestro(retornar_series=False))
            est_puntual += [sum(est_puntual)]
            est_superior = list(uppers) + [upper_total]
            indice = pd.Index(self.años_siniestro + ['Total'],
                            dtype = str,name = 'Año Siniestro')
            resultados = pd.DataFrame({'Estimación Puntual' : est_puntual,
                                    'Límite Superior' : est_superior},
                                    index = indice)
        
            return resultados



        

