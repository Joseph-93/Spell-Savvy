#!/usr/bin/env python3
"""
Fill word lists to 2000 words each using Datamuse API.
Fetches real English words and avoids phrases.
Includes smart backfilling when letters run out of words.
"""

import requests
import time
import random
from pathlib import Path
from collections import defaultdict

# Target number of words per bucket
TARGET_WORDS_PER_BUCKET = 2000

# Letters with their relative frequency in English (to balance distribution)
# Common letters get more words, rare letters get fewer
LETTER_WEIGHTS = {
    'a': 100, 'b': 80, 'c': 80, 'd': 80, 'e': 100,
    'f': 70, 'g': 70, 'h': 80, 'i': 90, 'j': 30,
    'k': 50, 'l': 80, 'm': 80, 'n': 80, 'o': 90,
    'p': 80, 'q': 20, 'r': 80, 's': 90, 't': 90,
    'u': 70, 'v': 50, 'w': 70, 'x': 10, 'y': 50,
    'z': 10
}

def fetch_words_for_length_and_letter(word_length, starting_letter):
    """
    Fetch words of a specific length starting with a specific letter from Datamuse API.
    """
    # Build the pattern: letter + (length-1) question marks
    pattern = starting_letter + ('?' * (word_length - 1))
    url = f"https://api.datamuse.com/words?sp={pattern}&max=1000"
    
    try:
        print(f"  Fetching {word_length}-letter words starting with '{starting_letter}'...", end=' ')
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            return []
        
        data = response.json()
        
        # Filter out phrases (anything with spaces) and ensure correct length
        words = []
        for item in data:
            word = item.get('word', '').lower()
            # Skip if it contains a space (phrase) or isn't the right length
            if ' ' not in word and len(word) == word_length and word.isalpha():
                words.append(word)
        
        print(f"✓ Got {len(words)} words")
        return words
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def fill_word_list(word_length):
    """
    Fill a word list file to TARGET_WORDS_PER_BUCKET words.
    Includes smart backfilling when letters run out of words.
    """
    file_path = Path(__file__).parent / 'game' / 'management' / 'commands' / f'{word_length}_letter_words.txt'
    
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return
    
    # Read existing words
    with open(file_path, 'r', encoding='utf-8') as f:
        existing_words = set(line.strip().lower() for line in f if line.strip())
    
    current_count = len(existing_words)
    print(f"\n{'='*60}")
    print(f"📚 {word_length}-letter words")
    print(f"{'='*60}")
    print(f"Current count: {current_count}")
    print(f"Target count: {TARGET_WORDS_PER_BUCKET}")
    
    if current_count >= TARGET_WORDS_PER_BUCKET:
        print(f"✅ Already has {current_count} words (>= {TARGET_WORDS_PER_BUCKET}). Skipping.")
        return
    
    needed = TARGET_WORDS_PER_BUCKET - current_count
    print(f"Need to add: {needed} words\n")
    
    # Collect new words from each letter
    letter_words = {}  # Track words collected per letter
    all_collected_words = set()
    
    # Calculate how many words to fetch per letter based on weights
    total_weight = sum(LETTER_WEIGHTS.values())
    
    # Phase 1: Fetch from all letters based on weights
    print("Phase 1: Fetching words from all letters...")
    for letter in 'abcdefghijklmnopqrstuvwxyz':
        # Calculate proportional number of words for this letter
        letter_proportion = LETTER_WEIGHTS[letter] / total_weight
        fetch_target = int(needed * letter_proportion * 1.5) + 20  # Extra buffer
        
        words = fetch_words_for_length_and_letter(word_length, letter)
        
        # Filter out words we already have (existing or collected)
        new_words = [w for w in words if w not in existing_words and w not in all_collected_words]
        
        if new_words:
            # Randomly sample to avoid bias
            sample_size = min(len(new_words), fetch_target)
            sampled = random.sample(new_words, sample_size)
            letter_words[letter] = sampled
            all_collected_words.update(sampled)
        else:
            letter_words[letter] = []
        
        # Small delay to be nice to the API
        time.sleep(0.2)
    
    # Flatten all collected words
    all_new_words = list(all_collected_words)
    random.shuffle(all_new_words)
    
    print(f"\n📊 Phase 1 collected {len(all_new_words)} unique new words")
    
    # Phase 2: Smart backfilling if we're still short
    if len(all_new_words) < needed:
        shortage = needed - len(all_new_words)
        print(f"\n⚠️  Still need {shortage} more words!")
        print(f"Phase 2: Smart backfilling from letters with available words...")
        
        # Find letters that still have available words
        letters_with_more = []
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            # Check if this letter returned the max (likely has more)
            if len(letter_words.get(letter, [])) >= 100:  # Arbitrary threshold
                letters_with_more.append(letter)
        
        if letters_with_more:
            print(f"   Found {len(letters_with_more)} letters with potentially more words: {', '.join(letters_with_more)}")
            
            # Attempt to fill the gap
            attempts = 0
            max_attempts = len(letters_with_more) * 3  # Give it a good try
            
            while len(all_new_words) < needed and attempts < max_attempts:
                # Pick a random letter that likely has more words
                letter = random.choice(letters_with_more)
                
                # Fetch again (API returns random order, so we might get different words)
                print(f"   Backfill attempt {attempts + 1}: Fetching more from '{letter}'...", end=' ')
                words = fetch_words_for_length_and_letter(word_length, letter)
                
                # Filter out words we already have
                new_words = [w for w in words if w not in existing_words and w not in all_collected_words]
                
                if new_words:
                    # Add the new words
                    random.shuffle(new_words)
                    added_count = min(len(new_words), shortage)
                    to_add = new_words[:added_count]
                    
                    all_new_words.extend(to_add)
                    all_collected_words.update(to_add)
                    
                    shortage = needed - len(all_new_words)
                    print(f"✓ Added {added_count} words ({shortage} still needed)")
                else:
                    print(f"✗ No new words found")
                    # Remove this letter from the pool
                    letters_with_more.remove(letter)
                    if not letters_with_more:
                        print("   ⚠️  Exhausted all letters with available words")
                        break
                
                attempts += 1
                time.sleep(0.2)
            
            print(f"\n📊 Phase 2 collected {len(all_new_words) - (needed - shortage)} additional words")
        else:
            print("   ⚠️  No letters found with additional words available")
    
    # Take only what we need
    words_to_add = all_new_words[:needed]
    
    print(f"\n📝 Adding {len(words_to_add)} words to reach target")
    
    if len(words_to_add) == 0:
        print(f"⚠️  Could not find enough new words")
        return
    
    # Combine existing and new words
    all_words = sorted(list(existing_words) + words_to_add)
    
    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        for word in all_words:
            f.write(word + '\n')
    
    final_count = len(all_words)
    print(f"✅ Updated! Final count: {final_count} words")
    
    if final_count < TARGET_WORDS_PER_BUCKET:
        shortage = TARGET_WORDS_PER_BUCKET - final_count
        print(f"⚠️  Still {shortage} words short of target (API may not have enough unique words)")
    
    return final_count

