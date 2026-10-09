"""Event-driven chat policy. Adapter supplies verified duel events and time.

No game access: returns messages for an adapter to send. Times are monotonic
seconds, active_seconds excludes warmup and pauses. Call tick once per batch
after submitting events so message priorities can be resolved together.
"""
import json
from pathlib import Path
import random
import re


def render(line, player, steam_id, owner):
    text = line['text']
    if line['category'] == 'opening':
        return '^1' + text + '^7'
    colors = {'nekitz0r': '4', 'PsyRoZ': '3', 'Cooller': '3',
              'Nikolai "Agent"': '3', 'Intel_maps': '3', 'SkillZ': '3',
              'GG': '3', 'WP': '3', '$100': '3', 'red armor': '1',
              'rockets': '1', 'rocket': '1', 'rail': '1'}
    pattern = r'(?<!\w)(' + '|'.join(re.escape(k) for k in sorted(colors, key=len, reverse=True)) + r')(?!\w)'
    text = re.sub(pattern, lambda m: '^' + colors[next(k for k in colors if k.lower() == m[0].lower())] + m[0] + '^7', text, flags=re.I)
    if '{player}' in text:
        if not player:
            return None
        name = re.sub(r'\^[0-9]', '', str(player)).replace('^', '')
        name = ''.join(c for c in name if c.isprintable())
        if not name:
            return None
        text = text.replace('{player}', '^' + ('4' if str(steam_id) == str(owner) else '3') + name + '^7')
    return '^7' + text + '^7'


