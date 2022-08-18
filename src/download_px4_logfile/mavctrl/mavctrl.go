package mavctrl

import (
	"fmt"
	"log"
	"regexp"

	"github.com/aler9/gomavlib"
	"github.com/aler9/gomavlib/pkg/dialects/common"
)

type MavlinkControl struct {
	node      *gomavlib.Node
	Connected bool
}

//func validate_address(addr string) (string, string, bool) {

func validate_address(addr string) (string, string, bool) {
	re := regexp.MustCompile(`(.*:)?((([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+))?:([0-9]+))$`)
	matches := re.FindStringSubmatch(addr)
	addr_ok := true

	conn_type := ""
	ip_address := ""
	ip_port := ""

	/*
		log.Printf("[mavctrl] matches len: %d\n", len(matches))
		for i := 0; i < len(matches); i++ {
			log.Printf("[mavctrl] +--- matches[%d]: %s\n", i, matches[i])
		}
	*/

	log.Printf("[mavctrl] matches len: %d\n", len(matches))
	if len(matches) == 9 {
		// Verify connection type
		switch matches[1] {
		case "tcp:":
			conn_type = "tcp"
		case "udp:":
			conn_type = "udp"
		case "":
			// Set udp is connection type not given
			log.Printf("[mavctrl] Connection type not given, default to udp\n")
			conn_type = "udp"
		default:
			log.Println("[mavctrl] ERROR: Supported connection types are: [ udp | tcp ], e.g. tcp:127.0.0.1:1234")
			addr_ok = false
		}

		var num int32

		// Verify ip address
		if matches[3] != "" {
			for i := 4; i < 8; i++ {
				fmt.Sscan(matches[i], &num)
				if num < 0 || num > 255 {
					log.Println("[mavctrl] ERROR: Address must be IPv4 dot-decimal notation with four octets")
					addr_ok = false
					break
				}
			}
			ip_address = matches[3]
		} else {
			log.Print("[mavctrl] Address not given, default to 0.0.0.0")
			// Set localhost if address not given
			ip_address = "0.0.0.0"
		}

		// Verify port number
		fmt.Sscan(matches[5], &num)
		if num < 0 || num > 65535 {
			log.Print("[mavctrl] ERROR: Port number must be 16-bit value")
			addr_ok = false
		} else {
			ip_port = matches[8]
		}
	} else {
		log.Println("[mavctrl] ERROR: Port not given!")
		addr_ok = false
	}
	return conn_type, ip_address + ":" + ip_port, addr_ok
}

func (ctrl *MavlinkControl) Init(address string) bool {

	var err error

	// Parse address <type>:<ip_address>:<port>
	//  if type is missing, then use udp
	conn_type, validated_addr, ok := validate_address(address)
	if !ok {
		log.Println("[mavctrl] ERROR: Address and/or port not valid!")
		return false
	} else {
		log.Println("[mavctrl] Address and port valid")
	}

	// create a node which
	// - communicates with a TCP endpoint in client mode
	// - understands common dialect
	// - writes messages with given system id

	var endpoints []gomavlib.EndpointConf

	if conn_type == "tcp" {
		endpoints = []gomavlib.EndpointConf{gomavlib.EndpointTCPClient{validated_addr}}
	} else {
		endpoints = []gomavlib.EndpointConf{gomavlib.EndpointUDPServer{validated_addr}}
	}
	log.Printf("[mavctrl] Connecting to %s\n", validated_addr)
	ctrl.node, err = gomavlib.NewNode(gomavlib.NodeConf{
		Endpoints:   endpoints,
		Dialect:     common.Dialect,
		OutVersion:  gomavlib.V2,
		OutSystemID: 10,
	})
	if err != nil {
		log.Printf("[mavctrl] %s\n", err.Error())
		return false
	}

	for evt := range ctrl.node.Events() {
		if _, ok := evt.(*gomavlib.EventFrame); ok {
			ctrl.Connected = true
			log.Println("[mavctrl] Connected")
			break
		}
	}

	return ctrl.Connected
}

func (ctrl *MavlinkControl) Close() {
	ctrl.node.Close()
}
