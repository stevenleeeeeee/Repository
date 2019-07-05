```bash
{
	"name": "mynet",
	"type": "macvlan",			#类型，这里指定为macvlan
	"master": "eth0",			#宿主机接口名称
	"ipam": {					#?????
		"type": "host-local",
		"subnet": "10.0.0.0/17",
		"rangeStart": "10.0.64.1",
		"rangeEnd": "10.0.64.126",
		"gateway": "10.0.127.254",
		"routes": [{
				"dst": "0.0.0.0/0"
			},
			{
				"dst": "10.0.80.0/24",
				"gw": "10.0.0.61"
			}
		]
	}
}
```