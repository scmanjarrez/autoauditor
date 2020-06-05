# Descripción
Auto auditor de vulnerabilidades en un entorno dockerizado. 
- Los módulos a probar están en **rc.json**.
- Los ficheros de configuración de los contenedores se encuentran en **VulMach**.
- A la espera de una nueva versión del wrapper de msfrpc (**pymetasploit3**)

# Requisitos
La cuenta desde la cual se ejecuta el script debe pertenecer al grupo **docker** de manera
que pueda acceder a la API sin permisos de superusuario.

# Preparación del entorno de pruebas
- ./setup.sh
> Prepara los contenedores con vulnerabilidades y el servidor VPN.

# Ejecución
- source autoauditor\_venv/bin/activate
- python ../autoauditor/autoauditor.py -v client.ovpn -r rc.json -o output/msf.log -d output/loot -hc network.json
> Ejecuta autoauditor usando los módulos listados en **rc.json**.  
> Crea un túnel VPN con la configuración presente en **client.ovpn**.  
> Escribe toda la información de ejecución en el fichero **msf.log** presente en el directorio **output**.  
> La información recolectada se guardará en el directorio **loot** presente en el directorio **output**.  
> Guarda la información de ejecución en la blockchain de hyperledger usando la configuración presente en **network.json**. 

# Salida
- La salida de metasploit framework (community) separada por módulos se encuentra en el fichero **output/msf.log**.  
- La información recolectada durante la ejecución se encuentra en el directorio **output/loot**.
- En la blockchain indicada por **network.json** se almacenará los reportes generados usando como identificador sha256(orgName+reportDate).

# Limpieza del entorno
- deactivate
- ./setup.sh -s

# Entornos virtuales
La ejecución se realiza en un entorno virtual, sin embargo, es necesario que la cuenta de usuario desde 
la que se ejecuta la herramienta pertenezca al grupo **docker** para que se pueda comunicar
con la API.
