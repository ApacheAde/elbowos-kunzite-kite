# Kunzite Kite

Full-colour Python 3 neon thermal-kite arcade for [ElbowOS](https://x.com/ElbowOS).

A gold tether runs from a moving winch to a pink diamond kite. Teal thermals lift the kite. Snag lilac petals. Dodge crimson storm motes.

This is an original arcade toy. It is not a Nintendo ROM, not an emulator, and not a copy of the prior ElbowOS platformer, cards, slots, or bucket-wheel packs.

## Play

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 kunzite_kite.py --play
```

Controls: A / D or arrows move the winch. W / S or up / down reel the tether. R restarts.

## Record a 9:16 reel

```bash
python3 kunzite_kite.py --record
```

Headless autoplay writes a 1080x1920, 15-second, 30fps H.264 MP4 with title, score, and `x.com/ElbowOS` on the frames.

- Featured account: https://x.com/ElbowOS
- Drive reel: https://drive.google.com/file/d/1NLsdj4Zh5SJun6LpLCFCZ0EzPeCn0xyu/view
