package main

import (
	"bytes"
	"code.google.com/p/go.net/websocket"
	"encoding/binary"
	"io"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
	"unsafe"
)

var (
	start_time  int64
	signal_chan chan os.Signal
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
	defer ws.Close()
	var head Head
	const headSize = unsafe.Sizeof(head)

	start_time = getNowMillisecond()
	ws.PayloadType = 2

	file, err := os.Open("record.dat.2")
	if err != nil {
		log.Print(err)
		return
	}
	defer file.Close()

	for {
		size := int64(headSize)
		buf := make([]byte, size)

		n, err := file.Read(buf)
		if err != nil {
			log.Print(err)
			return
		}
		if n != int(size) {
			log.Print("invlid head size.")
			return
		}
		if err == io.EOF {
			log.Print("got EOF in Read head")
			return
		}

		err = binary.Read(bytes.NewBuffer(buf), binary.LittleEndian, &head)
		if err != nil {
			log.Print(err)
			return
		}

		buf = make([]byte, head.BodyLength)
		n, err = file.Read(buf)
		if err != nil {
			log.Print(err)
			return
		}
		if n != int(head.BodyLength) {
			log.Print("invlid body size.")
			return
		}
		if err == io.EOF {
			log.Print("got EOF in Read body")
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
		if err == syscall.EPIPE {
			log.Print("Websocket Got Broken PIPE")
			return
		} else if err != nil {
			log.Print("Websocket Write Failed")
			log.Print(err)
			return
		}
		if n != int(head.BodyLength) {
			log.Print("Send body failed")
			return
		}
	}
}

func signalCallback() {
	for s := range signal_chan {
		sig := s.String()
		if sig == "broken pipe" {
			continue
		}
		log.Print("Got Signal: ", sig)
		log.Print("Server exit...")
		os.Exit(0)
	}
}

func main() {
	signal_chan = make(chan os.Signal, 10)
	signal.Notify(signal_chan,
		syscall.SIGHUP,
		syscall.SIGINT,
		syscall.SIGTERM,
		syscall.SIGQUIT,
		syscall.SIGPIPE,
		syscall.SIGALRM,
		syscall.SIGKILL,
		syscall.SIGPIPE)

	go signalCallback()

	listen_addr := ":23456"
	http.Handle("/serv/record", websocket.Handler(Recorder))
	http.Handle("/serv/playback", websocket.Handler(Processor))

	log.Print("Listen on TCP ", listen_addr)
	err := http.ListenAndServe(listen_addr, nil)
	if err != nil {
		panic("ListenAndServe: " + err.Error())
	}
}
