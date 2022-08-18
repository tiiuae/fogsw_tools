package mavctrl

import (
	"fmt"
	"log"
	"os"
	"strconv"
	"time"

	"github.com/aler9/gomavlib"
	"github.com/aler9/gomavlib/pkg/dialects/common"
)

const (
	ftpReadBufferSize int           = 131072
	ftpAckMinWait_ms  int64         = 2000
	ftpAckTimeout_ms  int64         = 8000
	ftpResendWait_ms  time.Duration = 300
	ftpTryCount       int           = 5
	ftpMsgLen         uint8         = 251
)

const (
	ftpOpcodeNone             uint8 = 0
	ftpOpcodeTerminateSession uint8 = 1
	ftpOpcodeResetSession     uint8 = 2
	ftpOpcodeListDirectory    uint8 = 3
	ftpOpcodeOpenFileRO       uint8 = 4
	ftpOpcodeReadFile         uint8 = 5
	ftpOpcodeCreateFile       uint8 = 6
	ftpOpcodeWriteFile        uint8 = 7
	ftpOpcodeRemoveFile       uint8 = 8
	ftpOpcodeCreateDirectory  uint8 = 9
	ftpOpcodeRemoveDirectory  uint8 = 10
	ftpOpcodeOpenFileWO       uint8 = 11
	ftpOpcodeTruncateFile     uint8 = 12
	ftpOpcodeRename           uint8 = 13
	ftpOpcodeCalcFileCRC32    uint8 = 14
	ftpOpcodeBurstReadFile    uint8 = 15

	ftpOpcodeAck uint8 = 128
	ftpOpcodeNak uint8 = 129
)

const (
	ftpHdrPosSeqNumber     uint8 = 0
	ftpHdrPosSession       uint8 = 2
	ftpHdrPosOpcode        uint8 = 3
	ftpHdrPosSize          uint8 = 4
	ftpHdrPosReqOpcode     uint8 = 5
	ftpHdrPosBurstComplete uint8 = 6
	ftpHdrPosPadding       uint8 = 7
	ftpHdrPosOffset        uint8 = 8
	ftpHdrPosData          uint8 = 12
)

const (
	ftpNakNone           uint8 = 0
	ftpNakFail           uint8 = 1
	ftpNakFailErrno      uint8 = 2
	ftpNakInvDataSize    uint8 = 3
	ftpNakInvSession     uint8 = 4
	ftpNakNoSessionAvail uint8 = 5
	ftpNakEOF            uint8 = 6
	ftpNakUnknownCmd     uint8 = 7
	ftpNakFileExists     uint8 = 8
	ftpNakFileProtected  uint8 = 9
	ftpNakFileNotFound   uint8 = 10
)

const ftpMaxPayloadLen uint32 = uint32(ftpMsgLen - ftpHdrPosData)

type ftpheader struct {
	opcode uint8
	size   uint8
	offset uint32
}

type session struct {
	id     uint8
	active bool
}

type Diritem struct {
	Type string
	Name string
	Size int
}

var (
	ftp_session = session{0, false}
	ftp_seq     = uint16(0)
)

/**********************************************************
 * Mavlink Control API functions
 */

func (ctrl *MavlinkControl) CheckSdCardExists() bool {
	return ctrl.ftpCheckExists("/fs", "D", "microsd")
}

func (ctrl *MavlinkControl) CheckLogDirExists() bool {
	if !ctrl.ftpCheckExists("/fs", "D", "microsd") {
		log.Println("[ftp] No SDCARD found")
		return false
	}
	if !ctrl.ftpCheckExists("/fs/microsd", "D", "log") {
		log.Println("[ftp] No log dir found")
		return false
	}
	return true
}

