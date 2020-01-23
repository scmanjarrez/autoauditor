Descripción

	Auto auditor de vulnerabilidades en un entorno dockerizado
	- Los módulos a probar están en rc.json
	- Los CVEs ya están bajados 
	- Se espera una nueva versión del wrapper de msfrpc


Requisitos
	Necesita una versión de python 3.6 o superior, donde estén soportados los f-strings.
	Además necesita 
		- pymetasploit3
		- docker

	Instalar con pip3 install -r requirements.txt

Preparar el entorno con
	bash ./setup.sh

Ejecutar con
	python3 ./auditor.py -v client.ovpn

Salida
	La salida de metasploit framework (community) separada por exploits se encuentra en el fichero msf.log. 
	La carpeta loot contiene la información obtenida de la ejecución de los exploits.

Limpiar el entorno con 
	./setup.sh -s

Entornos virtuales
	En principio se diseñó para ejecutar en un entorno virtual, pero son necesario privilegios 
	para acceder al API de docker.


	

