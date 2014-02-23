package recorder

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"time"
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

type HeadReply struct {
	Status int32
}

func GetValidByte(src []byte) []byte {
	var str_buf []byte
	for _, v := range src {
		if v != 0 {
			str_buf = append(str_buf, v)
		}
	}
	return str_buf
}

func Handler(conn net.Conn) {
	var vm_info VMInfo
	const vm_info_size = unsafe.Sizeof(vm_info)

	var head Head
	const headSize = unsafe.Sizeof(head)

	// set read deadline
	conn.SetReadDeadline(time.Now().Add(3 * time.Second))
	conn.SetWriteDeadline(time.Now().Add(3 * time.Second))

	// Receive Head information from client
	log.Println("Recorder Server: Receive Head information from client")
	buf := make([]byte, vm_info_size)
	n, err := io.ReadFull(conn, buf)
	if neterr, ok := err.(net.Error); ok && neterr.Timeout() {
		log.Print("Recorder Server: Timeout reading Head Info: ", err.Error())
		return
	}
	if err != nil {
		log.Print("Recorder Server: Error reading Head Info: ", err.Error())
		return
	}
	if n != int(vm_info_size) {
		log.Print("Recorder Server: Read VMInfo head error.")
		return
	}

	err = binary.Read(bytes.NewBuffer(buf), binary.LittleEndian, &vm_info)
	if err != nil {
		log.Print("Recorder Server: Parse VMinfo failed: ", err)
		return
	}
	log.Println("Recorder Server: OK")

	// Send HeadReply to client
	log.Println("Recorder Server: Send HeadReply to client")
	var head_reply HeadReply
	head_reply.Status = 0
	reply_buf := new(bytes.Buffer)

	err = binary.Write(reply_buf, binary.LittleEndian, head_reply)
	if err != nil {
		log.Println("Recorder Server: binary.Write failed: ", err)
		return
	}

	n, err = conn.Write(reply_buf.Bytes())

	if neterr, ok := err.(net.Error); ok && neterr.Timeout() {
		log.Print("Recorder Server: Timeout Write HeadReply: ", err.Error())
		return
	}
	if err != nil {
		log.Println("Recorder Server: Write HeadReply to client failed: ", err)
		return
	}
	log.Println("Recorder Server: OK")

	host := string(GetValidByte(vm_info.Host[:]))
	vm_ref := string(GetValidByte(vm_info.VMRef[:]))
	start_time := string(GetValidByte(vm_info.StartTime[:]))

	// Open Record file to write
	fname := fmt.Sprintf("./data/%s_%s_%s.dat", host, vm_ref, start_time)
	file, err := os.Create(fname)
	if err != nil {
		log.Print("Recorder Server: Open Data file failed: ", err)
		return
	}

	// cancel the socket deadline
	var zero time.Time
	conn.SetReadDeadline(zero)
	conn.SetWriteDeadline(zero)

	log.Print("Recorder Server: Receive VNC Data from client.")
	// Receive VNC Data from client
	for {
		size := int64(headSize)
		var n int

		// Receive VNC Data Head from client
		buf = make([]byte, size)

		n, err = io.ReadFull(conn, buf)

		if err == io.EOF {
			log.Printf("Recorder Server: Client %s disconnected while read head.", conn.RemoteAddr())
			return
		}

		if err != nil {
			log.Print("Recorder Server: Error reading Data head: ", err)
			break
		}
		if n != int(size) {
			log.Print("Recorder Server: Invalid data head size")
			break
		}

		err = binary.Read(bytes.NewBuffer(buf), binary.LittleEndian, &head)
		if err != nil {
			log.Print("Recorder Server: Parse Data head failed: ", err)
			break
		}

		n, err = file.Write(buf)
		if err != nil {
			log.Print("Recorder Server: Error Write Data head: ", err)
			break
		}
		if n != int(size) {
			log.Print("Recorder Server: Invalid data while write head size")
			break
		}

		// // Receive VNC Data Body from client
		buf = make([]byte, head.BodyLength)

		n, err := io.ReadFull(conn, buf)

		if err == io.EOF {
			log.Printf("Recorder Server: Client %s disconnected while read body.", conn.RemoteAddr())
			return
		}

		if err != nil {
			log.Print("Recorder Server: Error reading Data Body: ", err)
			break
		}
		if n != int(head.BodyLength) {
			log.Print("Recorder Server: invalid body size")
			break
		}

		n, err = file.Write(buf)
		if err != nil {
			log.Print("Recorder Server: Error Write Data Body: ", err)
			break
		}
		if n != int(head.BodyLength) {
			log.Print("Recorder Server: Invalid data while write body size")
			break
		}
	}

	log.Printf("Recorder Server: Client %s disconnected.", conn.RemoteAddr())
}

func StartRecorder() {
	log.Print("Recorder Server: Listen on TCP 0.0.0.0:23457")

	listener, err := net.Listen("tcp", "0.0.0.0:23457")
	if err != nil {
		log.Print("Recorder Server: error listening:", err.Error())
		os.Exit(1)
	}

	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Print("Recorder Server: Error accept:", err.Error())
			return
		}
		go Handler(conn)
	}
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
