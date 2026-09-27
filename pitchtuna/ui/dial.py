"""Optional graphical tuner dial (pygame).

A windowed, instrument-style dial with a semicircular cents gauge, a large
note readout, a level meter and lock coloring. Works with any iterable of
mono float32 frames, so it can run on a live microphone stream or on a finite
synthetic source (used by ``--dial --smoke-test`` to render a screenshot).
"""

from __future__ import annotations

import math
from typing import Iterable, Optional

from ..pitch import detect_pitch
from ..stability import StabilityTracker
from .table import evaluate

WIDTH, HEIGHT = 520, 400

BG = (18, 22, 33)
PANEL = (28, 34, 50)
TEXT = (235, 240, 250)
MUTED = (120, 130, 150)
GREEN = (80, 220, 130)
AMBER = (245, 190, 80)
RED = (240, 90, 90)
BLUE = (90, 160, 240)


def _font(size: int):
    try:
        return pygame.font.SysFont("arial,helvetica", size)
    except Exception:
        return pygame.font.Font(None, int(size * 0.6))


def _gauge_point(pivot, radius: int, angle_deg: float):
    rad = math.radians(angle_deg)
    x = pivot[0] + radius * math.cos(rad)
    y = pivot[1] - radius * math.sin(rad)
    return int(x), int(y)


def _draw_gauge(surface, cents: float, in_tune: bool, active: bool = True) -> None:
    pivot = (WIDTH // 2, 250)
    radius = 108
    # ticks: -50 cents maps to 180° (far left), 0 -> 90° (top), +50 -> 0°
    for c in range(-50, 51, 5):
        angle = 180 - (c + 50) / 100 * 180
        major = c % 25 == 0
        r1 = radius - (14 if major else 8)
        color = GREEN if abs(c) <= 5 else MUTED
        width = 3 if major else 1
        pygame.draw.line(surface, color, _gauge_point(pivot, r1, angle),
                         _gauge_point(pivot, radius, angle), width)
        if major:
            label = _font(16).render(f"{c:+d}".replace("+0", "0"), True, MUTED)
            pos = _gauge_point(pivot, radius - 28, angle)
            surface.blit(label, label.get_rect(center=pos))
    # needle (neutral/grey while silent)
    if active:
        angle = 180 - (max(-50, min(50, cents)) + 50) / 100 * 180
        tip = _gauge_point(pivot, radius - 6, angle)
        pygame.draw.line(surface, RED if not in_tune else GREEN, pivot, tip, 4)
    else:
        tip = _gauge_point(pivot, radius - 6, 90)
        pygame.draw.line(surface, MUTED, pivot, tip, 2)
    pygame.draw.circle(surface, TEXT, pivot, 7)
    pygame.draw.circle(surface, PANEL, pivot, 4)


def _draw(surface, ev, tuning, a4: float) -> None:
    surface.fill(BG)
    pygame.draw.rect(surface, PANEL, (0, 0, WIDTH, 46))
    title = f"{tuning.instrument.name}    A4={a4:g} Hz"
    surface.blit(_font(22).render(title, True, TEXT), (16, 11))

    if not ev.voiced:
        note_text = "--"
        color = MUTED
        sub = "Listening ... play a note"
    else:
        note_text = ev.detected_note
        color = GREEN if ev.in_tune else (AMBER if ev.locked else BLUE)
        if ev.in_tune:
            sub = "In tune"
        else:
            sub = f"{ev.cents:+.1f} cents  {'sharp' if ev.cents > 0 else 'flat'}"
    big = _font(78).render(note_text, True, color)
    surface.blit(big, big.get_rect(center=(WIDTH // 2, 92)))
    sub_surf = _font(22).render(sub, True, TEXT if ev.voiced else MUTED)
    surface.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, 138)))

    _draw_gauge(surface, ev.cents if ev.voiced else 0.0, ev.in_tune, ev.voiced)

    # target + lock
    target = f"Target: {ev.target_label}  {ev.target_note}"
    surface.blit(_font(18).render(target, True, MUTED), (24, 360))
    lock = "LOCKED" if ev.locked else ("tracking" if ev.voiced else "idle")
    lock_surf = _font(18).render(lock, True, GREEN if ev.locked else MUTED)
    surface.blit(lock_surf, lock_surf.get_rect(right=WIDTH - 24, top=360))

    # level meter
    meter_w = 200
    filled = int(min(1.0, ev.rms / 0.5) * meter_w)
    pygame.draw.rect(surface, PANEL, (24, 382, meter_w, 10), border_radius=4)
    if filled:
        pygame.draw.rect(surface, GREEN, (24, 382, filled, 10), border_radius=4)


def run_dial(
    frame_source: Iterable,
    sample_rate: int,
    tuning,
    a4: float,
    max_frames: Optional[int] = None,
    save_path: Optional[str] = None,
    in_tune_cents: float = 5.0,
) -> None:
    global pygame
    import pygame

    pygame.init()
    pygame.display.set_caption("PitchTuna")
    surface = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    tracker = StabilityTracker(a4)

    count = 0
    last_ev = None
    running = True
    frame_iter = iter(frame_source)
    while running:
        try:
            frame = next(frame_iter)
        except StopIteration:
            break
        result = detect_pitch(frame, sample_rate, rms_gate=0.01)
        state = tracker.update(result)
        ev = evaluate(state, tuning, a4, in_tune_cents)
        last_ev = ev
        _draw(surface, ev, tuning, a4)
        pygame.display.flip()
        clock.tick(30)
        count += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE,
                pygame.K_q,
            ):
                running = False
        if max_frames is not None and count >= max_frames:
            running = False

    if save_path and last_ev is not None:
        pygame.image.save(surface, save_path)
    pygame.quit()
