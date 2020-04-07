# Descripción
Auto auditor de vulnerabilidades en un entorno dockerizado. 
- Los módulos a probar están en **rc.json**.
- Los ficheros de configuración de los contenedores se encuentran en **VulMach**.
- A la espera de una nueva versión del wrapper de msfrpc (**pymetasploit3**)

# Requisitos
La cuenta desde la cual se ejecuta el script debe pertenecer al grupo **docker** de manera
que pueda acceder a la API sin permisos de superusuario.

# Preparación del entorno
- sudo ./setup.sh
> Prepara los contenedores con vulnerabilidades y el servidor VPN.
- ./gen\_venv.sh
> Crea un entorno virtual de python3 y descarga los módulos necesarios para la ejecución.

> Mientras se actualiza la versión de pymetasploit3, usar el entorno virtual ya preparado en _venv\_bk_.
> - **cp -R venv\_bk autoauditor\_venv**
> - **NO** ejecutes gen_venv.sh

# Ejecución
- sudo ./autoauditor_venv/bin/python ./autoauditor.py -v client.ovpn -r rc.json -o msf.log -d loot
> Ejecuta autoauditor usando los módulos listados en **rc.json**.  
> Crea un túnel VPN con la configuración presente en **client.ovpn**.  
> Escribe toda la información de ejecución en el fichero **msf.log**.  
> La información recolectada se guardará en el directorio **loot**.  

# Salida
La salida de metasploit framework (community) separada por módulos se encuentra en el fichero **msf.log**.  
La carpeta **loot** contiene la información obtenida durante la ejecución.

# Limpieza del entorno
- sudo ./setup.sh -s

# Entornos virtuales
En principio se diseñó para ejecutar en un entorno virtual, pero son necesario privilegios
para acceder al API de docker.

