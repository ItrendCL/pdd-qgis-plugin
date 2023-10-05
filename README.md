# QGIS Plugin para la Plataforma de Datos de Itrend

Este plugin permite descargar y cargar los conjuntos de datos de la [Plataforma de Datos](https://www.plataformadedatos.cl) directamente en [QGIS](https://www.qgis.org). El usuario debe proveer credenciales válidas y una ruta para descargar los archivos.

<img src="logo.svg" width="400px" height="auto">

- **Autor**: [Sebastián Castro](https://github.com/sebacastroh)
- **Version**: 1.0.0
- **Fecha**: 05 de octubre de 2023

# Descarga

Puedes descargar la última versión estable [aquí](https://github.com/ItrendCL/pdd-qgis-plugin/releases/download/v1.0.0/pdd-qgis-plugin.zip). Otras versiones de desarrollo están publicadas en la sección ```Releases```.

# Instalación

## Instalación directa a través de un zip

1. Descarga la versión más actual del plugin disponible arriba o en la sección ```Releases``` de GitHub ubicada a la derecha del sitio
2. En el menú superior de QGIS, abre la sección ```Complementos > Administrar e instalar complementos ...```
3. Selecciona la opción **Instalar a partir de ZIP** y selecciona el archivo descargado desde GitHub
4. Haz clic en **Instalar complemento**

Deberías encontrar el logo de Itrend en la sección superior de QGIS.

# Configuración

## Credenciales

1. Ingrese a la [sección de herramientas](https://www.plataformadedatos.cl/tools) de la Plataforma de Datos para obtener sus credenciales de acceso. Si no tiene cuenta, deberá crearse una antes.
2. Haga clic en ```Credenciales de acceso > Crear nuevas credenciales```. Seleccione la vigencia de las credenciales (máximo 90 días) y espere a obtener sus nuevas credenciales.
3. Descargue y guarde sus credenciales en un lugar seguro.
4. En QGIS, abra el complemento haciendo clic en el logo de Itrend. En el menú inferior, seleccione ```Configurar credenciales``` e ingrese las credenciales generadas previamente. Haga clic en aceptar para guardar los cambios.

Las credenciales quedan guardadas dentro de la configuración de QGIS. En caso de que sus credenciales caduquen, repita estos pasos. La aplicación le dará la opción de configurarlas nuevamente si detecta que no son válidas.

## Descargas

Todos los conjuntos de datos se deben descargar en alguna carpeta de su computadora. Para configurar la carpeta a utilizar siga los siguientes pasos

1. En QGIS, abra el complemento haciendo clic en el logo de Itrend. En el menú inferior, seleccione ```Configurar carpeta```.
2. Seleccione la carpeta donde se descargarán todos los archivos.

En caso de que un conjuto de datos ya haya sido descargado, la aplicación no realizará la descarga y abrirá el existente. Si desea actualizar el archivo con el más reciente de la Plataforma, puede eliminarlo o seleccionar la opción ```Forzar descarga``` en el plugin.

# Modo de uso

Se puede escoger uno o varios conjuntos de datos. En caso de ser colecciones, se descargará una tabla para escoger qué elemento de la colección se desea cargar

## Ventana principal
![image](https://user-images.githubusercontent.com/82397256/202242586-1becd118-e82d-4415-aeeb-bbb62fcdbbb7.png)

## Selección de un conjunto de datos
![image](https://user-images.githubusercontent.com/82397256/202243129-89ccd9e7-05df-41ef-8a65-735a72407e21.png)

## Ejemplo de una colección
![image](https://user-images.githubusercontent.com/82397256/202243341-e5f3ed96-bfc6-4b8e-83aa-6b15e024a422.png)
