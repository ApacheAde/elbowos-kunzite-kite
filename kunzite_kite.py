#!/usr/bin/env python3
"""Kunzite Kite — neon thermal-kite arcade for ElbowOS. Python 3 + pygame.

Steer the winch, pay out or reel the gold tether, and ride teal thermals.
Snag lilac petals. Dodge crimson storm motes. Not a clone of prior ElbowOS packs.
"""
import math
import os
import random
import subprocess
import sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/KUNZITE_KITE_ElbowOS.mp4")
INK = (18, 6, 32)
ROSE = (255, 92, 186)
LILAC = (214, 168, 255)
GOLD = (255, 214, 92)
TEAL = (64, 255, 214)
CRIMSON = (255, 64, 92)
MIST = (255, 236, 250)


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY and not RECORD else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption("Kunzite Kite")
        self.font = pygame.font.Font(None, 86)
        self.small = pygame.font.Font(None, 46)
        self.sky = self._sky()
        self.reset()

    def _sky(self):
        surf = pygame.Surface((W, H))
        for y in range(H):
            t = y / H
            col = (18 + int(48 * t), 6 + int(18 * t), 36 + int(40 * (1 - t)))
            pygame.draw.line(surf, col, (0, y), (W, y))
        return surf

    def reset(self):
        random.seed(11)
        self.winch = 540.0
        self.length = 640.0
        self.kx, self.ky = 540.0, 980.0
        self.vx, self.vy = 0.0, 0.0
        self.score = 0
        self.t = 0
        self.trail = []
        self.pops = []
        self.petals = [self._petal(i * 170) for i in range(9)]
        self.bolts = [self._bolt(i * 280) for i in range(5)]

    def _petal(self, y):
        return [random.randint(120, W - 120), y % (H - 400) + 180, random.uniform(-1.2, 1.2)]

    def _bolt(self, y):
        return [random.randint(140, W - 140), y % (H - 500) + 220, random.uniform(2.2, 3.6)]

    def thermal(self, x, y):
        lift = 0.0
        for i in range(4):
            cx = (220 + i * 230 + math.sin(self.t * 0.01 + i) * 80) % W
            lift += max(0.0, 1.0 - abs(x - cx) / 160.0) * 0.55
        return lift

    def step(self, steer, reel):
        self.t += 1
        self.winch = max(90, min(W - 90, self.winch + steer * 11))
        self.length = max(260, min(1180, self.length + reel * 9))
        lift = self.thermal(self.kx, self.ky)
        self.vy -= 0.22 + lift * 0.55
        self.vx += math.sin(self.t * 0.05 + self.kx * 0.01) * 0.18
        dx, dy = self.winch - self.kx, (H - 130) - self.ky
        dist = math.hypot(dx, dy) or 1
        if dist > self.length:
            pull = (dist - self.length) * 0.08
            self.vx += dx / dist * pull
            self.vy += dy / dist * pull
        elif dist < self.length * 0.72:
            self.vy -= 0.35
        self.vx *= 0.985
        self.vy *= 0.985
        self.kx += self.vx
        self.ky += self.vy
        self.kx = max(40, min(W - 40, self.kx))
        self.ky = max(160, min(H - 200, self.ky))
        self.trail.append((self.kx, self.ky))
        self.trail = self.trail[-18:]
        for p in self.petals:
            p[1] -= 1.6 + self.thermal(p[0], p[1])
            p[0] += p[2] + math.sin(self.t * 0.04 + p[1]) * 0.6
            if p[1] < 140 or p[0] < 40 or p[0] > W - 40:
                p[:] = self._petal(H - 180)
            if math.hypot(p[0] - self.kx, p[1] - self.ky) < 54:
                self.score += 10
                self.pops.append([p[0], p[1], 18])
                p[:] = self._petal(H - 80)
        for b in self.bolts:
            b[1] += b[2]
            b[0] += math.sin(self.t * 0.03 + b[1] * 0.01) * 1.4
            if b[1] > H - 160:
                b[:] = self._bolt(160)
            if math.hypot(b[0] - self.kx, b[1] - self.ky) < 46:
                self.score = max(0, self.score - 5)
                self.vx += 6 if self.kx > b[0] else -6
                self.pops.append([b[0], b[1], 14])
                b[:] = self._bolt(140)
        self.pops = [[x, y, n - 1] for x, y, n in self.pops if n > 1]

    def autopilot(self):
        goal = min(self.petals, key=lambda p: abs(p[0] - self.kx) + abs(p[1] - self.ky) * 0.45)
        steer = 1 if goal[0] > self.winch + 12 else -1 if goal[0] < self.winch - 12 else 0
        reel = 1 if goal[1] < self.ky - 40 else -1 if goal[1] > self.ky + 80 else 0
        for b in self.bolts:
            if abs(b[0] - self.kx) < 110 and 0 < b[1] - self.ky < 180:
                steer = -1 if b[0] >= self.kx else 1
                reel = -1
        if self.t % 90 < 8:
            steer = 1 if (self.t // 90) % 2 == 0 else -1
        return steer, reel

    def draw(self, surf):
        surf.blit(self.sky, (0, 0))
        for i in range(4):
            cx = int((220 + i * 230 + math.sin(self.t * 0.01 + i) * 80) % W)
            ribbon = pygame.Surface((180, H), pygame.SRCALPHA)
            pygame.draw.polygon(ribbon, (64, 255, 214, 36), [(70, 0), (110, 0), (150, H), (30, H)])
            surf.blit(ribbon, (cx - 90, 0))
        for i, (x, y) in enumerate(self.trail):
            pygame.draw.circle(surf, (255, 140, 210), (int(x), int(y)), 3 + i // 5)
        pygame.draw.line(surf, GOLD, (int(self.winch), H - 130), (int(self.kx), int(self.ky)), 4)
        pygame.draw.rect(surf, GOLD, (int(self.winch) - 36, H - 148, 72, 22), border_radius=8)
        pygame.draw.circle(surf, ROSE, (int(self.winch), H - 136), 8)
        ang = math.sin(self.t * 0.12) * 0.35
        pts = []
        for a, r in ((-1.2 + ang, 34), (0.15, 18), (1.2 + ang, 34), (3.0, 22)):
            pts.append((self.kx + math.cos(a) * r, self.ky + math.sin(a) * r * 1.35))
        pygame.draw.polygon(surf, ROSE, pts)
        pygame.draw.polygon(surf, MIST, pts, 3)
        pygame.draw.line(surf, GOLD, (self.kx - 28, self.ky), (self.kx + 28, self.ky), 2)
        for p in self.petals:
            pygame.draw.circle(surf, LILAC, (int(p[0]), int(p[1])), 16)
            pygame.draw.circle(surf, MIST, (int(p[0]), int(p[1])), 6)
        for b in self.bolts:
            x, y = int(b[0]), int(b[1])
            bolt = [(x, y - 28), (x + 10, y - 4), (x + 2, y - 4), (x + 16, y + 26), (x - 2, y + 2), (x - 12, y + 2)]
            pygame.draw.polygon(surf, CRIMSON, bolt)
        for x, y, n in self.pops:
            pygame.draw.circle(surf, GOLD, (int(x), int(y)), n, 2)
        title = self.font.render("KUNZITE KITE", True, MIST)
        score = self.font.render(f"SCORE {self.score}", True, GOLD)
        tag = self.small.render("x.com/ElbowOS", True, TEAL)
        surf.blit(title, title.get_rect(center=(W // 2, 78)))
        surf.blit(score, score.get_rect(center=(W // 2, 156)))
        surf.blit(tag, tag.get_rect(center=(W // 2, H - 58)))

    def play_interactive(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            steer = reel = 0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                    self.reset()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                steer = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                steer = 1
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                reel = -1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                reel = 1
            self.step(steer, reel)
            self.draw(self.screen)
            pygame.display.flip()
            clock.tick(FPS)
        pygame.quit()

    def record(self):
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
            "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "veryfast", "-movflags", "+faststart", OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = FPS * SECS
        try:
            for _ in range(frames):
                steer, reel = self.autopilot()
                self.step(steer, reel)
                self.draw(self.screen)
                proc.stdin.write(pygame.image.tobytes(self.screen, "RGB"))
        finally:
            if proc.stdin:
                proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore") if proc.stderr else ""
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1500:]}")
        print("wrote", OUT)
        pygame.quit()


def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()


if __name__ == "__main__":
    main()
