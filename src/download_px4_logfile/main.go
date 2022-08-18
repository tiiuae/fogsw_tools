package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"runtime/debug"
	"strings"
	"time"

	"github.com/tiiuae/fogsw_tools/src/download_px4_logfile/mavctrl"
)

var (
	ctrl                mavctrl.MavlinkControl
	argsAddressPtr      = flag.String("address", "udp::14540", "Mavlink address. E.g udp:192.168.200.101:14541, tcp:127.0.0.1:5760")
	argsFlightLogDirPtr = flag.String("dir", ".", "Local path where flight log files to be stored")
	argsGetLatestPtr    = flag.Bool("latest", false, "Get latest log without prompting")
	argsVersionPtr      = flag.Bool("version", false, "Version info")
)

/*********************************************
 * Helper functions
 */

func getVersion() string {
	version := ""
	info, _ := debug.ReadBuildInfo()

	for _, e := range info.Settings {
		switch e.Key {
		case "vcs.revision":
			version = version + e.Value[:7]
		case "vcs.time":
			version = "git" + strings.Replace(e.Value[:10], "-", "", -1) + "." + version
		}
	}
	if version == "" {
		version = "[unknown]"
	}

	return version
}

func SplitFileName(name string) (base string, ext string) {
	dotpos := strings.LastIndex(name, ".")
	if (dotpos == -1) || ((dotpos + 1) >= len(name)) {
		log.Println("[Main] ERROR no file ext in log file name: ", name)
		base = name
		ext = ""
	} else {
		base = name[0:dotpos]
		ext = name[dotpos+1:]
	}
	return
}

func IsValidDate(dateStr string) bool {
	now := time.Now()
	dt, ok := time.Parse("2006-01-02", dateStr)
	if ok == nil {
		if dt.Before(now) {
			return true
		}
	}
	log.Println("[IsValidDate] INVALID DATE")
	return false
}

/*********************************************
 * LogFileItem
 */

type LogFileItem struct {
	Id       int
	Dir      string
	Crypted  bool
	DataFile mavctrl.Diritem
	KeyFile  mavctrl.Diritem
}

func (l *LogFileItem) FindCryptedFileExist(name_no_ext string) bool {
	if l.Crypted {
		if l.DataFile.Name == name_no_ext+"ulgc" {
			return true
		}
		if l.KeyFile.Name == name_no_ext+"ulgk" {
			return true
		}
	}
	return false
}

/*********************************************
 * LogItemStore
 */

type LogItemStore struct {
	Items []LogFileItem
}

func (s *LogItemStore) ItemExists(dir string, name_no_ext string) (*LogFileItem, bool) {
	for i := 0; i < len(s.Items); i++ {
		if dir == s.Items[i].Dir {
			if s.Items[i].Crypted {
				if s.Items[i].DataFile.Name == name_no_ext+".ulgc" {
					return &s.Items[i], true
				}
				if s.Items[i].KeyFile.Name == name_no_ext+".ulgk" {
					return &s.Items[i], true
				}
			}
		}
	}
	return nil, false
}

func (s *LogItemStore) Add(dir string, file mavctrl.Diritem) {
	base, ext := SplitFileName(file.Name)
	//log.Println("[LogItemStore] Add: " + base + " " + ext)
	switch ext {
	case "ulg":
		// Non-encrypted log file
		var item LogFileItem
		item.Id = len(s.Items)
		item.Dir = dir
		item.Crypted = false
		item.DataFile = file
		s.Items = append(s.Items, item)
	case "ulgc":
		// Enqrypted log data file
		item_p, found := s.ItemExists(dir, base)
		if found {
			item_p.DataFile = file
		} else {
			var item LogFileItem
			item.Id = len(s.Items)
			item.Dir = dir
			item.Crypted = true
			item.DataFile = file
			s.Items = append(s.Items, item)
		}
	case "ulgk":
		// Enqrypted log key file
		item_p, found := s.ItemExists(dir, base)
		if found {
			item_p.KeyFile = file
		} else {
			var item LogFileItem
			item.Id = len(s.Items)
			item.Dir = dir
			item.Crypted = true
			item.KeyFile = file
			s.Items = append(s.Items, item)
		}
	}
}

