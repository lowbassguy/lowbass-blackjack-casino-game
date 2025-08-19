# Lowbass's Blackjack Casino Game

A sleek, terminal-based Blackjack game with realistic card tracking and a persistent currency system.

## Features

- **Realistic Casino Experience**: Uses a 6-deck shoe with proper card tracking
- **Smart Card Management**: Automatic reshuffling when 75% of cards are used
- **Persistent Progress**: Save and load your game progress including balance and statistics
- **Colorful Terminal Interface**: Beautiful ANSI color-coded display for an immersive experience
- **Comprehensive Statistics**: Track your wins, losses, and overall performance
- **Standard Blackjack Rules**: 
  - Dealer hits on 16 and below, stands on 17+
  - Blackjack pays 3:2
  - Double down available on initial hand
  - Push (tie) returns your bet

## Installation

### Requirements
- Python 3.6 or higher
- No external dependencies required (uses only Python standard library)

### Running the Game

```bash
python lowbass-blackjack-game.py
```

Or make it executable:

```bash
chmod +x lowbass-blackjack-game.py
./lowbass-blackjack-game.py
```

## How to Play

1. **Start**: Choose "New Game" from the main menu
2. **Enter Your Name**: Personalize your gaming experience
3. **Place Your Bet**: You start with $1000
4. **Make Decisions**: 
   - **Hit (H)**: Draw another card
   - **Stand (S)**: Keep your current hand
   - **Double Down (D)**: Double your bet and receive exactly one more card
5. **Win Conditions**:
   - Get closer to 21 than the dealer without going over
   - Dealer busts (goes over 21)
   - Get a Blackjack (21 with first two cards)

## Game Controls

- `1-5`: Menu navigation
- `H`: Hit (draw a card)
- `S`: Stand (keep current hand)
- `D`: Double down (when available)
- `Q`: Quit during betting
- `Ctrl+C`: Graceful shutdown with progress save

## Save System

Your progress is automatically saved to `~/.blackjack_save.json` including:
- Current balance
- Total winnings
- Hands played and won
- Win rate statistics

## Debug Mode

The game runs in verbose debug mode by default. To disable, edit line 23 in the source code:
```python
DEBUG = False  # Set to False for quieter operation
```

## Card Shoe Details

- Uses 6 standard decks (312 cards total)
- Cards are tracked and not replaced until reshuffle
- Automatic reshuffle when only 25% of cards remain
- Real-time display of remaining cards in the shoe

## Author

Created by Joshua "lowbass" Sommerfeldt

## License

This software is provided for personal use only. See LICENSE file for details.

## Enjoy the Game!

Good luck at the tables! Remember to gamble responsibly. 🎰🎲
