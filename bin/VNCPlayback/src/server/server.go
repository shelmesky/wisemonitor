package main

import (
	"bytes"
	"code.google.com/p/go.net/websocket"
	"encoding/binary"
	"io"
	"log"
	"net/http"
	"os"
	"syscall"
	"time"
	"unsafe"
)

var (
	start_time int64
)

type Head struct {
	Type       int32
	TimeDelta  uint32
	BodyLength uint32
}

func getNowMillisecond() int64 {
	var tv syscall.Timeval
	syscall.Gettimeofday(&tv)
	return (int64(tv.Sec)*1e3 + int64(tv.Usec)/1e3)
}

func Recorder(ws *websocket.Conn) {
	//code
}

func Processor(ws *websocket.Conn) {
	var head Head
	const headSize = unsafe.Sizeof(head)

	start_time = getNowMillisecond()
	ws.PayloadType = 2

	file, err := os.Open("record.dat.2")
	if err != nil {
		log.Fatal(err)
		return
	}
	defer file.Close()

	for {
		size := int64(headSize)
		buf := make([]byte, size)

		n, err := file.Read(buf)
		if err != nil {
			log.Fatal(err)
			return
		}
		if n != int(size) {
			log.Fatal("invlid head size.")
			return
		}
		if err == io.EOF {
			log.Fatal("got EOF in Read head")
			return
		}

		err = binary.Read(bytes.NewBuffer(buf), binary.LittleEndian, &head)
		if err != nil {
			log.Fatal(err)
			return
		}

		buf = make([]byte, head.BodyLength)
		n, err = file.Read(buf)
		if err != nil {
			log.Fatal(err)
			return
		}
		if n != int(head.BodyLength) {
			log.Fatal("invlid body size.")
			return
		}
		if err == io.EOF {
			log.Fatal("got EOF in Read body")
			return
		}

        // ignore packet which send from ws client
		if head.Type == 1 {
			continue
		}

		now := getNowMillisecond()
		toffset := now - start_time

		var delay uint32
		if head.TimeDelta <= uint32(toffset) {
			delay = 1
		} else {
			delay = (head.TimeDelta) - uint32(toffset)
		}
		sleep := time.Duration(int(delay)) * time.Millisecond

		time.Sleep(sleep)

        n, err = ws.Write(buf)
        if err != nil {
            log.Fatal(err)
            return
        }
        if n != int(head.BodyLength) {
            log.Fatal("Send body failed")
            return
        }
	}
}

func main() {
    listen_addr := ":23456"
	http.Handle("/serv/record", websocket.Handler(Recorder))
	http.Handle("/serv/playback", websocket.Handler(Processor))

    log.Print("Listen on TCP ", listen_addr)
	err := http.ListenAndServe(listen_addr, nil)
	if err != nil {
		panic("ListenAndServe: " + err.Error())
	}
}
