package main

import (
	"bytes"
	"code.google.com/p/go.net/websocket"
	"encoding/binary"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"recorder"
	"runtime"
	"strconv"
	"strings"
	"syscall"
	"time"
	"unsafe"
)

var (
	start_time  int64
	signal_chan chan os.Signal
)

const Layout = "2006-01-02 15:04:05"

type Head struct {
	Type       int32
	TimeDelta  uint32
	BodyLength uint32
}

type FileInfo struct {
	Filename  string `json:"filename"`
	Filesize  int64  `json:"filesize"`
	Starttime string `json:"starttime"`
	Endtime   string `json:"endtime"`
	Totaltime int64  `json:"totaltime"`
}

type Filelist struct {
	Status int        `json:"status"`
	Data   []FileInfo `json:"data"`
}

func GetFileList(path, host, vm_uuid string) *Filelist {
	var file_list *Filelist = new(Filelist)
	filepath.Walk(path, func(path string, info os.FileInfo, err error) error {
		if !info.IsDir() {
			filename_splited := strings.Split(info.Name(), "_")
			xen_host := filename_splited[0]
			uuid := filename_splited[1]

			if xen_host == host && uuid == vm_uuid {
				var file_info FileInfo

				// parse filename and filesize
				file_info.Filename = info.Name()
				file_info.Filesize = info.Size()

				// parse start_time
				time_and_suffix := strings.Split(filename_splited[2], ".")
				start_time := time_and_suffix[0]

				// parse total time
				start_time_int, err := strconv.Atoi(start_time)
				if err != nil {
					log.Println("Playback Server: Parse start_time failed: ", err)
					return nil
				}
				start_time_struct := time.Unix(int64(start_time_int), 0)
				end_time_struct := info.ModTime()

				duration := end_time_struct.Sub(start_time_struct)
				file_info.Totaltime = int64(duration.Seconds())

				// parse start_time and end_time in format
				file_info.Starttime = start_time_struct.Format(Layout)
				file_info.Endtime = end_time_struct.Format(Layout)

				// append file_info to file_list
				file_list.Data = append(file_list.Data, file_info)
			}
		}
		return nil
	})
	if len(file_list.Data) == 0 {
		file_list.Status = 1
	} else {
		file_list.Status = 0
	}

	return file_list
}

func getNowMillisecond() int64 {
	var tv syscall.Timeval
	syscall.Gettimeofday(&tv)
	return (int64(tv.Sec)*1e3 + int64(tv.Usec)/1e3)
}

func ListFileHandler(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query()
	var host, vm_uuid string

	if value, ok := query["host"]; ok {
		host = value[0]
	} else {
		log.Println("Playback Server: Emptry Host name in Query")
		http.Error(w, "Emptry Host", 404)
		return
	}

	if value, ok := query["vm_uuid"]; ok {
		vm_uuid = value[0]
	} else {
		log.Println("Playback Server: Emptry VM UUID in Query")
		http.Error(w, "Emptry VM UUID", 404)
		return
	}

	filelist := GetFileList("./data", host, vm_uuid)
	json_buf, err := json.Marshal(filelist)
	if err != nil {
		log.Println("Playback Server: Marshal json failed: ", err)
		http.Error(w, "Parse JSON Failed", 500)
	}

	if filelist.Status == 1 {
		log.Println("Playback Server: Got empty Filelist")
		http.Error(w, "Empty Filelist", 404)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.Write(json_buf)
}

func Processor(ws *websocket.Conn) {
	var filename string
	ws_query := ws.Request().URL.Query()
	if value, ok := ws_query["filename"]; ok {
		filename = value[0]
	} else {
		log.Println("Playback Server: Emptry filename in Query")
		return
	}

	defer ws.Close()
	var head Head
	const headSize = unsafe.Sizeof(head)

	start_time = getNowMillisecond()
	ws.PayloadType = 2

	file, err := os.Open("./data/" + filename)
	if err != nil {
		log.Println("Playback Server: Failed to open VNC Data file: ", err)
		return
	}
	defer file.Close()

	for {
		size := int64(headSize)
		buf := make([]byte, size)

		n, err := file.Read(buf)
		if err == io.EOF {
			log.Print("Playback Server: got EOF in Read head")
			return
		}
		if err != nil {
			log.Print("Playback Server: Failed to Read Head", err)
			return
		}
		if n != int(size) {
			log.Print("Playback Server: invlid head size.")
			return
		}

		err = binary.Read(bytes.NewBuffer(buf), binary.LittleEndian, &head)
		if err != nil {
			log.Print("Playback Server: Failed to Parse Head: ", err)
			return
		}

		buf = make([]byte, head.BodyLength)
		n, err = file.Read(buf)
		if err == io.EOF {
			log.Print("Playback Server: got EOF in Read body")
			return
		}
		if err != nil {
			log.Print("Playback Server: Failed to Read Boby: ", err)
			return
		}
		if n != int(head.BodyLength) {
			log.Print("Playback Server: invlid body size.")
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
			log.Print("Playback Server: Websocket Got Broken PIPE")
			return
		} else if err != nil {
			log.Print("Playback Server: Websocket Write Failed")
			log.Print(err)
			return
		}
		if n != int(head.BodyLength) {
			log.Print("Playback Server: Send body failed")
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

func addDefaultHeaders(fn http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Server", "RPServer 0.1")
		fn(w, r)
	}
}

func main() {
	runtime.GOMAXPROCS(runtime.NumCPU())

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
	go recorder.StartRecorder()

	listen_addr := "0.0.0.0:23456"

	http.Handle("/serv/playback", websocket.Handler(Processor))
	http.HandleFunc("/serv/listfile", addDefaultHeaders(ListFileHandler))

	log.Print("Playback Server: Listen on WebSocket ", listen_addr)
	err := http.ListenAndServe(listen_addr, nil)
	if err != nil {
		panic("Playback Server: ListenAndServe: " + err.Error())
	}
}
