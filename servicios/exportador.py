import pandas as pd
import os

class Exportador:
    @staticmethod
    def exportar_a_excel(datos, columnas, nombre_archivo):
        if not os.path.exists('exportados'):
            os.makedirs('exportados')
        df = pd.DataFrame(datos, columns=columnas)
        ruta = os.path.join('exportados', nombre_archivo)
        df.to_excel(ruta, index=False)
        return ruta