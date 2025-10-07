#!/usr/bin/env python3
"""
Title: lowbass's Blackjack Casino Game with Card Tracking
Author: Joshua "lowbass" Sommerfeldt
Date: 2025-01-28
Purpose: A sleek terminal-based Blackjack game with realistic card tracking and currency system
"""

import os
import sys
import json
import random
import signal
import atexit
import logging
from datetime import datetime
from typing import List, Tuple, Optional, Dict
from enum import Enum
from pathlib import Path
from time import sleep

# Configure logging with verbose mode
DEBUG = True  # Toggle for verbose logging (default ON)
LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s'
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format=LOG_FORMAT,
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('🎰 Blackjack')

# ANSI color codes for sleek terminal interface
class Colors:
    """Terminal color codes for a sleek interface"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BG_GREEN = '\033[42m'
    BG_RED = '\033[41m'
    CLEAR = '\033[2J\033[H'

class Suit(Enum):
    """Card suits with Unicode symbols"""
    SPADES = ('♠', 'black')
    HEARTS = ('♥', 'red')
    DIAMONDS = ('♦', 'red')
    CLUBS = ('♣', 'black')

class Card:
    """Represents a playing card with suit and rank"""
    
    def __init__(self, suit: Suit, rank: str):
        self.suit = suit
        self.rank = rank
        self.is_face_up = True
        logger.debug(f"🎴 Created card: {rank} of {suit.name}")
    
    def __str__(self):
        """Display card with color coding"""
        if not self.is_face_up:
            return f"{Colors.BLUE}[??]{Colors.RESET}"
        
        symbol, color = self.suit.value
        color_code = Colors.RED if color == 'red' else Colors.WHITE
        return f"{color_code}{self.rank}{symbol}{Colors.RESET}"
    
    def get_value(self) -> List[int]:
        """Return possible values for the card (Ace can be 1 or 11)"""
        if self.rank in ['J', 'Q', 'K']:
            return [10]
        elif self.rank == 'A':
            return [1, 11]
        else:
            return [int(self.rank)]

    def get_hilo_value(self) -> int:
        """Return the Hi-Lo value for card counting"""
        if self.rank in ['10', 'J', 'Q', 'K', 'A']:
            return -1
        elif self.rank in ['2', '3', '4', '5', '6']:
            return 1
        return 0

class Deck:
    """Manages a shoe of cards with tracking of used cards"""
    
    def __init__(self, num_decks: int = 6):
        """Initialize with multiple decks like a real casino shoe"""
        self.num_decks = num_decks
        self.cards: List[Card] = []
        self.used_cards: List[Card] = []
        self.running_count = 0
        self.reshuffle_threshold = 0.25  # Reshuffle when 25% cards remain
        logger.info(f"🎲 Initializing shoe with {num_decks} decks")
        self.reset()
    
    @property
    def true_count(self) -> float:
        """Calculate true count based on remaining decks"""
        remaining_decks = len(self.cards) / 52
        if remaining_decks == 0:
            return 0
        return self.running_count / remaining_decks

    def reset(self):
        """Create fresh shoe of cards"""
        self.cards = []
        self.used_cards = []
        self.running_count = 0
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        
        # Create multiple decks
        for _ in range(self.num_decks):
            for suit in Suit:
                for rank in ranks:
                    self.cards.append(Card(suit, rank))
        
        self.shuffle()
        logger.info(f"✨ Shoe ready with {len(self.cards)} cards")
    
    def shuffle(self):
        """Shuffle the remaining cards"""
        random.shuffle(self.cards)
        logger.debug(f"🔄 Shuffled {len(self.cards)} cards")
    
    def draw(self) -> Card:
        """Draw a card from the shoe"""
        if self.needs_reshuffle():
            logger.warning("⚠️ Shoe running low, reshuffling...")
            self.reshuffle()
        
        card = self.cards.pop()
        self.used_cards.append(card)
        self.running_count += card.get_hilo_value()
        logger.debug(f"📤 Drew card: {card}, Running Count: {self.running_count}, {len(self.cards)} remaining")
        return card
    
    def needs_reshuffle(self) -> bool:
        """Check if shoe needs reshuffling"""
        total = len(self.cards) + len(self.used_cards)
        return len(self.cards) < (total * self.reshuffle_threshold)
    
    def reshuffle(self):
        """Reshuffle all cards back into shoe"""
        self.cards.extend(self.used_cards)
        self.used_cards = []
        self.shuffle()
        logger.info(f"♻️ Reshuffled shoe: {len(self.cards)} cards available")
    
    def get_stats(self) -> Dict:
        """Get statistics about the shoe"""
        return {
            'remaining': len(self.cards),
            'used': len(self.used_cards),
            'total': len(self.cards) + len(self.used_cards),
            'percentage_used': (len(self.used_cards) / (len(self.cards) + len(self.used_cards))) * 100
        }

class Hand:
    """Represents a player or dealer hand"""

    def __init__(self, name: str, is_split: bool = False):
        self.name = name
        self.cards: List[Card] = []
        self.is_standing = False
        self.is_busted = False
        self.is_split = is_split
        logger.debug(f"✋ Created hand for {name}")
    
    def add_card(self, card: Card):
        """Add a card to the hand"""
        self.cards.append(card)
        logger.debug(f"➕ {self.name} received {card}")
        self.check_bust()
    
    def get_value(self) -> int:
        """Calculate best hand value (handling Aces)"""
        possible_values = [0]
        
        for card in self.cards:
            if not card.is_face_up:
                continue
                
            new_values = []
            for current_val in possible_values:
                for card_val in card.get_value():
                    new_values.append(current_val + card_val)
            possible_values = new_values
        
        # Find best value that doesn't bust
        valid_values = [v for v in possible_values if v <= 21]
        if valid_values:
            return max(valid_values)
        return min(possible_values)  # All bust, return lowest
    
    def check_bust(self):
        """Check if hand is busted"""
        if self.get_value() > 21:
            self.is_busted = True
            logger.info(f"💥 {self.name} BUSTED with {self.get_value()}")
    
    def is_blackjack(self) -> bool:
        """Check if hand is a natural blackjack (not from split)"""
        return len(self.cards) == 2 and self.get_value() == 21 and not self.is_split
    
    def display(self, show_all: bool = True) -> str:
        """Display hand with cards"""
        cards_str = ' '.join(str(card) for card in self.cards)
        value = self.get_value() if show_all else '??'
        
        status = ""
        if self.is_blackjack() and show_all:
            status = f" {Colors.YELLOW}⭐ BLACKJACK!{Colors.RESET}"
        elif self.is_busted:
            status = f" {Colors.RED}💥 BUST!{Colors.RESET}"
        
        return f"{self.name}: {cards_str} (Value: {value}){status}"

class Player:
    """Represents the player with currency tracking"""
    
    def __init__(self, name: str = "Player", starting_balance: float = 1000):
        self.name = name
        self.balance = starting_balance
        self.total_winnings = 0
        self.hands_played = 0
        self.hands_won = 0
        logger.info(f"👤 Player '{name}' initialized with ${self.balance:.2f}")

    @property
    def save_file(self) -> Path:
        """Generate save file path from player name."""
        safe_name = "".join(c for c in self.name if c.isalnum() or c in (' ', '_')).rstrip()
        return Path.home() / f'blackjack_save_{safe_name}.json'
    
    def can_bet(self, amount: float) -> bool:
        """Check if player can afford bet"""
        return self.balance >= amount
    
    def place_bet(self, amount: float) -> bool:
        """Place a bet if affordable"""
        if self.can_bet(amount):
            self.balance -= amount
            logger.debug(f"💰 Bet ${amount:.2f} placed. Balance: ${self.balance:.2f}")
            return True
        return False
    
    def win(self, amount: float):
        """Add winnings to balance"""
        self.balance += amount
        self.total_winnings += amount
        self.hands_won += 1
        logger.info(f"🎉 Won ${amount:.2f}! New balance: ${self.balance:.2f}")
    
    def save_progress(self):
        """Save player progress to file"""
        try:
            save_data = {
                'name': self.name,
                'balance': self.balance,
                'total_winnings': self.total_winnings,
                'hands_played': self.hands_played,
                'hands_won': self.hands_won,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.save_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            logger.debug(f"💾 Progress for '{self.name}' saved to {self.save_file}")
        except Exception as e:
            logger.error(f"❌ Failed to save progress for '{self.name}': {e}")
    
    def load_progress(self) -> bool:
        """Load player progress from file based on self.name."""
        try:
            if self.save_file.exists():
                with open(self.save_file, 'r') as f:
                    data = json.load(f)
                
                # Sanity check name in file, but don't overwrite self.name
                if data.get('name') != self.name:
                    logger.warning(f"Name mismatch in save file: expected '{self.name}', found '{data.get('name')}'. Loading data anyway.")

                self.balance = data['balance']
                self.total_winnings = data.get('total_winnings', 0)
                self.hands_played = data.get('hands_played', 0)
                self.hands_won = data.get('hands_won', 0)
                
                logger.info(f"📂 Progress for '{self.name}' loaded from {data.get('timestamp', 'N/A')}")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to load progress for '{self.name}': {e}")
        return False
    
    def get_stats(self) -> str:
        """Get player statistics"""
        win_rate = (self.hands_won / self.hands_played * 100) if self.hands_played > 0 else 0
        return (f"{Colors.CYAN}═══ Player Stats ═══{Colors.RESET}\n"
                f"Balance: ${self.balance:.2f}\n"
                f"Total Winnings: ${self.total_winnings:.2f}\n"
                f"Hands Played: {self.hands_played}\n"
                f"Hands Won: {self.hands_won}\n"
                f"Win Rate: {win_rate:.1f}%")

class BlackjackGame:
    """Main game controller with all game logic"""
    
    def __init__(self):
        self.deck = Deck(num_decks=6)
        self.player = Player()
        self.dealer_hand: Optional[Hand] = None
        self.player_hands: List[Hand] = []
        self.hand_bets: Dict[Hand, float] = {}
        self.running = True

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        atexit.register(self.shutdown)

        logger.info("🎰 Blackjack game initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"📡 Received signal {signum}, shutting down gracefully...")
        self.running = False
        self.shutdown()
        sys.exit(0)
    
    def shutdown(self):
        """Graceful shutdown - save progress and cleanup"""
        logger.info("🔚 Initiating graceful shutdown...")
        
        try:
            # Save player progress
            self.player.save_progress()
            
            # Clear screen
            print(Colors.CLEAR)
            
            # Display final stats
            print(self.player.get_stats())
            
            # Farewell message
            print(f"\n{Colors.GREEN}Thanks for playing! See you next time! 👋{Colors.RESET}")
            
            logger.info("✅ Shutdown complete. Goodbye! 🎲")
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_table(self, active_hand: Optional[Hand] = None):
        """Display the current game table"""
        self.clear_screen()
        print(f"{Colors.BG_GREEN}{Colors.WHITE}{'═' * 50}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}🎰 LOWBASS'S BLACKJACK CASINO 🎰{Colors.RESET}".center(60))
        print(f"{Colors.BG_GREEN}{Colors.WHITE}{'═' * 50}{Colors.RESET}\n")

        # Display shoe stats
        stats = self.deck.get_stats()
        print(f"📊 Shoe: {stats['remaining']}/{stats['total']} cards "
              f"({100-stats['percentage_used']:.1f}% remaining)")

        # Card Counting Display
        true_count = self.deck.true_count
        if true_count >= 2:
            count_advice = f"{Colors.GREEN}Player advantage. Bet high!{Colors.RESET}"
        elif true_count <= -2:
            count_advice = f"{Colors.RED}Dealer advantage. Bet low.{Colors.RESET}"
        else:
            count_advice = f"{Colors.YELLOW}Neutral. Bet normally.{Colors.RESET}"

        print(f"📈 Count: {self.deck.running_count} (True: {true_count:.2f}) | {count_advice}\n")

        # Display dealer hand
        if self.dealer_hand:
            print(f"{Colors.RED}{'─' * 30}{Colors.RESET}")
            print(self.dealer_hand.display(show_all=False))
            print(f"{Colors.RED}{'─' * 30}{Colors.RESET}\n")

        # Display player hands
        if self.player_hands:
            for i, hand in enumerate(self.player_hands, 1):
                # Highlight active hand
                if hand == active_hand:
                    print(f"{Colors.YELLOW}{'─' * 30}{Colors.RESET}")
                    print(f"{Colors.YELLOW}▶ Hand {i} (ACTIVE) ◀{Colors.RESET}")
                else:
                    print(f"{Colors.BLUE}{'─' * 30}{Colors.RESET}")
                    if len(self.player_hands) > 1:
                        print(f"Hand {i}:")

                print(hand.display())
                print(f"Bet: ${self.hand_bets[hand]:.2f}")

                if hand == active_hand:
                    print(f"{Colors.YELLOW}{'─' * 30}{Colors.RESET}\n")
                else:
                    print(f"{Colors.BLUE}{'─' * 30}{Colors.RESET}\n")

        # Display balance
        print(f"💰 Balance: ${self.player.balance:.2f}\n")
    
    def get_bet(self) -> float:
        """Get bet amount from player"""
        while True:
            try:
                print(f"💵 Balance: ${self.player.balance:.2f}")
                bet_input = input(f"{Colors.YELLOW}Enter bet amount (or 'q' to quit): {Colors.RESET}")

                if bet_input.lower() == 'q':
                    self.running = False
                    return 0

                bet = float(bet_input)

                # Validate bet
                if bet <= 0:
                    print(f"{Colors.RED}❌ Bet must be positive!{Colors.RESET}")
                    continue

                if not self.player.can_bet(bet):
                    print(f"{Colors.RED}❌ Insufficient funds!{Colors.RESET}")
                    continue

                return bet

            except ValueError:
                print(f"{Colors.RED}❌ Invalid bet amount!{Colors.RESET}")

    def can_split(self, hand: Hand) -> bool:
        """Check if the hand can be split"""
        if len(hand.cards) != 2:
            return False

        # Check if both cards have the same rank
        if hand.cards[0].rank != hand.cards[1].rank:
            return False

        # Check if player has sufficient funds for additional bet
        current_bet = self.hand_bets[hand]
        if not self.player.can_bet(current_bet):
            return False

        return True
    
    def deal_initial_cards(self):
        """Deal initial two cards to player and dealer"""
        logger.info("🎴 Dealing initial cards...")

        player_hand = self.player_hands[0]

        # Deal cards alternating
        player_hand.add_card(self.deck.draw())
        self.dealer_hand.add_card(self.deck.draw())
        player_hand.add_card(self.deck.draw())

        # Dealer's second card is face down initially
        dealer_second = self.deck.draw()
        dealer_second.is_face_up = False
        self.dealer_hand.add_card(dealer_second)

        logger.debug("✅ Initial cards dealt")
    
    def player_turn(self):
        """Handle player's turn for all hands"""
        hand_index = 0

        while hand_index < len(self.player_hands):
            current_hand = self.player_hands[hand_index]

            # Check for blackjack on initial hand
            if current_hand.is_blackjack() and len(self.player_hands) == 1:
                self.display_table(current_hand)
                print(f"{Colors.YELLOW}⭐ BLACKJACK! You win!{Colors.RESET}")
                sleep(2)
                current_hand.is_standing = True
                hand_index += 1
                continue

            # Check if this is a split ace (gets only one card)
            is_split_ace = (current_hand.is_split and
                          len(current_hand.cards) > 0 and
                          current_hand.cards[0].rank == 'A')

            if is_split_ace and len(current_hand.cards) == 2:
                # Split aces get only one card and automatically stand
                self.display_table(current_hand)
                print(f"{Colors.CYAN}Split Aces receive only one card.{Colors.RESET}")
                sleep(2)
                current_hand.is_standing = True
                hand_index += 1
                continue

            # Play the hand
            while not current_hand.is_standing and not current_hand.is_busted:
                self.display_table(current_hand)

                # Build action prompt
                actions = "(H)it, (S)tand"

                # Double down only on initial 2 cards
                if len(current_hand.cards) == 2:
                    current_bet = self.hand_bets[current_hand]
                    if self.player.can_bet(current_bet):
                        actions += ", (D)ouble Down"

                # Split only on initial 2 cards with same rank
                if self.can_split(current_hand):
                    actions += ", (P)split"

                action = input(f"{Colors.CYAN}{actions}? {Colors.RESET}").lower()

                if action == 'h':
                    # Hit - draw another card
                    current_hand.add_card(self.deck.draw())
                    logger.info(f"👊 Player hits. Hand value: {current_hand.get_value()}")

                elif action == 's':
                    # Stand - end turn
                    current_hand.is_standing = True
                    logger.info(f"✋ Player stands at {current_hand.get_value()}")

                elif action == 'd' and len(current_hand.cards) == 2:
                    # Double down - only allowed on initial hand
                    current_bet = self.hand_bets[current_hand]
                    if self.player.can_bet(current_bet):
                        self.player.place_bet(current_bet)
                        self.hand_bets[current_hand] *= 2
                        current_hand.add_card(self.deck.draw())
                        current_hand.is_standing = True
                        logger.info(f"⚡ Player doubles down! Bet: ${self.hand_bets[current_hand]:.2f}")
                    else:
                        print(f"{Colors.RED}❌ Insufficient funds to double down!{Colors.RESET}")
                        sleep(2)

                elif action == 'p' and self.can_split(current_hand):
                    # Split the hand
                    current_bet = self.hand_bets[current_hand]
                    self.player.place_bet(current_bet)

                    # Create two new hands from the split
                    card1 = current_hand.cards[0]
                    card2 = current_hand.cards[1]

                    hand1 = Hand("Player", is_split=True)
                    hand1.add_card(card1)
                    hand1.add_card(self.deck.draw())

                    hand2 = Hand("Player", is_split=True)
                    hand2.add_card(card2)
                    hand2.add_card(self.deck.draw())

                    # Replace current hand with the two split hands
                    self.player_hands[hand_index] = hand1
                    self.player_hands.insert(hand_index + 1, hand2)

                    # Set bets for both hands
                    del self.hand_bets[current_hand]
                    self.hand_bets[hand1] = current_bet
                    self.hand_bets[hand2] = current_bet

                    logger.info(f"✂️ Player splits hand into two hands with ${current_bet:.2f} each")

                    # Start over with the first split hand
                    current_hand = hand1
                    continue

                else:
                    print(f"{Colors.RED}❌ Invalid action!{Colors.RESET}")
                    sleep(1)

            hand_index += 1
    
    def dealer_turn(self):
        """Handle dealer's turn following house rules"""
        # Reveal dealer's hidden card
        self.dealer_hand.cards[1].is_face_up = True
        logger.info(f"🎭 Dealer reveals: {self.dealer_hand.get_value()}")
        
        # Dealer must hit on 16 and below, stand on 17 and above
        while self.dealer_hand.get_value() < 17:
            self.display_table()
            sleep(1)  # Dramatic pause
            
            self.dealer_hand.add_card(self.deck.draw())
            logger.info(f"🎴 Dealer draws. Hand value: {self.dealer_hand.get_value()}")
        
        if not self.dealer_hand.is_busted:
            self.dealer_hand.is_standing = True
            logger.info(f"✋ Dealer stands at {self.dealer_hand.get_value()}")
    
    def determine_winner(self, hand: Hand) -> Tuple[str, float]:
        """Determine winner and calculate payout for a specific hand"""
        player_val = hand.get_value()
        dealer_val = self.dealer_hand.get_value()
        bet = self.hand_bets[hand]

        # Check for busts
        if hand.is_busted:
            return "dealer", 0

        if self.dealer_hand.is_busted:
            return "player", bet * 2

        # Check for blackjacks (natural 21, not from split)
        if hand.is_blackjack() and not self.dealer_hand.is_blackjack():
            return "player", bet * 2.5  # Blackjack pays 3:2

        if self.dealer_hand.is_blackjack() and not hand.is_blackjack():
            return "dealer", 0

        # Compare values
        if player_val > dealer_val:
            return "player", bet * 2
        elif dealer_val > player_val:
            return "dealer", 0
        else:
            return "push", bet  # Tie - return bet
    
    def play_hand(self):
        """Play a single hand of blackjack"""
        # Get bet
        initial_bet = self.get_bet()
        if not self.running:
            return

        # Place bet
        self.player.place_bet(initial_bet)

        # Initialize hands
        initial_hand = Hand("Player")
        self.player_hands = [initial_hand]
        self.hand_bets = {initial_hand: initial_bet}
        self.dealer_hand = Hand("Dealer")

        # Deal initial cards
        self.deal_initial_cards()

        # Player's turn (handles all hands including splits)
        self.player_turn()

        # Check if all player hands busted
        all_busted = all(hand.is_busted for hand in self.player_hands)

        # Dealer's turn (only if player has at least one non-busted hand)
        if not all_busted:
            self.dealer_turn()

        # Determine winner for each hand and display results
        self.display_table()
        print(f"\n{Colors.BOLD}{'=' * 50}{Colors.RESET}")
        print(f"{Colors.BOLD}RESULTS:{Colors.RESET}\n")

        total_payout = 0
        hands_won = 0

        for i, hand in enumerate(self.player_hands, 1):
            winner, payout = self.determine_winner(hand)
            bet = self.hand_bets[hand]

            # Display result for this hand
            if len(self.player_hands) > 1:
                print(f"Hand {i}:")

            if winner == "player":
                self.player.balance += payout
                total_payout += payout
                hands_won += 1
                profit = payout - bet
                print(f"{Colors.GREEN}  🎉 WIN! Profit: ${profit:.2f} (Payout: ${payout:.2f}){Colors.RESET}")
            elif winner == "dealer":
                print(f"{Colors.RED}  😔 LOSE! Lost: ${bet:.2f}{Colors.RESET}")
            else:
                self.player.balance += payout
                total_payout += payout
                print(f"{Colors.YELLOW}  🤝 PUSH! Bet returned: ${payout:.2f}{Colors.RESET}")

        # Display total results
        if len(self.player_hands) > 1:
            print(f"\n{Colors.BOLD}Total Payout: ${total_payout:.2f}{Colors.RESET}")

        print(f"{Colors.BOLD}{'=' * 50}{Colors.RESET}\n")

        # Update stats
        self.player.hands_played += 1
        if hands_won > 0:
            self.player.hands_won += 1

        # Incremental save after each hand
        self.player.save_progress()

        # Wait for player to continue
        input(f"{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    
    def main_menu(self) -> str:
        """Display main menu and get choice"""
        self.clear_screen()
        print(f"{Colors.BOLD}{Colors.GREEN}{'═' * 50}")
        print("🎰 WELCOME TO LOWBASS'S BLACKJACK CASINO 🎰".center(50))
        print(f"{'═' * 50}{Colors.RESET}\n")
        
        print("1. 🎮 Play Game")
        print("2. 📊 View Statistics")
        print("3. 📖 Rules & Help")
        print("4. 🚪 Exit\n")
        
        return input(f"{Colors.YELLOW}Choose option (1-4): {Colors.RESET}")
    
    def show_rules(self):
        """Display game rules"""
        self.clear_screen()
        print(f"{Colors.CYAN}{'═' * 50}")
        print("📖 BLACKJACK RULES".center(50))
        print(f"{'═' * 50}{Colors.RESET}\n")
        
        rules = """
        🎯 OBJECTIVE:
        Beat the dealer by getting closer to 21 without going over.

        🎴 CARD VALUES:
        • Number cards: Face value (2-10)
        • Face cards (J,Q,K): 10 points
        • Ace: 1 or 11 points (whichever is better)

        🎮 GAMEPLAY:
        1. Place your bet
        2. Receive 2 cards (face up)
        3. Dealer receives 2 cards (1 face up, 1 face down)
        4. Choose to Hit (draw), Stand (keep), Double Down, or Split
        5. Dealer reveals hidden card and draws until 17+

        💰 PAYOUTS:
        • Regular win: 1:1 (double your bet)
        • Blackjack: 3:2 (2.5x your bet)
        • Push (tie): Bet returned

        🎲 SPECIAL RULES:
        • Dealer must hit on 16 and below
        • Dealer must stand on 17 and above
        • Blackjack beats regular 21
        • Double Down only on initial 2 cards
        • Split only when both cards have the same rank
        • Split requires an additional bet equal to the original
        • Split Aces receive only one additional card each
        • 21 after a split does not count as Blackjack (pays 1:1)

        📊 CARD TRACKING:
        • This game uses a 6-deck shoe (312 cards)
        • Cards are tracked and not replaced until reshuffle
        • Shoe reshuffles when 75% of cards are used
        """
        
        print(rules)
        input(f"\n{Colors.CYAN}Press Enter to return to menu...{Colors.RESET}")
    
    def run(self):
        """Main game loop"""
        logger.info("🚀 Starting lowbass's Blackjack Casino...")
        
        while self.running:
            choice = self.main_menu()
            
            if choice == '1':
                # Play Game (New or Load)
                print(f"\n{Colors.GREEN}Let's play!{Colors.RESET}")
                name = input("Enter your name: ")
                self.player = Player(name if name else "Player")

                if self.player.load_progress():
                    print(f"\n{Colors.CYAN}Welcome back, {self.player.name}! Your progress has been loaded.{Colors.RESET}")
                else:
                    print(f"\n{Colors.GREEN}Welcome, {self.player.name}! A new profile will be created for you.{Colors.RESET}")
                
                sleep(2)

                while self.running and self.player.balance > 0:
                    self.play_hand()
                
                if self.player.balance <= 0:
                    print(f"\n{Colors.RED}💸 You're out of money! Game Over!{Colors.RESET}")
                    input("Press Enter to return to the menu...")

            elif choice == '2':
                # View statistics
                self.clear_screen()
                # If we want to view stats for any player, we'd need to prompt for a name here.
                # For now, it shows stats of the last player.
                print(self.player.get_stats())
                input(f"\n{Colors.CYAN}Press Enter to return to menu...{Colors.RESET}")
            
            elif choice == '3':
                # Show rules
                self.show_rules()
            
            elif choice == '4':
                # Exit
                self.running = False
            
            else:
                print(f"{Colors.RED}❌ Invalid choice!{Colors.RESET}")
                sleep(1)
        
        logger.info("🏁 Game loop ended")

def main():
    """Entry point with error handling"""
    try:
        logger.info("🎲 lowbass's Blackjack Casino starting up...")
        game = BlackjackGame()
        game.run()
    except KeyboardInterrupt:
        logger.info("⌨️ Keyboard interrupt received")
    except Exception as e:
        logger.error(f"💀 Fatal error: {e}", exc_info=True)
    finally:
        logger.info("👋 lowbass's Blackjack Casino shutting down. Thanks for playing!")

if __name__ == "__main__":
    main()