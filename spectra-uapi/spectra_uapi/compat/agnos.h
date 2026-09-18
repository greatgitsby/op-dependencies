#pragma once

// The original AGNOS UAPI uses stdint names and retains a sparse annotation.
// Supply userspace definitions without changing the pinned source headers.
#include <stdint.h>
#include <time.h>
#ifndef __user
#define __user
#endif
