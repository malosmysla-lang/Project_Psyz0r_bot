#pragma once
#include <array>
#include <cstdint>

namespace psyz0r {
enum class ControlTarget { ServerBot, ConnectedClient };
struct OwnState {
    std::int64_t server_time_ms = 0;
    std::array<float, 3> position{}, velocity{}, view_angles{};
    int health = 0, armor = 0, weapon = 0;
    bool alive = false, on_ground = false;
    bool state_verified = false, view_angles_valid = false;
};
struct GameCommand {
    std::uint64_t id = 0;
    std::int64_t server_time_ms = 0;
    std::array<float, 3> view_angles{};
    int forward = 0, right = 0;
    int weapon = 0;
    bool jump = false, attack = false;
    bool quiet_walk = false;
    int valid_for_ms = 0;
};
// Contract only. No retail QL implementation exists yet.
// Acceptance must not be interpreted as observed execution.
class GameInterface {
public:
    virtual ~GameInterface() = default;
    virtual ControlTarget target() const = 0;
    virtual OwnState read_own_state() = 0;
    virtual bool submit(const GameCommand&) = 0;
    virtual void stop() = 0;
};
}
