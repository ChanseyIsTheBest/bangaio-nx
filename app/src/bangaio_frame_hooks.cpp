// bangaio-nx (2026-10-29, from nights-nx's nights_frame_hooks.cpp): Bangai-O's frame hook on D3DDevice_Swap
// (sub_8216F7C8: XDK 20209, paired with Bejeweled 3's sub_822F5EB0 and Zuma's Revenge's sub_82309410,
// docs/bangaio-notes.md).
//
// - Counts game frames (g_banjo_game_frames: the captures' video and frame-rate lines read it; banjo-nx counted them in
//   its N&B-only ring renderer hooks, not built here).
// - With Renut's renderer, Renut's Swap presents (renut_native_sub_8216F7C8, BANJO_RENUT_HOOK_SHARED in
//   renut_engine/gpu/d3d/hooks/device.cpp) and the frame is paced here (from peggle2-nx's PaceRenutSwap): Renut presents
//   without the console's vertical blank and its Swap does not wait for one, and Bangai-O's game speed follows its frame
//   rate. The console's Swap waits for the flip every 'interval' vblanks of 60 Hz (the device word at +13808, the
//   presentation interval). A frame that is already late goes at once (no catching up), as a late flip does.
// Credits: peggle2-nx's frame hook (the pacing), banjo-nx's display_sync (the release on the display's refresh).

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <thread>

#include <rex/cvar.h>
#include <rex/hook.h>
#include <rex/logging.h>

#if BANJO_RENUT_RENDERER
#include "renut_engine/display_sync.h"
#include "renut_engine/gpu/banjo_renut_select.h"
#include "renut_engine/gpu/banjo_shared_hooks.h"
#endif

std::atomic<uint64_t> g_banjo_game_frames{0};

// banjo-nx's controls overlay persists rebinds through its N&B cvar menu (renut_engine/cvar_menu.cpp, N&B-only, not
// built): here the rebinds last for the session.
void RenutSaveConfig() {
  static bool logged = false;
  if (!logged) {
    logged = true;
    REXLOG_INFO("[bangaio] controls: rebinds are kept for this session only (no cvar menu in this build)");
  }
}

#if BANJO_RENUT_RENDERER
REXCVAR_DEFINE_BOOL(bangaio_renut_swap_pacing, true, "BangaiO",
                    "Renut's renderer: the Swap waits for the presentation interval the game set (60 Hz vblanks), as "
                    "the console's does; false = frames as fast as they come (timing tests only: the game speeds up)");

namespace {

// The device's presentation interval (N&B +13596, XDK 20209: +13808; tools/renut_device_offsets_bangaio.py).
constexpr uint32_t kDeviceOffsetPresentInterval = 13808;

void PaceRenutSwap(uint32_t interval) {
  using Clock = std::chrono::steady_clock;
  static Clock::time_point previous{};
  if (!REXCVAR_GET(bangaio_renut_swap_pacing) || interval == 0) return;
  const auto frame = std::chrono::nanoseconds(16'666'667LL * std::min<uint32_t>(interval, 4));
  const auto now = Clock::now();
  // With the display's refresh known (the Switch: the display's vsync event), the release is a refresh plus the
  // measured phase (banjo-nx's banjo_display_sync); otherwise the timer below.
  banjo::display_sync::Start();
  {
    static uint64_t previous_release = 0;
    const auto to_ns = [](Clock::time_point t) {
      return uint64_t(std::chrono::duration_cast<std::chrono::nanoseconds>(t.time_since_epoch()).count());
    };
    bool anchored = false;
    const uint64_t release = banjo::display_sync::NextRelease(to_ns(now), previous_release, uint64_t(frame.count()),
                                                              &anchored);
    if (release) {
      previous_release = release;
      const Clock::time_point at{std::chrono::duration_cast<Clock::duration>(std::chrono::nanoseconds(release))};
      for (;;) {
        const auto t = Clock::now();
        if (t >= at) break;
        if (at - t > std::chrono::microseconds(400))
          std::this_thread::sleep_for(at - t - std::chrono::microseconds(400));
        else
          std::this_thread::yield();
      }
      banjo::display_sync::NoteRelease(release, anchored);
      previous = std::max(at, now);
      return;
    }
    previous_release = 0;
  }
  const auto due = previous + frame;
  if (previous == Clock::time_point{} || due <= now) {
    previous = now;
    return;
  }
  // The last part is yielded away instead of slept: Windows' sleeps overshoot by up to ~1 ms; Horizon's
  // svcSleepThread is precise, so the console spins only the last 0.4 ms.
#if REX_PLATFORM_SWITCH
  constexpr auto kTail = std::chrono::microseconds(400);
#else
  constexpr auto kTail = std::chrono::microseconds(1500);
#endif
  for (;;) {
    const auto t = Clock::now();
    if (t >= due) break;
    const auto left = due - t;
    if (left > kTail)
      std::this_thread::sleep_for(left - kTail);
    else
      std::this_thread::yield();
  }
  previous = due;
}

}  // namespace
#endif

REX_EXTERN(__imp__sub_8216F7C8);
REX_HOOK_RAW(sub_8216F7C8) {  // D3DDevice_Swap
#if BANJO_RENUT_RENDERER
  if (::banjo::renut_gpu::Active()) {
    uint8_t interval_bytes[4];
    std::memcpy(interval_bytes, base + ctx.r3.u32 + kDeviceOffsetPresentInterval, 4);
    renut_native_sub_8216F7C8(ctx, base);  // Renut's Swap (presents)
    g_banjo_game_frames.fetch_add(1, std::memory_order_relaxed);
    PaceRenutSwap(interval_bytes[3]);
    return;
  }
#endif
  __imp__sub_8216F7C8(ctx, base);
  g_banjo_game_frames.fetch_add(1, std::memory_order_relaxed);
}

// bangaio-nx (2026-10-29): D3DDevice_Present (sub_8216FE50; Bejeweled 3's sub_822F6618, unique shape). Bangai-O shows
// its frames through Present, and Renut's Present swaps natively, never through the guest Swap above: the first Renut
// runs counted no frames and paced none (renut3: 6,553 game frames in 10 s on the PC, the game running ten times too
// fast). So Present is hooked here too, as Swap is: Renut's Present, the frame count, the game's presentation interval.
REX_EXTERN(__imp__sub_8216FE50);
REX_HOOK_RAW(sub_8216FE50) {  // D3DDevice_Present
#if BANJO_RENUT_RENDERER
  if (::banjo::renut_gpu::Active()) {
    uint8_t interval_bytes[4];
    std::memcpy(interval_bytes, base + ctx.r3.u32 + kDeviceOffsetPresentInterval, 4);
    renut_native_sub_8216FE50(ctx, base);  // Renut's Present (resolves into the front buffer and swaps)
    g_banjo_game_frames.fetch_add(1, std::memory_order_relaxed);
    static bool logged = false;
    if (!logged) {
      logged = true;
      REXLOG_INFO("[bangaio] Present: presentation interval {} (frames paced to {} Hz)", interval_bytes[3],
                  interval_bytes[3] ? 60 / interval_bytes[3] : 0);
    }
    PaceRenutSwap(interval_bytes[3]);
    return;
  }
#endif
  __imp__sub_8216FE50(ctx, base);  // the original calls the Swap hooked above, which counts the frame
}
