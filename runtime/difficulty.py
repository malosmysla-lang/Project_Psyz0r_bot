"""Between-match policy; no server commands, score/physics modification or aim assist.

The adapter must supply a verified full duel summary and stable human identity.
Execution profiles are proposals for a future controller, not live QL tuning.
"""
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re


@dataclass(frozen=True)
class DuelResult:
    match_id: str
    opponent_id: str
    map_id: str
    bot_frags: int
    human_frags: int
    active_seconds: float
    combat_samples: int
    full_duel: bool = True
    verified: bool = False
    aborted: bool = False
    forfeit: bool = False
    intentional_tilt: bool = False
    leaving: bool = False


def explicit_answer(text):
    """Exact human phrases only: gg and free-text containing 'yes' are not consent."""
    text = re.sub(r'\^[0-9]', '', str(text)).casefold().strip()
    text = re.sub(r'[.!?,:;]+$', '', text).strip()
    yes = {'да', 'давай', 'согласен', 'согласна', 'ещё', 'еще', 'реванш',
           'давай ещё', 'давай еще', 'ещё карту', 'еще карту', 'yes', 'y', 'sure',
           'rematch', 'yes rematch', 'gg yes', 'gg да', 'gg давай'}
    no = {'нет', 'не хочу', 'не надо', 'хватит', 'no', 'n', 'no thanks', 'gg no', 'gg нет'}
    return True if text in yes else False if text in no else None


class DifficultySession:
    def __init__(self, config=None):
        self.config = config if config is not None else json.loads(
            (Path(__file__).resolve().parents[1] / 'config/difficulty.json').read_text(encoding='utf-8'))
        self._validate()
        self.levels = {}  # Session memory, keyed by stable human identity; not permanent storage.
        self.active = None
        self.pending = None
        self.finished = set()
        self.journal = []

    def _validate(self):
        c = self.config
        if c['initial_level'] != 3 or [p['level'] for p in c['profiles']] != list(range(1, 6)):
            raise ValueError('Exactly five levels and initial level 3 are required')
        for key in ('min_active_seconds', 'min_combat_samples', 'clear_frag_margin', 'reply_timeout'):
            value = c[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError('Invalid difficulty threshold: ' + key)
        if not 0 < c['clear_margin_ratio'] <= 1:
            raise ValueError('Invalid relative score margin')
        for p in c['profiles']:
            for key in ('reaction_ms', 'decision_interval_ms'):
                if not isinstance(p[key], (int, float)) or not math.isfinite(p[key]) or p[key] <= 0:
                    raise ValueError('Invalid profile timing')
            if p['accuracy_percent'] is not None or p['aim_error_degrees'] is not None:
                raise ValueError('Aim/accuracy values require a separate owner-approved implementation')
            if p['execution_enabled'] is not False:
                raise ValueError('Live execution profiles are not verified')

    def trace(self, reason, **fields):
        self.journal.append(dict(reason=reason, **fields))
        self.journal = self.journal[-1024:]

    def level(self, opponent):
        return self.levels.get(str(opponent), 3)

    def profile(self, opponent):
        return dict(self.config['profiles'][self.level(opponent) - 1])

    def begin(self, match_id, opponent, map_id, now):
        opponent = str(opponent)
        if self.active:
            if self.active[:3] == (match_id, opponent, map_id):
                return self.active[3]
            raise ValueError('Finish or cancel the active match first')
        p = self.pending
        if (p and p['accepted'] and p['opponent'] == opponent and p['map_id'] != map_id
                and now <= p['deadline']):
            self.levels[opponent] = p['next_level']
            self.trace('level_applied_on_next_map', level=p['next_level'], opponent=opponent)
        elif p:
            self.trace('proposal_not_applied', opponent=opponent)
        self.pending = None
        current = self.level(opponent)
        self.levels.setdefault(opponent, current)
        self.active = (match_id, opponent, map_id, current)
        self.trace('match_started_level_frozen', match_id=match_id, level=current)
        return current

    def finish(self, result, now):
        if result.match_id in self.finished:
            return None
        if not self.active or self.active[:3] != (result.match_id, str(result.opponent_id), result.map_id):
            raise ValueError('Result does not match the active duel')
        for score in (result.bot_frags, result.human_frags):
            if type(score) is not int:  # Quake scores can be negative after suicides.
                raise ValueError('Scores must be integers')
        if (not math.isfinite(result.active_seconds) or result.active_seconds < 0
                or type(result.combat_samples) is not int or result.combat_samples < 0):
            raise ValueError('Invalid duel evidence')
        current = self.active[3]
        self.active = None
        self.finished.add(result.match_id)
        self.pending = None
        if result.leaving or result.aborted or not result.full_duel or not result.verified:
            self.trace('no_rematch_unverified_incomplete_or_leaving', match_id=result.match_id)
            return None
        proposed, reason = current, 'close_match'
        if result.forfeit or result.intentional_tilt:
            reason = 'unreliable_forfeit_or_intentional_tilt'
        elif (result.active_seconds < self.config['min_active_seconds']
              or result.combat_samples < self.config['min_combat_samples']):
            reason = 'insufficient_evidence'
        else:
            gap = result.human_frags - result.bot_frags
            denominator = max(1, abs(result.bot_frags), abs(result.human_frags))
            if abs(gap) >= self.config['clear_frag_margin'] and abs(gap) / denominator >= self.config['clear_margin_ratio']:
                proposed = min(5, current + 1) if gap > 0 else max(1, current - 1)
                reason = 'human_clear_win' if gap > 0 else 'bot_clear_win'
                if proposed == current:
                    reason = 'level_boundary'
        message = ('GG! Реванш? :)' if proposed == current
                   else f'GG! Ещё карту на {proposed}-м уровне?')
        self.pending = dict(match_id=result.match_id, opponent=str(result.opponent_id),
                            map_id=result.map_id, next_level=proposed, current_level=current,
                            reason=reason, sent=False, accepted=False,
                            deadline=now + self.config['reply_timeout'])
        self.trace('rematch_proposed', current=current, proposed=proposed, adaptation_reason=reason)
        return message

    def mark_sent(self, now):
        if self.pending and not self.pending['sent']:
            self.pending['sent'] = True
            self.pending['deadline'] = now + self.config['reply_timeout']
            self.trace('rematch_question_sent')

    def answer(self, opponent, text, now, *, human=True):
        p = self.pending
        if (not human or not p or not p['sent']
                or p['opponent'] != str(opponent) or now > p['deadline']):
            return None
        answer = explicit_answer(text)
        if p['accepted'] and answer is not False:
            return None
        if answer is None:
            self.trace('ambiguous_rematch_answer_ignored')
        elif answer:
            p['accepted'] = True
            p['deadline'] = now + self.config['reply_timeout']
            self.trace('rematch_accepted_waiting_for_next_map', next_level=p['next_level'])
        else:
            self.pending = None
            self.trace('rematch_declined')
        return answer

    def cancel(self, *, opponent=None):
        self.active = None
        self.pending = None
        self.trace('session_cancelled', opponent=opponent)
