# Descripción
Auto auditor de vulnerabilidades en un entorno dockerizado.
- Los módulos a probar están en **rc.json**.
- Los ficheros de configuración de los contenedores se encuentran en **VulMach**.
- A la espera de una nueva versión del wrapper de msfrpc (**pymetasploit3**)

# Requisitos
La cuenta desde la cual se ejecuta el script debe pertenecer al grupo **docker** de manera
que pueda acceder a la API sin permisos de superusuario.

# Preparación del entorno de pruebas
> cd config && ./setup.sh
- Prepara los contenedores con vulnerabilidades y el servidor VPN.
## Opcional
> curl -sSL https://bit.ly/2ysbOFE | bash -s -- 2.1.1 1.4.7
- Descarga los binarios y ficheros de prueba para crear una red de hyperledger fabric.
> cp ../hyperledger/autoauditor\_chaincode/chaincode.sh fabric-samples/test-network
- Copia el fichero de configuración de la blockchain.
> cp -R ../hyperledger/autoauditor\_chaincode/ fabric-samples/chaincode
- Copia los ficheros con el chaincode de autoauditor.
> cd fabric-samples/test-network && ./chaincode.sh -u -a -r && cd -
- Ejecuta el script que se encarga de instalar el SmartContract en la blockchain.
> docker run --rm -d --name docker-resolver -v /var/run/docker.sock:/tmp/docker.sock -v /etc/hosts:/tmp/hosts dvdarias/docker-hoster
- Será necesario instanciar un contenedor que sirva como DNS local y resuelva los nombres
de los demás contenedores.

# Ejecución
> source autoauditor\_venv/bin/activate
<!-- -->
> python ../autoauditor/autoauditor.py -v client.ovpn -r rc5.json -o output/msf.log -d output/loot -hc network.template.json -ho output/blockchain.log
- Ejecuta autoauditor usando los módulos listados en **rc.json**.
- Crea un túnel VPN con la configuración presente en **client.ovpn**.
- Guarda un registro de ejecución en el fichero **msf.log** presente en el directorio **output**.
- La información recolectada se guardará en el directorio **loot** presente en el directorio **output**.
- Almacena el reporte generado en la blockchain de hyperledger indicada en el fichero de configuración **network.json**.
- Registra los reportes almacenados en la blokchain en el fichero **blockchain.log** presente en el directorio **output**.

# Salida
- La salida de metasploit framework (community) separada por módulos se encuentra en el fichero **output/msf.log**.
- La información recolectada durante la ejecución se encuentra en el directorio **output/loot**.
- En la blockchain indicada por **network.json** se almacenarán los reportes generados usando como identificador sha256(orgName+reportDate).
- Un registro de los reportes almacenados en la blockchain en **output/blockchain.log**.

# Limpieza del entorno
> deactivate
<!-- -->
> ./setup.sh -s
<!-- -->
> cd fabric-samples/test-network && ./chaincode.sh -d && cd -

# Entornos virtuales
La ejecución se realiza en un entorno virtual, sin embargo, es necesario que la cuenta de usuario desde
la que se ejecuta la herramienta pertenezca al grupo **docker** para que se pueda comunicar
con la API.

# Posibles problemas, causas y soluciones
- Missing 'proposalResponses' parameter in transaction request.
> Error que se obtiene al tratar de realizar una transacción en la blockchain.
<!-- -->
> **Solución:** Borrar la carpeta wallet-test del directorio desde el que se ejecuta autoauditor.

- FileNotFoundError: [Errno 2] No such file or directory:
> Error obtenido justo al ejecutar autoauditor.
<!-- -->
> **Solución:** Comprueba que la blockchain esté correctamente instanciada, si es así, comprueba que el fichero
de configuración de la blockchain tiene los path bien definidos.

- status = StatusCode.UNAVAILABLE<br>details = "DNS resolution failed"
> Error al tratar de realizar cualquier petición contra la blockchain.
<!-- -->
> **Solución:** Comprueba que tienes conexión a los nodos (peer) de la blockchain. Si estás usando el entorno de pruebas,
entonces comprueba que el contenedor docker-resolver está ejecutándose.
