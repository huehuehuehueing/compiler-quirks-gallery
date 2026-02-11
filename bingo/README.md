# Compiler Optimization Bingo

A study tool for COSC-69.16 that generates interactive bingo cards testing
knowledge of compiler optimizations, assembly patterns, and hardening features
from the Compiler Optimization Gallery.

## Generating Cards

Requires Python 3.8+ and Jinja2 (`pip install jinja2`).

```
python bingo/generate.py [OPTIONS]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--output, -o` | `bingo-cards/` | Output directory |
| `--count, -n` | `1` | Number of cards to generate |
| `--seed, -s` | random | Base seed (cards use seed, seed+1, ...) |
| `--difficulty, -d` | `mixed` | Preset: `easy`, `mixed`, or `hard` |

Example: generate a classroom set of 30 unique cards:

```
python bingo/generate.py -o cards/ -n 30 -d mixed
```

Each card is a self-contained HTML file with no external dependencies.
The `--seed` flag makes generation reproducible (same seed = same card).

## How to Play

Each card is a 5x5 grid of 24 challenge squares plus a FREE center square.
Every square shows a **prompt** face-up (a question about compiler behavior).
The **answer** is hidden on the back.

### Game Flow

1. **Read the prompt** on a square.
2. **Formulate your answer** before touching the card. Say it out loud
   (classroom) or write it down (self-study).
3. **Click the square** to flip it and reveal the correct answer.
4. **Compare honestly**: did your answer match? The card operates on the
   **honor system** -- clicking always flips the square and awards points.
   There is no enforced right/wrong check. If you got it wrong, you still
   see the correct answer (that's the learning part), but you should not
   count those points toward your score.

Flipping is permanent for the current session. Use the **Reset** button to
start over. Use **Print** to save a snapshot of your card.

### Modes

Toggle between modes with the buttons at the top of the card.

- **Classroom**: The instructor reads prompts aloud or projects a question.
  Students locate the matching square on their card and formulate an answer.
  Clicking a square opens a modal showing the correct answer with **Correct**
  and **Wrong** buttons. Pressing Correct flips the square (blue) and awards
  points. Pressing Wrong flips the square (gray, inactive) with no points
  awarded. Category labels are dimmed so students rely on the prompt text.

- **Self-Study**: Category labels are emphasized to help you navigate the
  card by topic. Work through squares at your own pace, using the gallery
  source files as reference.

- **Quiz**: An enforced-answer mode that replaces the honor system with
  keyword verification. Clicking a square opens a modal where you type your
  answer. The system checks whether your input contains a recognized keyword
  (case-insensitive substring match). Correct answers flip the square and
  award points. Wrong answers show "Incorrect" feedback and let you retry.
  Clicking **Give Up** reveals the answer (gray-tinted square) but awards no
  points. The scoreboard shows "Score" instead of "Points" and adds a
  **Correct** counter to distinguish verified answers from gave-up reveals.

## Scoring

### Points per Square

Each square has a difficulty rating shown by star badges in the corner:

| Stars | Difficulty | Points | Color |
|-------|------------|--------|-------|
| ★     | Easy       | 1      | Green |
| ★★    | Medium     | 2      | Orange |
| ★★★   | Hard       | 3      | Red |

You earn a square's points when you **correctly answer its prompt** and then
flip it to confirm. Since the card cannot verify your answer, this is
self-reported: only count points for answers you genuinely got right.

### Bingo Bonus

Completing an entire line of 5 squares (row, column, or diagonal) earns a
**+5 point bonus** per line. The FREE center square counts toward all lines
it belongs to. Completed lines are highlighted with a gold border.

There are 12 possible lines: 5 rows + 5 columns + 2 diagonals.

### Scoreboard

The header displays three counters:

- **Points**: your running total (square points + bingo bonuses)
- **Bingos**: number of completed lines
- **Flipped**: how many of the 24 squares you have revealed

### Honest Scoring in Practice

Because the card cannot distinguish correct from incorrect answers, here are
two suggested approaches:

**Track mistakes mentally**: Flip every square you attempt. At the end,
subtract the point value of any squares you got wrong from the displayed
total. Your real score = displayed score - penalty.

**Only flip correct answers**: Before clicking, commit to your answer. If
you are wrong (you can peek at the answer key or ask the instructor), leave
the square face-up and move on. Your displayed score is accurate, and
unflipped squares show what you still need to study.

## Difficulty Presets

The `--difficulty` flag controls the mix of square ratings on the card:

| Preset | ★ Easy | ★★ Medium | ★★★ Hard | Max Points |
|--------|--------|-----------|----------|------------|
| `easy` | 12 | 8 | 4 | 40 |
| `mixed` | 8 | 10 | 6 | 46 |
| `hard` | 4 | 8 | 12 | 56 |

Max points assume all 24 squares answered correctly, before bingo bonuses.

## Card Layout

Difficulty is not randomly scattered -- it follows a spatial pattern:

- **Corners** (4 squares): prefer hard challenges
- **Center ring** (8 squares adjacent to FREE): prefer easy challenges
- **Edges** (12 remaining squares): prefer medium challenges

This means easier squares cluster near the middle of the card and harder
ones sit at the periphery, so completing a bingo line typically requires
answering a mix of difficulties.

## Challenge Types

The 53 challenges in the pool span six categories:

| Type | Example Prompt |
|------|---------------|
| **Flag Effect** | "This flag inserts a stack canary..." → `-fstack-protector-all` |
| **Assembly Pattern** | "cmov instead of jcc + mov indicates..." → If-conversion |
| **Scenario Comparison** | "At -O3 but not -O2, array loops gain SSE instructions..." → Auto-vectorization |
| **Compiler Difference** | "GCC reads canary from %fs:0x28. Where does MSVC read it?" → `__security_cookie` |
| **Security Implication** | "memset to clear a password may be removed because..." → Dead store |
| **True/False** | "volatile prevents ALL optimizations on a variable" → False |

## License

Copyright (c) 2026 Larry H (<l.gr [at] dartmouth [dot] edu>)

Part of the Compiler Optimization Gallery, licensed under the
GNU Affero General Public License v3.0 (AGPL-3.0).
See [LICENSE](../LICENSE) for the full license text.
