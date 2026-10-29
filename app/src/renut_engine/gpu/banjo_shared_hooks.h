// bangaio-nx (tools/renut_hook_remap_bangaio.py): the addresses both Renut's renderer and the port's own code hook
// (src/bangaio_frame_hooks.cpp); the port's hook calls renut_native_sub_X when Renut's renderer is chosen.
#pragma once

#include <cstdint>

#include <rex/ppc.h>

extern "C" void renut_native_sub_8216F7C8(PPCContext& ctx, uint8_t* base);
extern "C" void renut_native_sub_8216FE50(PPCContext& ctx, uint8_t* base);
