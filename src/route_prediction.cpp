#include "psyz0r/route_prediction.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <fstream>
#include <unordered_set>
namespace psyz0r {
RoutePatternSettings RoutePatternSettings::load(const std::string& path) {
    std::ifstream f(path);if(!f) throw std::runtime_error("Cannot open route prediction settings");
    RoutePatternSettings s;std::string key;double v;std::unordered_set<std::string> seen;
    while(f>>key) {
        if(!(f>>v)||!std::isfinite(v)||v<0||!seen.insert(key).second) throw std::invalid_argument("Invalid route pattern setting");
        if(key=="min_repeats"||key=="max_pattern_zones"||key=="max_observations") {
            if(v!=std::floor(v)||v>1024) throw std::invalid_argument("Invalid route pattern integer");
            if(key=="min_repeats") s.min_repeats=static_cast<int>(v);
            else if(key=="max_pattern_zones") s.max_pattern_zones=static_cast<int>(v);
            else s.max_observations=static_cast<int>(v);
        } else if(key=="history_seconds") s.history_seconds=v;
        else if(key=="forecast_ttl") s.forecast_ttl=v;
        else if(key=="timing_tolerance") s.timing_tolerance=v;
        else if(key=="minimum_confidence") s.minimum_confidence=v;
        else if(key=="mismatch_decay") s.mismatch_decay=v;
        else if(key=="initial_confidence") s.initial_confidence=v;
        else throw std::invalid_argument("Unknown route prediction setting");
    }
    RoutePredictor validation(s);return s;
}
RoutePredictor::RoutePredictor(RoutePatternSettings s):settings_(s) {
    if(s.min_repeats<3||s.min_repeats>100||s.max_pattern_zones<2||s.max_pattern_zones>32||s.max_observations>1024||s.max_observations<s.min_repeats*s.max_pattern_zones||
       !std::isfinite(s.history_seconds)||s.history_seconds<=0||!std::isfinite(s.forecast_ttl)||s.forecast_ttl<=0||
       !std::isfinite(s.timing_tolerance)||s.timing_tolerance<0||s.timing_tolerance>1||
       !std::isfinite(s.minimum_confidence)||s.minimum_confidence<=0||s.minimum_confidence>1||
       !std::isfinite(s.mismatch_decay)||s.mismatch_decay<0||s.mismatch_decay>=1||
       !std::isfinite(s.initial_confidence)||s.initial_confidence<s.minimum_confidence||s.initial_confidence>1)
        throw std::invalid_argument("Invalid route prediction settings");
}
void RoutePredictor::reset() {history_.clear();prediction_.reset();last_time_=-1;}
bool RoutePredictor::observe(const ZoneObservation& o) {
    if(!o.perceptible||o.source.empty()||o.zone.empty()) return false;
    if(!std::isfinite(o.time)||o.time<0||o.time<=last_time_) throw std::invalid_argument("Invalid zone observation time");
    last_time_=o.time;
    while(!history_.empty()&&o.time-history_.front().time>settings_.history_seconds) history_.pop_front();
    // Staying in one zone does not refresh forecast lifetime or count as a new cycle.
    if(!history_.empty()&&history_.back().zone==o.zone) return false;
    if(prediction_&&(o.time>prediction_->expires_at||o.zone!=prediction_->next_zone)) {
        prediction_->confidence*=settings_.mismatch_decay;
        if(prediction_->confidence<settings_.minimum_confidence) prediction_.reset();
    }
    history_.push_back(o);
    while(history_.size()>static_cast<std::size_t>(settings_.max_observations)) history_.pop_front();
    for(int length=2;length<=settings_.max_pattern_zones;++length) {
        const int needed=length*settings_.min_repeats;
        if(history_.size()<static_cast<std::size_t>(needed)) continue;
        const std::size_t first=history_.size()-needed;
        bool repeated=true;
        for(int i=length;i<needed;++i)
            if(history_[first+i].zone!=history_[first+i%length].zone) {repeated=false;break;}
        if(!repeated) continue;
        double interval=0;
        for(int i=length;i<needed;++i) interval+=history_[first+i].time-history_[first+i-length].time;
        interval/=(needed-length);
        for(int i=length;i<needed;++i)
            if(std::abs(history_[first+i].time-history_[first+i-length].time-interval)>interval*settings_.timing_tolerance) {
                repeated=false;break;
            }
        if(!repeated) continue;
        RouteForecast f;for(int i=0;i<length;++i) f.pattern.push_back(history_[first+i].zone);
        f.next_zone=f.pattern.front();
        double step=0;
        for(int i=length;i<needed;i+=length) step+=history_[first+i].time-history_[first+i-1].time;
        step/=(settings_.min_repeats-1);
        f.expected_time=o.time+step;f.confidence=settings_.initial_confidence;f.expires_at=o.time+settings_.forecast_ttl;
        prediction_=f;return true;
    }
    return true;
}
std::optional<RouteForecast> RoutePredictor::forecast(double now) const {
    if(!std::isfinite(now)||now<last_time_) throw std::invalid_argument("Invalid forecast time");
    if(!prediction_||now>=prediction_->expires_at) return std::nullopt;
    auto f=*prediction_;
    const double learned_at=f.expires_at-settings_.forecast_ttl;
    f.confidence*=std::max(0.0,1-(now-learned_at)/settings_.forecast_ttl);
    return f.confidence>=settings_.minimum_confidence?std::optional<RouteForecast>(f):std::nullopt;
}
}