class ChatPolicy:
    def __init__(self, config=None, rng=None):
        self.config = config or json.loads((Path(__file__).resolve().parents[1] / 'config/chat.json').read_text(encoding='utf-8'))
        self.rng = rng or random.Random()
        self.lines = {line['id']: line for line in self.config['lines']}
        if len(self.lines) != len(self.config['lines']):
            raise ValueError('Duplicate chat line ID')
        self.last_time = float('-inf')
        self.last_line = None
        self.duel_id = None
        self.diagnostics = []
        self.cancel()

    def cancel(self):
        """Map change, disconnect, new duel or bot removal cancels pending output."""
        self.active = False
        self.present = False
        self.pending = {}

    def start(self, duel_id, player, steam_id, now, active_seconds=0):
        if duel_id == self.duel_id:
            return
        self.cancel()
        self.duel_id = duel_id
        self.player, self.steam_id = player, steam_id
        self.active = self.present = True
        self.used, self.events = set(), set()
        self.retort_times = []
        self.behavior_mood = 'normal'
        self.behavior_reactions = 0
        self.interactions = {}
        self.last_weapon_item = float('-inf')
        self.rare_used = self.ended = False
        self.next_period = active_seconds + self.config['period']
        self.offer(1, ['S01', 'S02', 'S03'], now, None)

    def offer(self, priority, ids, now, ttl=5, repeat=False):
        eligible = [self.lines[i] for i in ids if self.lines[i]['enabled'] and (repeat or i not in self.used)
                    and not (i == 'P04' and str(self.steam_id) == str(self.config['owner_steam_id']))
                    and render(self.lines[i], self.player, self.steam_id, self.config['owner_steam_id'])]
        alternatives = [line for line in eligible if line['id'] != self.last_line]
        if alternatives:
            eligible = alternatives
        if eligible and priority not in self.pending:
            self.pending[priority] = (self.rng.choice(eligible), None if ttl is None else now + ttl)

    def trace(self, now, reason, **fields):
        self.diagnostics.append(dict(time=now, reason=reason, **fields))
        self.diagnostics = self.diagnostics[-1024:]

    def forget_opponent(self, steam_id):
        """Disconnect/team change: clear the opponent and cancel its pending output."""
        self.interactions.pop(str(steam_id), None)
        if str(steam_id) == str(getattr(self, 'steam_id', None)):
            self.cancel()
            self.duel_id = None

    def interaction_record(self, event_id, now, record):
        """Consume a verified C++ ReactionTrace, not a guessed weapon selection.

        Transport/sensors are not implemented here. Opponent IDs must be stable
        session identities mapped to the chat's human Steam ID by the adapter.
        """
        opponent = str(record.get('opponent_id', ''))
        if not self.active or opponent != str(self.steam_id) or event_id in self.events:
            return
        self.events.add(event_id)
        reason = record.get('reason')
        if not record.get('source') or reason not in (
                'gauntlet_damage_below_threshold', 'revenge_started',
                'corpse_retaliation_enabled'):
            self.trace(now, 'interaction_ignored', source=record.get('source'), event=reason)
            return
        state = self.interactions.setdefault(opponent, {
            'last_gauntlet': float('-inf'), 'last_line': None,
            'last_reply_time': None, 'last_reply_type': None, 'corpse_announced': False})
        if reason == 'corpse_retaliation_enabled':
            if state['corpse_announced']:
                return
            state['corpse_announced'] = True
            self.offer(-2, self.config['corpse_reply_ids'], now,
                       self.config['corpse_reply_ttl'], repeat=True)
            self.trace(now, 'corpse_reply_offered', source=record['source'])
            return
        if now - state['last_gauntlet'] < self.config['gauntlet_reply_interval']:
            self.trace(now, 'gauntlet_topic_cooldown')
            return
        if now - self.last_time < self.config['cooldown']:
            self.trace(now, 'gauntlet_global_cooldown')
            return
        if self.rng.random() >= self.config['gauntlet_reply_probability']:
            self.trace(now, 'gauntlet_probability_suppressed')
            return
        ids = [i for i in self.config['gauntlet_reply_ids'] if i != state['last_line']]
        self.offer(-1, ids, now, 0, repeat=True)
        self.trace(now, 'gauntlet_reply_offered', source=record['source'])

    def weapon_item_offer(self, ids, now):
        if now - self.last_weapon_item < self.config['weapon_item_interval']:
            self.trace(now, 'weapon_item_topic_cooldown')
            return
        if self.rng.random() >= self.config['weapon_item_probability']:
            self.trace(now, 'weapon_item_probability_suppressed')
            return
        self.offer(3, ids, now, 0)

    def item_event(self, event_id, now, *, opponent_steam_id, kind, perceptible=False):
        """Only a visible/audible pickup of the actual duel participant."""
        if (not self.active or not perceptible or event_id in self.events
                or str(opponent_steam_id) != str(self.steam_id)):
            return
        self.events.add(event_id)
        self.weapon_item_offer(self.config.get('item_reply_ids', {}).get(kind, []), now)

    def death(self, event_id, now, *, bot_killed_human=False, human_killed_bot=False,
              weapon='', opponent_steam_id=None):
        """Caller must exclude suicides/environment/other players; IDs dedupe hooks."""
        if not self.active or event_id in self.events or str(opponent_steam_id) != str(self.steam_id):
            return
        self.events.add(event_id)
        if human_killed_bot and not bot_killed_human:
            if self.rng.random() >= self.config['praise_probability']:
                return
            ids = ['P01', 'P02', 'P03', 'P04', 'P05']
            if weapon.lower() == 'railgun':
                self.weapon_item_offer(['P06'], now)
                if 3 in self.pending:
                    return
            self.offer(2, ids, now)

        elif bot_killed_human and not human_killed_bot:
            ids = {'railgun': ['K01'], 'rocket': ['K02', 'K03', 'K04'],
                   'rocket_launcher': ['K02', 'K03', 'K04']}.get(weapon.lower(), [])
            self.weapon_item_offer(ids, now)

    def opponent_chat(self, event_id, now, *, sender_steam_id, text,
                      sender_is_bot=False, is_reply=False):
        """Adapter supplies human identity; responses to responses are excluded."""
        if (not self.active or sender_is_bot or is_reply
                or str(sender_steam_id) != str(self.steam_id) or event_id in self.events):
            return
        self.events.add(event_id)
        words = set(re.findall(r'\w+', str(text).lower()))
        if not words.intersection(self.config.get('retort_words', [])):
            return
        if now - self.last_time < self.config['cooldown']:
            return
        window = self.config.get('retort_window', 60)
        self.retort_times = [t for t in self.retort_times if now - t < window]
        if len(self.retort_times) >= self.config.get('retort_limit', 1):
            return
        self.retort_times.append(now)
        self.offer(2, self.config.get('retort_ids', []), now, 0)

    def behavior_update(self, event_id, now, mood):
        """Called by future adapter with mood from the C++ decision journal."""
        if not self.active or event_id in self.events:
            return
        self.events.add(event_id)
        if mood == self.behavior_mood:
            return
        self.behavior_mood = mood
        if self.behavior_reactions >= self.config.get('behavior_reaction_limit', 2):
            return
        ids = self.config.get('behavior_ids', {}).get(mood, [])
        if ids and now - self.last_time >= self.config['cooldown']:
            self.offer(2, ids, now, 0)
            self.behavior_reactions += 1

    def decision_record(self, event_id, now, record):
        """Consume the mood field of a C++ decision record; never transmit commands."""
        mood = record.get('mood')
        if mood not in ('normal', 'relaxed', 'lead_loss_tilt', 'surrender_tilt', 'pressure_escape'):
            raise ValueError('Unknown behavior mood')
        self.behavior_update(event_id, now, mood)
        for reaction in record.get('interaction_events', []):
            self.interaction_record(('interaction', reaction['event_id']), now, reaction)

    def end(self, now, result=None, *, aborted=False, leaving=False):
        if not self.present or self.ended:
            return
        self.ended = True
        self.active = False
        self.pending.clear()
        if aborted:
            return
        ids = ['E06'] if leaving else {'human_win': ['E01', 'E02'],
            'bot_win': ['E03'], 'tie': ['E04', 'E05']}.get(result, [])
        self.offer(0, ids, now, self.config.get('end_reply_ttl', 25))

    def tick(self, now, active_seconds):
        if not self.present:
            return None
        self.pending = {p: entry for p, entry in self.pending.items()
                        if entry[1] is None or now <= entry[1]}
        if self.active and active_seconds >= self.next_period:
            self.next_period = active_seconds + self.config['period']
            rare = not self.rare_used and self.rng.random() < self.config['rare_probability']
            category = 'rare' if rare else 'ordinary'
            if self.rng.random() < self.config.get('periodic_probability', 0):
                ids = [i for i, line in self.lines.items() if line['category'] == category
                       and i not in self.config.get('weapon_item_ids', [])]
                self.offer(3, ids, now, 0)
        if not self.pending:
            return None
        priority = min(self.pending)
        line, expiry = self.pending[priority]
        if now - self.last_time < self.config['cooldown']:
            # Event/periodic messages are dropped instead of accumulating.
            self.pending = {p: entry for p, entry in self.pending.items() if p in (-2, 0, 1)}
            self.trace(now, 'global_cooldown')
            return None
        if line['id'] in self.config.get('weapon_item_ids', []) and now - self.last_weapon_item < self.config['weapon_item_interval']:
            self.pending.pop(priority)
            self.trace(now, 'weapon_item_topic_cooldown')
            return None
        self.pending.clear()
        self.used.add(line['id'])
        self.rare_used |= line['category'] == 'rare'
        self.last_time, self.last_line = now, line['id']
        if line['id'] in self.config.get('weapon_item_ids', []):
            self.last_weapon_item = now
        state = self.interactions.setdefault(str(self.steam_id), {'last_gauntlet': float('-inf'), 'last_line': None, 'corpse_announced': False})
        state['last_reply_time'], state['last_reply_type'] = now, line['category']
        if line['category'] in ('gauntlet_reaction', 'corpse_reaction'):
            state['last_reply_time'], state['last_reply_type'] = now, line['category']
            if line['category'] == 'gauntlet_reaction':
                state['last_gauntlet'], state['last_line'] = now, line['id']
        self.trace(now, 'message_sent', line_id=line['id'], category=line['category'])
        return render(line, self.player, self.steam_id, self.config['owner_steam_id'])
