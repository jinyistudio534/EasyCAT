EasyCAT HAT work with Node-red
![alt text](https://github.com/jinyistudio534/EasyCAT/blob/main/easycat_nodered/easycat_gateway_mbtcp_1.png "")

Please execute <b>node-udp-easycat3232.py</b> first and then execute <b>sudo node-red</b>

Required python library

[aioudp](https://pypi.org/project/aioudp/)

[spidev](https://pypi.org/project/spidev/)

[RPi.GPIO](https://pypi.org/project/RPi.GPIO/)

Required Node-red library

[@redplc/node-red-redplc](https://flows.nodered.org/node/@redplc/node-red-redplc)

[node-red-contrib-pythonshell](https://flows.nodered.org/node/node-red-contrib-pythonshell)

[node-red-contrib-queue-gate](https://flows.nodered.org/search?term=node-red-contrib-queue-gate) ** Not necessary, can be removed by yourself

[node-red-contrib-node-line-api](https://flows.nodered.org/node/node-red-contrib-node-line-api) ** Not necessary, can be removed by yourself

Modbus tcp/rtu Slave Simulator Installer

[Slave Simulators (MS Windows)](https://www.hmisys.com/downloads/PeakHMISlaveSimulatorInstall.exe)