def main():
    """
    Main function to fill all word lists.
    """
    print("=" * 60)
    print("WORD LIST FILLER - Datamuse API (Enhanced)")
    print("=" * 60)
    print(f"Target: {TARGET_WORDS_PER_BUCKET} words per bucket")
    print(f"API: https://api.datamuse.com/words")
    print(f"Features: Smart backfilling, duplicate detection")
    print("=" * 60)
    
    # Track results
    results = {}
    
    # Process word lists from 3 to 20 letters
    for word_length in range(3, 21):
        try:
            final_count = fill_word_list(word_length)
            results[word_length] = final_count if final_count else 0
        except Exception as e:
            print(f"❌ Error processing {word_length}-letter words: {e}")
            results[word_length] = 0
    
    print("\n" + "=" * 60)
    print("✅ COMPLETE!")
    print("=" * 60)
    
    # Summary
    print("\nFinal word counts:")
    total_words = 0
    buckets_at_target = 0
    
    for word_length in range(3, 21):
        file_path = Path(__file__).parent / 'game' / 'management' / 'commands' / f'{word_length}_letter_words.txt'
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                count = len([line for line in f if line.strip()])
            
            total_words += count
            
            if count >= TARGET_WORDS_PER_BUCKET:
                status = "✅"
                buckets_at_target += 1
            elif count >= TARGET_WORDS_PER_BUCKET * 0.75:
                status = "⚠️ "
            else:
                status = "❌"
            
            percentage = (count / TARGET_WORDS_PER_BUCKET) * 100
            print(f"  {status} {word_length:2d}-letter words: {count:4d} ({percentage:5.1f}%)")
    
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"Total words across all buckets: {total_words:,}")
    print(f"Buckets at {TARGET_WORDS_PER_BUCKET} target: {buckets_at_target}/18")
    print(f"Average words per bucket: {total_words / 18:.0f}")
    
    if buckets_at_target == 18:
        print(f"\n🎉 ALL BUCKETS FILLED TO TARGET! 🎉")
    elif buckets_at_target >= 15:
        print(f"\n🎊 Excellent! Most buckets filled!")
    elif buckets_at_target >= 10:
        print(f"\n👍 Good progress! Many buckets filled!")
    else:
        print(f"\n💪 Keep going! Some buckets need more words.")

if __name__ == '__main__':
    main()
