// bangaio-nx 1.0.0 (2026-10-29, the user's request): the player's settings. The shipped renut.toml holds only these
// three, under plain names; every other setting is the build's own default (Renut on deko3d, the full game, no logging,
// docked 900 lines shown at 1080, SMAA on). ApplyBangaioSettings (RenutApp::OnPreSetup, after the toml is loaded) hands
// each one the toml sets to the key it stands for, so those keys keep working on their own too.
//
// - docked_resolution -> banjo_renut_render_height_docked (the display stays 1920x1080 docked: 900 is drawn at 1600x900
//   and scaled up after the playfield, with the HUD and text drawn at 1080; 1080 draws the whole frame at 1080).
// - smaa -> banjo_renut_smaa.
// - language -> user_language, the XConfig language the game reads (ExGetXConfigSetting(3, 9) in sub_8215E218). The
//   game tests for 2 (Japanese) and 4 (French) only (its 19 checks of that function's result); anything else is English.

#include <string>

#include <rex/cvar.h>

REXCVAR_DEFINE_INT32(docked_resolution, 900, "Bangai-O",
                     "Docked resolution: 900 = the game drawn at 1600x900 and shown at 1920x1080 (the HUD and text at "
                     "1080); 1080 = everything at 1920x1080 (more GPU work). Handheld is always 1280x720")
    .range(720, 1080);
REXCVAR_DEFINE_BOOL(smaa, true, "Bangai-O",
                    "SMAA anti-aliasing of the playfield (the HUD and its text are left as they are)");
REXCVAR_DEFINE_STRING(language, "english", "Bangai-O", "The game's language: english, japanese or french")
    .allowed({"english", "japanese", "french"});

namespace bangaio {

void ApplyBangaioSettings() {
  using rex::cvar::GetFlagSource;
  using rex::cvar::SetFlagByName;
  using rex::cvar::Source;
  if (GetFlagSource("docked_resolution") != Source::kDefault)
    SetFlagByName("banjo_renut_render_height_docked", std::to_string(REXCVAR_GET(docked_resolution)));
  if (GetFlagSource("smaa") != Source::kDefault)
    SetFlagByName("banjo_renut_smaa", REXCVAR_GET(smaa) ? "true" : "false");
  if (GetFlagSource("language") != Source::kDefault) {
    const std::string language = REXCVAR_GET(language);
    SetFlagByName("user_language", language == "japanese" ? "2" : language == "french" ? "4" : "1");
  }
}

}  // namespace bangaio
