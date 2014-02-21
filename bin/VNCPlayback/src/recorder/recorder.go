package recorder

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"log"
	"net"
	"os"
	"unsafe"
)

const (
	RECV_BUF_LEN = 1024
)

type VMInfo struct {
	Host      [64]byte
	VMRef     [128]byte
	StartTime [64]byte
}

type Head struct {
	Type       int32
	TimeDelta  uint32
	BodyLength uint32
}

func Runmain() {
	println("Starting the Rcorder server")

	listener, err := net.Listen("tcp", "0.0.0.0:6666")
	if err != nil {
		println("error listening:", err.Error())
		os.Exit(1)
	}

	for {
		conn, err := listener.Accept()
		if err != nil {
			println("Error accept:", err.Error())
			return
		}
		go Handler(conn)
	}
}

func Handler(conn net.Conn) {
	var vm_info VMInfo
	const vm_info_size = unsafe.Sizeof(vm_info)

	var head Head
	const headSize = unsafe.Sizeof(head)

	buf := make([]byte, vm_info_size)
	_, err := conn.Read(buf)
	if err != nil {
		println("Error reading:", err.Error())
		return
	}

	err = binary.Read(bytes.NewBuffer(buf), binary.LittleEndian, &vm_info)
	if err != nil {
		log.Print(err)
		return
	}

	host := string(vm_info.Host[:])
	vm_ref := string(vm_info.VMRef[:])
	start_time := string(vm_info.StartTime[:])

	fmt.Sprintf("%s_%s_%s.dat", host, vm_ref, start_time)
	file, err := os.OpenFile("p.dat", os.O_RDWR|os.O_CREATE, 0644)
	if err != nil {
		log.Print(err)
		return
	}

	for {
		size := int64(headSize)
		var n int

		buf, n, err = read(conn, int(size))
		if err != nil {
			log.Print(err)
			return
		}
		if n != int(size) {
			log.Print("invalid head size")
			return
		}

		err = binary.Read(bytes.NewBuffer(buf), binary.LittleEndian, &head)
		if err != nil {
			log.Print(err)
			return
		}

		file.Write(buf)

		buf, n, err = read(conn, int(head.BodyLength))
		if err != nil {
			log.Print(err)
			return
		}

		fmt.Println(n, "***", head.BodyLength)
		if n != int(head.BodyLength) {
			log.Print("invalid body size")
			return
		}

		file.Write(buf)
	}

	/*
		//send reply
		_, err = conn.Write(buf)
		if err != nil {
			println("Error send reply:", err.Error())
		} else {
			println("Reply sent")
		}
	*/
}

func read(conn net.Conn, length int) ([]byte, int, error) {
	data := make([]byte, length)
	buf_size := 1024
	buf := make([]byte, buf_size)
	i := 0
	for {
		if length < buf_size {
			if length == 0 {
				return data, i, nil
			}
			remain := make([]byte, length)
			r, err := conn.Read(remain)
			if err != nil {
				return nil, i, err
			}
			copy(data[i:(i+r)], remain[0:r])
			i += r
			length -= r
		} else {
			r, err := conn.Read(buf)
			if err != nil {
				return nil, i, err
			}
			copy(data[i:(i+r)], buf[0:r])
			i += r
			length -= r
		}
	}
	return data, i, nil
}
