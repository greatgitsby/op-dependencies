#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <linux/ioctl.h>
#include <linux/media.h>
#include <linux/types.h>
#include <linux/videodev2.h>

// System headers are global; incompatible camera types have internal linkage.
namespace {
#include <media/cam_defs.h>
#include <media/cam_icp.h>
#include <media/cam_isp.h>
#include <media/cam_req_mgr.h>
#include <media/cam_sensor.h>
#include <media/cam_sync.h>

// Literal expectations audited against the two pinned driver definitions.
// Do not derive expected values from the headers being tested.
#define SIZE(type, value) static_assert(sizeof(struct type) == value, #type)
#define OFFSET(type, field, value) static_assert(offsetof(struct type, field) == value, #type "." #field)

static_assert(sizeof(void *) == 8, "Supported camera targets use LP64");
static_assert(VIDIOC_CAM_CONTROL == 0xc01856c0, "camera ioctl");
static_assert(CAM_QUERY_CAP == 0x101 && CAM_CONFIG_DEV == 0x105 && CAM_FLUSH_REQ == 0x108);
SIZE(cam_control, 24);
OFFSET(cam_control, handle, 16);
SIZE(cam_packet_header, 24);
SIZE(cam_packet, 64);
OFFSET(cam_packet, payload, 56);
SIZE(cam_buf_io_cfg, 256);
SIZE(cam_cmd_buf_desc, 24);
SIZE(cam_cmd_probe, 20);
SIZE(cam_power_settings, 12);
SIZE(i2c_rdwr_header, 8);
SIZE(cam_csiphy_info, 24);
OFFSET(cam_csiphy_info, data_rate, 16);
SIZE(cam_req_mgr_session_info, 8);
SIZE(cam_req_mgr_link_info, 268);
SIZE(cam_req_mgr_flush_info, 24);
SIZE(cam_mem_mgr_alloc_cmd, 104);
SIZE(cam_mem_mgr_map_cmd, 96);
SIZE(cam_icp_query_cap_cmd, 176);
SIZE(cam_icp_acquire_dev_info, 60);
OFFSET(cam_icp_acquire_dev_info, out_res, 44);
OFFSET(cam_req_mgr_message, u, 8);
OFFSET(cam_req_mgr_frame_msg, request_id, 0);
OFFSET(cam_req_mgr_frame_msg, timestamp, 16);

#if MODERN
#ifndef CAM_QUERY_CAP_V2
#error camera_kt headers required
#endif
static_assert(CAM_COMMON_OPCODE_MAX == 0x10a && CAM_SENSOR_PROBE_CMD == 0x10b);
static_assert(CAM_REQ_MGR_LINK == 0x10e && CAM_REQ_MGR_SCHED_REQ == 0x110);
static_assert(CAM_REQ_MGR_ALLOC_BUF == 0x113 && CAM_REQ_MGR_MAP_BUF == 0x114);
SIZE(cam_cmd_i2c_info, 8);
OFFSET(cam_cmd_i2c_info, cmd_type, 5);
SIZE(cam_cmd_power, 20);
OFFSET(cam_cmd_power, power_settings, 8);
SIZE(cam_cmd_unconditional_wait, 8);
SIZE(cam_sensor_query_cap, 44);
SIZE(cam_req_mgr_sched_request, 32);
OFFSET(cam_req_mgr_sched_request, req_id, 24);
SIZE(cam_req_mgr_frame_msg, 40);
SIZE(cam_req_mgr_message, 56);
SIZE(cam_isp_query_cap_cmd, 216);
SIZE(cam_isp_in_port_info, 128);
OFFSET(cam_isp_in_port_info, data, 96);
OFFSET(cam_csiphy_info, mipi_flags, 4);
#define CHECK_ABI check_camera_kt
#else
#ifdef CAM_QUERY_CAP_V2
#error AGNOS headers required
#endif
static_assert(CAM_COMMON_OPCODE_MAX == 0x109 && CAM_SENSOR_PROBE_CMD == 0x10a);
static_assert(CAM_REQ_MGR_LINK == 0x10d && CAM_REQ_MGR_SCHED_REQ == 0x10f);
static_assert(CAM_REQ_MGR_ALLOC_BUF == 0x112 && CAM_REQ_MGR_MAP_BUF == 0x113);
SIZE(cam_cmd_i2c_info, 4);
OFFSET(cam_cmd_i2c_info, cmd_type, 3);
SIZE(cam_cmd_power, 16);
OFFSET(cam_cmd_power, power_settings, 4);
SIZE(cam_cmd_unconditional_wait, 4);
SIZE(cam_sensor_query_cap, 40);
SIZE(cam_req_mgr_sched_request, 24);
OFFSET(cam_req_mgr_sched_request, req_id, 16);
SIZE(cam_req_mgr_frame_msg, 32);
SIZE(cam_req_mgr_message, 40);
SIZE(cam_isp_query_cap_cmd, 144);
SIZE(cam_isp_in_port_info, 132);
OFFSET(cam_isp_in_port_info, data, 100);
OFFSET(cam_csiphy_info, lane_mask, 0);
OFFSET(cam_csiphy_info, csiphy_3phase, 4);
#define CHECK_ABI check_agnos
#endif
}  // namespace

// Only an ABI-neutral C symbol crosses translation-unit boundaries.
extern "C" int CHECK_ABI() {
  cam_cmd_i2c_info command = {};
  command.slave_addr = 0x1234;
  command.i2c_freq_mode = 1;
  command.cmd_type = 4;
#if MODERN
  const unsigned char expected[] = {0x34, 0x12, 0, 0, 1, 4, 0, 0};
#else
  const unsigned char expected[] = {0x34, 0x12, 1, 4};
#endif
  if (memcmp(&command, expected, sizeof(expected))) return 1;

  // Decode a literal little-endian frame event, independent of struct writes.
  const unsigned char event[] = {
    1, 0, 0, 0, 0, 0, 0, 0,             // session + reserved
    2, 0, 0, 0, 0, 0, 0, 0,             // request_id
    3, 0, 0, 0, 0, 0, 0, 0,             // frame_id
    0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11, // timestamp
    4, 0, 0, 0, 0, 0, 0, 0,             // link + status
#if MODERN
    5, 0, 0, 0, 0, 0, 0, 0,             // frame_id_meta + reserved
    0, 0, 0, 0, 0, 0, 0, 0,             // custom-message union tail
#endif
  };
  static_assert(sizeof(event) == sizeof(cam_req_mgr_message));
  cam_req_mgr_message message = {};
  memcpy(&message, event, sizeof(event));
  const auto &frame = message.u.frame_msg;
  if (message.session_hdl != 1 || frame.request_id != 2 || frame.frame_id != 3 ||
      frame.timestamp != UINT64_C(0x1122334455667788) || frame.link_hdl != 4 || frame.sof_status != 0) return 2;
#if MODERN
  if (frame.frame_id_meta != 5) return 3;
#endif
  return 0;
}
