package main

import (
	"bytes"
	"code.google.com/p/go.net/websocket"
	"encoding/binary"
	"encoding/json"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path"
	"path/filepath"
	"recorder"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"
	"unsafe"
)

var (
	start_time  int64
	signal_chan chan os.Signal
	mutex       sync.Mutex
	cond        sync.Cond
	config      GlobalConfig
	logfile     *os.File
)

const Layout = "2006-01-02 15:04:05"
const ConfigFile = "./config.json"

type GlobalConfig struct {
	PlaybackListen string `json:"playback_server_listen"`
	RecordListen   string `json:"record_server_listen"`
	LogFile        string `json:"log_file"`
	DataDir        string `json:"data_dir"`
}

type Head struct {
	Type       int32
	TimeDelta  uint32
	BodyLength uint32
}

type FileInfo struct {
	Id            int64  `json:"id"`
	Filename      string `json:"filename"`
	Filesize      int64  `json:"filesize"`
	Starttime     string `json:"starttime"`
	Endtime       string `json:"endtime"`
	Duration      int64  `json:"duration"`
	ClientAddress string `json:"client"`
}

type Filelist struct {
	Status int        `json:"status"`
	Data   []FileInfo `json:"data"`
}

func init() {
	// parse  JSON config file
	data, err := ioutil.ReadFile(ConfigFile)
	if err != nil {
		log.Fatal(err)
		return
	}
	err = json.Unmarshal(data, &config)
	if err != nil {
		log.Fatal(err)
	}

	// init log
	logfile, err = os.OpenFile(config.LogFile, os.O_RDWR|os.O_CREATE|os.O_APPEND, 0666)
	if err != nil {
		log.Fatal("Error opening file: %v", err)
	}
	log.SetOutput(logfile)
	log.Println("Server Start")
}