func (ctrl *MavlinkControl) ListDirectory(dir string) (list []Diritem, list_ok bool) {
	list_ok = true
	msg, ok := ctrl.ftpSendMsg(
		ftpheader{
			opcode: ftpOpcodeListDirectory,
			size:   uint8(len(dir) + 1),
			offset: 0,
		}, []uint8(dir), false)

	if ok {
		data, size := ctrl.ftpGetData(msg)
		parse_state := 0 // Wait for type

		var item Diritem
		var item_data_buf string = ""
		for i := uint8(0); i < size; i++ {
			switch parse_state {
			case 0: // GET TYPE
				if data[i] == 0x00 {
					// null char -> start over
					continue
				} else {
					// item type received --> read item name
					item.Type = string(data[i])
					parse_state = 1
				}
			case 1: // PARSE NAME
				if data[i] == 0x00 || data[i] == 0x09 {
					// Termination char -> add name
					item.Name = item_data_buf
					item_data_buf = ""
				}

				switch data[i] {
				case 0x00:
					// Item ready, add to list
					list = append(list, item)
					// null char -> start over
					parse_state = 0
				case 0x09:
					// TAB char -> name ends, get file size
					parse_state = 2
				default:
					// fill the name buffer
					item_data_buf += string(data[i])
				}
			case 2: // GET FILE SIZE
				if data[i] == 0x00 {
					// Termination char -> add size
					i, err := strconv.Atoi(item_data_buf)
					if err != nil {
						item.Size = 0
						log.Printf("[ftp] ERROR to read list file size: %s\n", err.Error())
					} else {
						item.Size = i
					}
					item_data_buf = ""
					// Item ready, add to list
					list = append(list, item)
					parse_state = 0
				} else {
					// fill the size buffer
					item_data_buf += string(data[i])
				}
			}
		}
	}
	return
}

func (ctrl *MavlinkControl) DownloadLogFile(src_dir string, src_file string, dst_path string, fsize int) bool {
	// Download file
	var src_file_path string = "/fs/microsd/log/" + src_dir + "/" + src_file
	var dst_file_path string = dst_path + "__part"

	if !ctrl.ftpOpenFileRO(src_file_path) {
		log.Printf("[ftp] Open file '%s' failed!\n", src_file_path)
		return false
	}
	log.Printf("[ftp] Reading...")

	var offset uint32 = 0
	//var readsize uint32 = ftpReadBufferSize
	buf := []uint8{}
	file, err := os.Create(dst_file_path)
	defer file.Close()
	if err != nil {
		log.Println("[ftp] ERROR to create file: ", err.Error())
		return false
	}

	for {
		slice, size := ctrl.ftpReadFile(offset)
		if size == 0 {
			break
		}
		offset += uint32(size)
		/*		err := ioutil.WriteFile(dst_file_path, slice, 0644)
				if err != nil {
					log.Printf("[ftp] File '%s' write failed: %d", dst_file_path, err)
					return false
				}
		*/
		buf = append(buf, slice...)
		if len(buf) > ftpReadBufferSize {
			log.Printf("[ftp] Progress %d%%", (offset*100)/uint32(fsize))
			_, err := file.Write(buf)
			//err := ioutil.WriteFile(dst_file_path, buf, 0644)
			if err != nil {
				log.Printf("[ftp] File '%s' write failed: %d", dst_file_path, err)
				return false
			}
			buf = []uint8{}
		}
	}
	log.Printf("[ftp] Progress 100%%\n")
	log.Printf("[ftp] Reading done (%d bytes)\n", offset)
	ctrl.ftpTerminateSession()

	if len(buf) > 0 {
		_, err := file.Write(buf)
		if err != nil {
			log.Printf("[ftp] File '%s' write failed: %d", dst_file_path, err)
			return false
		}
	}
	file.Close()

	os.Rename(dst_file_path, dst_path)

	return true
}

/**********************************************************
 * Mavlink File Transfer Protocol functions
 */

func (ctrl *MavlinkControl) ftpCreateDir(path string) bool {
	_, ok := ctrl.ftpSendMsg(
		ftpheader{
			opcode: ftpOpcodeCreateDirectory,
			size:   0,
			offset: 0,
		}, []uint8(path), false)
	return ok
}

func (ctrl *MavlinkControl) ftpTerminateSession() bool {
	_, ok := ctrl.ftpSendMsg(
		ftpheader{
			opcode: ftpOpcodeTerminateSession,
			size:   0,
			offset: 0,
		}, []uint8{}, false)
	if ok {
		ftp_session = session{0, false}
	}
	return ok
}

