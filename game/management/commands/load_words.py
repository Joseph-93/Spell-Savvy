from django.core.management.base import BaseCommand
from game.models import Word
import os

class Command(BaseCommand):
    help = 'Populate the database with ~5000 common English words organized by difficulty'

    def handle(self, *args, **kwargs):
        # Common English words organized by length (difficulty)
        # This is a curated list of common words for 6th graders and up
        # Directory containing your *_letter_words.txt files
        # Get the directory where this command file is located
        WORDS_DIR = os.path.dirname(os.path.abspath(__file__))
        words_by_length = {}
        # Loop through expected lengths (or dynamically scan the directory)
        for length in range(3, 21):  # from 3 to 20 letters
            filename = f"{length}_letter_words.txt"
            filepath = os.path.join(WORDS_DIR, filename)

            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    # Split lines, strip whitespace, and ignore empties
                    words = [w.strip() for w in f.read().splitlines() if w.strip()]
                    words_by_length[length] = words
            else:
                # Optionally log or skip missing files
                print(f"Warning: {filename} not found.")
                words_by_length[length] = []
        
        created_count = 0
        updated_count = 0
        
        # First pass: collect all words and their intended buckets
        # Later files override earlier files for duplicate words
        word_to_bucket = {}
        for length, words in words_by_length.items():
            for word_text in words:
                word_text = word_text.strip().lower()
                if word_text:
                    word_to_bucket[word_text] = length
        
        # Second pass: create/update all words
        for word_text, bucket in word_to_bucket.items():
            word, created = Word.objects.update_or_create(
                text=word_text,
                defaults={
                    'difficulty_bucket': bucket,
                    'word_length': len(word_text)
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded {created_count} new words and updated {updated_count} existing words'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Total words in database: {Word.objects.count()}'
            )
        )
