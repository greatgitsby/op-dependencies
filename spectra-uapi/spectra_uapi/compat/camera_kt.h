#pragma once

#include <time.h>
#include <linux/stddef.h>

// camera_kt v1.0.3 also builds with pre-5.16 Linux userspace headers.
// Match linux/stddef.h; the empty member is required for C flexible arrays.
#ifndef __DECLARE_FLEX_ARRAY
#define __DECLARE_FLEX_ARRAY(TYPE, NAME) \
  struct { \
    struct { } __empty_ ## NAME; \
    TYPE NAME[]; \
  }
#endif
