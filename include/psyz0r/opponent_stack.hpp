#pragma once
#include <algorithm>
#include <cmath>
#include <optional>
#include <string>
#include <stdexcept>
namespace psyz0r {
struct ExactOpponentStack {
    std::string opponent_id, match_id, map_id, source;
    unsigned respawn_generation=0;
    double observed_at=0;
    int health=0, armor=0;
    bool verified=false, alive=false;
};
struct StackContext {
    std::string opponent_id, match_id, map_id;
    unsigned respawn_generation=0;
};
// Continuous damage budget only: not an exact discrete weapon kill calculator.
inline double damage_budget(int health,int armor,double absorption) {
    if(health<0 || armor<0 || !std::isfinite(absorption) || absorption<=0 || absorption>=1)
        throw std::invalid_argument("Invalid stack/rules");
    return health + std::min(static_cast<double>(armor),health*absorption/(1-absorption));
}
inline std::optional<ExactOpponentStack> current_stack(const std::optional<ExactOpponentStack>& sample,
    const StackContext& context,double now,double ttl=0.25) {
    if(!sample || !sample->verified || !sample->alive || sample->source.empty() ||
       context.opponent_id.empty() || context.match_id.empty() || context.map_id.empty() ||
       sample->opponent_id!=context.opponent_id || sample->match_id!=context.match_id ||
       sample->map_id!=context.map_id || sample->respawn_generation!=context.respawn_generation ||
       !std::isfinite(now) || !std::isfinite(sample->observed_at) || sample->observed_at<0 ||
       !std::isfinite(ttl) || ttl<=0 || now<sample->observed_at || now-sample->observed_at>ttl ||
       sample->health<=0 || sample->armor<0) return std::nullopt;
    return sample;
}
}
