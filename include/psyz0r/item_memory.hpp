#pragma once
#include <cmath>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <optional>
namespace psyz0r {
struct ItemEstimate { double expected_respawn; double observed_at; };
// Prediction only: unseen enemy pickups may invalidate an expected respawn.
class ItemMemory {
public:
    bool pickup(const std::string& id,double now,double respawn_seconds,bool perceptible) {
        if(!perceptible) return false;
        if(id.empty()||!std::isfinite(now)||!std::isfinite(respawn_seconds)||now<0||respawn_seconds<=0)
            throw std::invalid_argument("Invalid item observation");
        auto it=items_.find(id);
        if(it!=items_.end()&&now<=it->second.observed_at) return false;
        items_[id]={now+respawn_seconds,now}; return true;
    }
    std::optional<ItemEstimate> estimate(const std::string& id) const {
        auto it=items_.find(id); return it==items_.end()?std::nullopt:std::optional<ItemEstimate>(it->second);
    }
    void reset() {items_.clear();}
private:
    std::unordered_map<std::string,ItemEstimate> items_;
};
}