func (ctrl *MavlinkControl) ftpResetSession() bool {
	_, ok := ctrl.ftpSendMsg(
		ftpheader{
			opcode: ftpOpcodeResetSession,
			size:   0,
			offset: 0,
		}, []uint8{}, false)
	if ok {
		ftp_session = session{0, false}
	}
	return ok
}

func (ctrl *MavlinkControl) ftpRemoveFile(path string) bool {
	_, ok := ctrl.ftpSendMsg(
		ftpheader{
			opcode: ftpOpcodeRemoveFile,
			size:   uint8(len(path) + 1),
			offset: 0,
		}, []uint8(path), false)
	return ok
}

func (ctrl *MavlinkControl) ftpCreateFile(path string) bool {
	if ftp_session.active {
		fmt.Println("Previous session not closed!!")
		return false
	}
	msg, ok := ctrl.ftpSendMsg(
		ftpheader{
			opcode: ftpOpcodeCreateFile,
			size:   uint8(len(path) + 1),
			offset: 0,
		}, []uint8(path), false)
	if ok {
		ftp_session = session{msg[ftpHdrPosSession], true}
	}
	return ok
}

func (ctrl *MavlinkControl) ftpOpenFileRO(path string) bool {
	if ftp_session.active {
		fmt.Println("Previous session not closed!!")
		return false
	}
	msg, ok := ctrl.ftpSendMsg(
		ftpheader{
			opcode: ftpOpcodeOpenFileRO,
			size:   uint8(len(path) + 1),
			offset: 0,
		}, []uint8(path), false)
	if ok {
		ftp_session = session{msg[ftpHdrPosSession], true}
	}
	return ok
}

func (ctrl *MavlinkControl) ftpOpenFileWO(path string) bool {
	if ftp_session.active {
		fmt.Println("Previous session not closed!!")
		return false
	}
	msg, ok := ctrl.ftpSendMsg(
		ftpheader{
			opcode: ftpOpcodeOpenFileWO,
			size:   uint8(len(path) + 1),
			offset: 0,
		}, []uint8(path), false)
	if ok {
		ftp_session = session{msg[ftpHdrPosSession], true}
	}
	return ok
}

func (ctrl *MavlinkControl) ftpWriteFile(buf []uint8, offset uint32) uint32 {
	if !ftp_session.active {
		fmt.Println("No session started!!")
		return 0
	}

	size := uint32(len(buf)) - offset
	if size > ftpMaxPayloadLen {
		size = ftpMaxPayloadLen
	}

	if size > 0 {
		_, ok := ctrl.ftpSendMsg(
			ftpheader{
				opcode: ftpOpcodeWriteFile,
				size:   uint8(size),
				offset: offset,
			}, buf[offset:offset+size], false)

		if ok {
			return size
		}
	}
	return 0
}

func (ctrl *MavlinkControl) ftpReadFile(offset uint32) ([]uint8, uint8) {
	if !ftp_session.active {
		fmt.Println("No session started!!")
		return []byte{0}, 0
	}

	msg, ok := ctrl.ftpSendMsg(
		ftpheader{
			opcode: ftpOpcodeReadFile,
			size:   uint8(ftpMaxPayloadLen),
			offset: offset,
		}, []uint8{}, true)

	if ok {
		if msg[ftpHdrPosOpcode] == ftpOpcodeAck {
			return ctrl.ftpGetData(msg)
		} else {
			// Nak handling
			err := msg[ftpHdrPosData]
			switch err {
			case ftpNakEOF:
				break
			case ftpNakFailErrno:
				ext := msg[ftpHdrPosData+1]
				fmt.Printf("ReadFile: target filesystem error %d\n", ext)
			default:
				fmt.Printf("ReadFile: error: %d\n", err)
			}
		}
	}
	return []uint8{}, 0
}