func (s *LogItemStore) GetLatestId() (int, bool) {
	var latest_time time.Time
	var latest_id int = -1
	found := false

	for i := 0; i < len(s.Items); i++ {
		base, _ := SplitFileName(s.Items[i].DataFile.Name)
		tm, err := time.Parse("2006-01-02 15_04_05", s.Items[i].Dir+" "+base)
		if err == nil {
			if latest_id < 0 || latest_time.Before(tm) {
				latest_time = tm
				latest_id = i
				found = true
			}
		}
	}

	return latest_id, found
}

func (s *LogItemStore) FetchLog(sel int) {
	if sel >= 0 && sel < len(s.Items) {
		dir := s.Items[sel].Dir
		name := s.Items[sel].DataFile.Name
		size := s.Items[sel].DataFile.Size
		base, ext := SplitFileName(name)
		outpath_no_ext := *argsFlightLogDirPtr + "/log-" + dir + "T" + strings.Replace(base, "_", "-", 0) + "Z."
		log.Printf("[FetchLog] : %s/%s (%d bytes)\n", dir, name, size)
		ctrl.DownloadLogFile(dir, name, outpath_no_ext+ext, size)
		if s.Items[sel].Crypted {
			size = s.Items[sel].KeyFile.Size
			name := s.Items[sel].KeyFile.Name
			_, ext = SplitFileName(name)
			log.Printf("[FetchLog] : %s/%s (%d bytes)\n", dir, name, size)
			ctrl.DownloadLogFile(dir, name, outpath_no_ext+ext, size)
		}
	}
}

/*********************************************
 * Main
 */

func logic() bool {
	var success bool = true
	flag.Parse()
	if *argsVersionPtr {
		fmt.Println("version:", getVersion())
		return success
	}

	log.Println("Flight-log-downloader, version:", getVersion())
	if *argsFlightLogDirPtr == "." {
		path, err := os.Getwd()
		if err == nil {
			*argsFlightLogDirPtr = path
		}
	}
	log.Println("Flight log dir: ", *argsFlightLogDirPtr)

	// Initialize
	if !ctrl.Init(*argsAddressPtr) {
		log.Fatalf("Can't connect to Flight Controller via Mavlink ('%s')\n", *argsAddressPtr)
	}
	defer ctrl.Close()

	if !ctrl.CheckLogDirExists() {
		return false
	}

	var log_items LogItemStore

	log_dir := "/fs/microsd/log"
	log_dir_list, ok := ctrl.ListDirectory("/fs/microsd/log")
	if ok {
		for d := int(0); d < len(log_dir_list); d++ {
			dirname := log_dir_list[d].Name
			if IsValidDate(dirname) {
				file_list, _ := ctrl.ListDirectory(log_dir + "/" + dirname)
				for f := int(0); f < len(file_list); f++ {
					if file_list[f].Type == "F" {
						log_items.Add(dirname, file_list[f])
					}
				}
			}
		}
	}

	var sel int = -1

	if *argsGetLatestPtr {
		// Get latest one
		id, ok := log_items.GetLatestId()
		if ok {
			sel = id
		}
		log.Println("Get Latest:", sel)

	} else {
		// Interactive selection menu
		log.Printf("\n\nLOG FILES:\n==========\n")
		for i := int(0); i < len(log_items.Items); i++ {
			filename, _ := SplitFileName(log_items.Items[i].DataFile.Name)
			crypted := ""
			if log_items.Items[i].Crypted {
				crypted = " (encrypted)"
			}
			fmt.Printf("%3d: %s/%s %15d %s\n", log_items.Items[i].Id, log_items.Items[i].Dir, filename, log_items.Items[i].DataFile.Size, crypted)
		}
		fmt.Printf("(Enter -> Exit)\n\n")

		fmt.Printf("Select: ")
		fmt.Scanf("%d", &sel)
		log.Printf("Selection: %d", sel)
	}

	log_items.FetchLog(sel)

	return true
}

func main() {
	if !logic() {
		os.Exit(1)
	}
}