func GetFileList(path, host, vm_uuid string) *Filelist {
	var file_list *Filelist = new(Filelist)
	var Id int64 = 0
	filepath.Walk(path, func(path string, info os.FileInfo, err error) error {
		if !info.IsDir() {
			filename_splited := strings.Split(info.Name(), "_")
			xen_host := filename_splited[0]
			uuid := filename_splited[1]
			start_time := filename_splited[2]
			client_address := filename_splited[3]

			if xen_host == host && uuid == vm_uuid {
				var file_info FileInfo

				// 获得文件名和大小
				file_info.Filename = info.Name()
				file_info.Filesize = info.Size()

				// 获得WebSocket客户端地址
				file_info.ClientAddress = client_address

				// 解析总时长
				start_time_int, err := strconv.Atoi(start_time)
				if err != nil {
					log.Println("Playback Server: Parse start_time failed: ", err)
					return nil
				}
				start_time_struct := time.Unix(int64(start_time_int), 0)
				end_time_struct := info.ModTime()

				duration := end_time_struct.Sub(start_time_struct)
				file_info.Duration = int64(duration.Seconds())

				// 转换时间戳到字符串
				file_info.Starttime = start_time_struct.Format(Layout)
				file_info.Endtime = end_time_struct.Format(Layout)

				file_info.Id = Id
				Id += 1

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

func Exist(filename string) bool {
	_, err := os.Stat(filename)
	return err == nil || os.IsExist(err)
}

// 得到毫秒级的时间戳
func getNowMillisecond() int64 {
	var tv syscall.Timeval
	syscall.Gettimeofday(&tv)
	return (int64(tv.Sec)*1e3 + int64(tv.Usec)/1e3)
}

// 删除虚拟机VNC记录文件
func DeleteFileHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "X-Requested-With")
	w.Header().Set("Access-Control-Max-Age", "86400")

	query := r.URL.Query()
	var filename string

	if value, ok := query["filename"]; ok {
		filename = value[0]
	} else {
		log.Println("Playback Server: Emptry Filename in Query")
		http.Error(w, "Emptry Filename", 404)
		return
	}

	var file_exist bool = true

	// 判断文件路径是否正确
	pwd, _ := os.Getwd()
	fullpath := path.Join(pwd, "data", filename)
	fullpath = path.Clean(fullpath)
	fullpath_dir := path.Dir(fullpath)
	correct_dir := path.Join(pwd, "data")
	if fullpath_dir != correct_dir {
		log.Println("Playback Server: Bad File Path To Delete: ", fullpath)
		http.Error(w, "Bad File", 403)
		return
	}

	// 判断文件是否存在
	if !Exist(fullpath) {
		file_exist = false
	}

	// 删除文件
	if file_exist {
		log.Println("Playback Server: Delete file:", filename)
		err := os.Remove(fullpath)
		if err != nil {
			// 删除文件失败后，只记录日志
			log.Println("Playback Server: Delete file failed :", err)
		}
	} else {
		log.Println("Playback Server: Not Found:", fullpath)
		http.Error(w, "Not Exist", 404)
		return
	}
}

// 根据主机名和虚拟机REF ID，列出虚拟机的VNC记录文件
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

// 从WebSocket客户端接收信号
func WaitSignal(ws *websocket.Conn, notify_stop_chan chan<- bool, timer **time.Timer,
	pause *bool, resume_chan chan bool, elapsed *int64) {

	var start_time int64
	var end_time int64

	for {
		// 设置Read Deadline为24小时
		ws.SetReadDeadline(time.Now().Add(86400 * time.Second))

		buf := make([]byte, 8)
		_, err := ws.Read(buf)

		if err != nil {
			log.Println("Playback Server: Read data from client failed: ", err)
			mutex.Lock()
			(*timer).Reset(time.Duration(time.Nanosecond))
			mutex.Unlock()
			notify_stop_chan <- true
			goto end
		}

		data, _ := strconv.Atoi(string(recorder.GetValidByte(buf)))
		if data == 800 { // 关闭
			// 如果执行了暂停，首先取消暂停
			if *pause == true {
				resume_chan <- true
			}
			// 取消定时器，发送结束信号
			mutex.Lock()
			(*timer).Reset(time.Duration(time.Nanosecond))
			mutex.Unlock()
			notify_stop_chan <- true
			goto end
		} else if data == 801 { // 暂停
			if *pause == false {
				// 设置暂停标志，记录暂停开始时间
				*pause = true
				start_time = getNowMillisecond()
			}
		} else if data == 802 { // 恢复
			if *pause == true {
				// 记录暂停结束时间，向恢复的channel发送信号
				end_time = getNowMillisecond()
				*elapsed += (end_time - start_time)
				*pause = false
				resume_chan <- true
			}
		}
	}

end:
	ws.Close()
}

// 处理WebSocket客户端的VNC重新播放
func Processor(ws *websocket.Conn) {
	log.Println("Playback Server: New WebSocket Client: ", ws.Request().RemoteAddr)

	// 发送定时器
	var timer *time.Timer

	// 暂停的标志
	var pause bool = false
	// 接收恢复信号的同步channel
	resume_chan := make(chan bool)

	// 暂停时间的总和
	var elapsed int64

	// 设置WebSocket内容的编码类型为Binary
	ws.PayloadType = 2

	notify_chan := make(chan bool)
	go WaitSignal(ws, notify_chan, &timer, &pause, resume_chan, &elapsed)

	var filename string
	ws_query := ws.Request().URL.Query()
	if value, ok := ws_query["filename"]; ok {
		filename = value[0]
	} else {
		log.Println("Playback Server: Emptry filename in Query")
		return
	}

	defer ws.Close()

	// 设置开始时间
	start_time = getNowMillisecond()

	// 判断文件路径是否正确
	pwd, _ := os.Getwd()
	fullpath := path.Join(pwd, "data", filename)
	fullpath = path.Clean(fullpath)
	fullpath_dir := path.Dir(fullpath)
	correct_dir := path.Join(pwd, "data")
	if fullpath_dir != correct_dir {
		log.Println("Playback Server: Bad File Path To Open: ", fullpath)
		return
	}

	// 打开VNC记录文件
	file, err := os.Open(fullpath)
	if err != nil {
		log.Println("Playback Server: Failed to open VNC Data file: ", err)
		return
	}
	defer file.Close()

	// 循环发送VNC记录文件，直到文件结束
	for {
		select {
		// 从channel中读取信号，并退出函数
		case quit := <-notify_chan:
			if quit == true {
				log.Println("Playback Server: Receive Close Signal, Quit Goroutine Now.")
				goto end
			}
		default:
			if !pause {
				// 获取Head结构体大小
				var head Head
				const headSize = unsafe.Sizeof(head)

				size := int64(headSize)
				buf := make([]byte, size)

				n, err := file.Read(buf)
				if err == io.EOF {
					log.Print("Playback Server: got EOF in Read head")
					goto end
				}
				if err != nil {
					log.Print("Playback Server: Failed to Read Head", err)
					goto end
				}
				if n != int(size) {
					log.Print("Playback Server: invlid head size.")
					goto end
				}

				err = binary.Read(bytes.NewBuffer(buf), binary.LittleEndian, &head)
				if err != nil {
					log.Print("Playback Server: Failed to Parse Head: ", err)
					goto end
				}

				buf = make([]byte, head.BodyLength)
				n, err = file.Read(buf)
				if err == io.EOF {
					log.Print("Playback Server: got EOF in Read body")
					goto end
				}
				if err != nil {
					log.Print("Playback Server: Failed to Read Boby: ", err)
					goto end
				}
				if n != int(head.BodyLength) {
					log.Print("Playback Server: invlid body size.")
					goto end
				}

				// 忽略是WebSocket客户端发送的帧
				if head.Type == 1 {
					continue
				}

				// 将文件中记录的暂停时间
				// 加上elapsed作为补偿
				head.TimeDelta += uint32(elapsed)

				now := getNowMillisecond()
				toffset := now - start_time

				var delay uint32
				if (head.TimeDelta) < uint32(toffset) {
					delay = 1
				} else {
					delay = (head.TimeDelta) - uint32(toffset)
				}
				sleep := time.Duration(int(delay)) * time.Millisecond

				mutex.Lock()
				timer = time.NewTimer(sleep)
				mutex.Unlock()
				<-timer.C

				n, err = ws.Write(buf)
				if err == syscall.EPIPE {
					log.Print("Playback Server: Websocket Got Broken PIPE")
					goto end
				} else if err != nil {
					log.Print("Playback Server: Websocket Write Failed")
					log.Print(err)
					goto end
				}
				if n != int(head.BodyLength) {
					log.Print("Playback Server: Send body failed")
					goto end
				}
			} else {
				// 如果已经暂停
				// 则以阻塞的方式读取channel
				<-resume_chan
			}
		}
	}
end:
	log.Println("Playback Server: Close WebSocket Connection: ", ws.Request().RemoteAddr)
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
	defer logfile.Close()

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
	http.HandleFunc("/serv/deletefile", addDefaultHeaders(DeleteFileHandler))

	log.Print("Playback Server: Listen on WebSocket ", listen_addr)
	err := http.ListenAndServe(listen_addr, nil)
	if err != nil {
		panic("Playback Server: ListenAndServe: " + err.Error())
	}
}