func (ctrl *MavlinkControl) ftpCheckExists(base_dir string, item_type string, item_to_find string) bool {
	msg, ok := ctrl.ftpSendMsg(
		ftpheader{
			opcode: ftpOpcodeListDirectory,
			size:   uint8(len(base_dir) + 1),
			offset: 0,
		}, []uint8(base_dir), false)

	found := false
	if ok {
		data, size := ctrl.ftpGetData(msg)
		parse_state := 0 // Wait for type

		var item_name_buf string = ""
		for i := uint8(0); i < size; i++ {
			c := string(data[i])
			switch parse_state {
			case 0: // GET TYPE
				if data[i] == 0x00 {
					// null char -> start over
					continue
				} else {
					// item type received --> read item name
					if c == item_type {
						// Desired type found, clean item name buffer
						//fmt.Println("   type found:", c)
						item_name_buf = ""
						parse_state = 1
					} else {
						// Wrong type, skip item
						parse_state = 2
					}
				}
			case 1: // PARSE NAME
				if data[i] == 0x00 || data[i] == 0x09 {
					// Termination char -> check name
					if item_name_buf != "" && item_to_find == item_name_buf {
						found = true
						break
					}
				}

				switch data[i] {
				case 0x00:
					// null char -> start over
					parse_state = 0
				case 0x09:
					// TAB char -> name ends, skip the rest (file size)
					parse_state = 2
				default:
					// fill the name buffer
					item_name_buf += c
				}
			case 2: // SKIP ITEM
				if data[i] == 0x00 {
					parse_state = 0
				}
			}
		}
		// EOF, check name
		if item_name_buf != "" && item_to_find == item_name_buf {
			found = true
		}
	}

	return found
}

/*********************************************
 * Send, Receive & GetData helper functions
 */

func (ctrl *MavlinkControl) ftpSendMsg(header ftpheader, data []uint8, retNak bool) ([ftpMsgLen]uint8, bool) {
	ftp_seq++

	payload := [ftpMsgLen]uint8{
		uint8(ftp_seq & 0xff),               // sequence number LSB
		uint8((ftp_seq >> 8) & 0xff),        // sequence number MSB
		ftp_session.id,                      // Session: 0
		header.opcode,                       // Opcode:
		header.size,                         // Size:
		0,                                   // Req Opcode: 0
		0,                                   // Burst Complete: 0
		0,                                   // Padding: 0
		uint8(header.offset & 0xff),         // offset LSB
		uint8((header.offset >> 8) & 0xff),  // offset 2nd
		uint8((header.offset >> 16) & 0xff), // offset 3rd
		uint8((header.offset >> 24) & 0xff), // offset MSB
	}
	if len(data) > 0 {
		copy(payload[12:], data[:])
	}

	msg := common.MessageFileTransferProtocol{
		TargetNetwork:   0,
		TargetSystem:    1,
		TargetComponent: 1,
		Payload:         payload,
	}

	var ok bool = false
	var resp_msg [ftpMsgLen]uint8
	for i := 0; i < ftpTryCount; i++ {
		ctrl.node.WriteMessageAll(&msg)
		resp_msg, ok = ctrl.waitForFTPAck(ftpAckMinWait_ms, header.opcode)
		if ok {
			if retNak || resp_msg[ftpHdrPosOpcode] == ftpOpcodeAck {
				break
			} else {
				fmt.Printf("   Nak: %d, opc: %d, err: %d\n", resp_msg[ftpHdrPosOpcode], resp_msg[ftpHdrPosReqOpcode], resp_msg[ftpHdrPosData])
			}
		}
		time.Sleep(ftpResendWait_ms * time.Millisecond)
	}
	return resp_msg, ok
}

func (ctrl *MavlinkControl) waitForFTPAck(timeout_ms int64, opcode uint8) ([ftpMsgLen]uint8, bool) {
	stamp_ms := time.Now().UnixMilli()

	for evt := range ctrl.node.Events() {
		if frm, ok := evt.(*gomavlib.EventFrame); ok {
			if msg, ok := frm.Message().(*common.MessageFileTransferProtocol); ok {
				if msg.Payload[ftpHdrPosReqOpcode] == opcode {
					return msg.Payload, true
				}
			}
		}
		if (time.Now().UnixMilli() - stamp_ms) > timeout_ms {
			break
		}
	}
	return [ftpMsgLen]uint8{0}, false
}

func (ctrl *MavlinkControl) ftpGetData(msg [ftpMsgLen]uint8) ([]uint8, uint8) {
	size := msg[ftpHdrPosSize]
	if size > 0 {
		return msg[ftpHdrPosData:(size + ftpHdrPosData)], size
	}
	return []uint8{}, 0
}
