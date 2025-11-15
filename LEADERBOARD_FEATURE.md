# Classroom Leaderboard Feature

## Overview
Students can now compete with their classmates on a leaderboard that shows rankings, scores, and how close they are to advancing!

## What's New

### For Students

#### 1. **Leaderboard Widget on Dashboard**
When you log in, you'll see:
- **Your Rank**: Where you stand in your classroom (e.g., #3 of 25)
- **Your Score**: Your total points
- **Gap to Next**: How many points behind the next person you are
- **Top 5 Preview**: Quick view of the top performers

#### 2. **Full Leaderboard Page**
Click "View Full Leaderboard" to see:
- Complete top 5 rankings with medal icons (🥇🥈🥉)
- Your highlighted position
- Detailed stats for each student
- How the scoring system works

#### 3. **Competitive Elements**
- See who's #1 in your class
- Track your progress against classmates
- Get motivated to climb the ranks
- Celebrate when you reach the top!

## Scoring System

Your score is calculated based on three factors:

### 1. **Base Points** (Word length = points earned)
```
Sum of all correct word lengths
```
Example: 
- "cat" (3 letters) = 3 points
- "elephant" (8 letters) = 8 points  
- "extraordinary" (13 letters) = 13 points
- Total for these 3 words = 24 points

### 2. **Bucket Bonus** (Current bucket × 10)
```
Current Bucket × 10 points
```
Example: Bucket 5 = 50 bonus points

### 3. **Accuracy Bonus** (Accuracy % ÷ 10)
```
(Accuracy Percentage) ÷ 10 points
```
Example: 85% accuracy = 8.5 ≈ 8 bonus points

### **Total Score Formula**
```
Score = Base Points + Bucket Bonus + Accuracy Bonus
```

### **Example Calculation**
```
Student: Alice
- Words Correct: 50 words
- Total Points from Words: 350 (average ~7 letters per word)
- Current Bucket: 5
- Accuracy: 85%

Base Points:    350
Bucket Bonus:   5 × 10   = 50
Accuracy Bonus: 85 ÷ 10  = 8

Total Score: 350 + 50 + 8 = 408 points
```

### **Why Word Length = Points?**
This rewards students for tackling harder, longer words:
- 3-letter words = 3 points each
- 5-letter words = 5 points each
- 10-letter words = 10 points each
- 20-letter words = 20 points each

Students in higher buckets naturally earn more points per word!

## UI Components

### Dashboard Widget

```
╔════════════════════════════════════════╗
║ 🏆 Classroom Leaderboard              ║
║                                        ║
║ ┌────────────────────────────────────┐ ║
║ │ 🥈  Your Rank                      │ ║
║ │     #2 of 15                       │ ║
║ │                                    │ ║
║ │ Your Score: 208                    │ ║
║ │                                    │ ║
║ │ Gap to #1: 15 pts behind Bob       │ ║
║ └────────────────────────────────────┘ ║
║                                        ║
║ Top 5 Students                         ║
║ 🥇 Bob        223 pts                  ║
║ 🥈 You        208 pts                  ║
║ 🥉 Carol      195 pts                  ║
║ #4 Dave       180 pts                  ║
║ #5 Eve        175 pts                  ║
║                                        ║
║        [View Full Leaderboard →]       ║
╚════════════════════════════════════════╝
```

### Full Leaderboard Page

```
Your Stats
─────────────────────────────────────────
📊 Your Stats
Rank: #2/15  |  Score: 208  |  Accuracy: 85%
Gap to Next: 15 points behind Bob

🌟 Top Students
─────────────────────────────────────────
🥇 Bob               Period 1 • Bucket 6 • 220 correct • 90% accuracy
   Score: 223 points

🥈 You (Alice)       Period 1 • Bucket 5 • 150 correct • 85% accuracy
   Score: 208 points

🥉 Carol             Period 1 • Bucket 5 • 145 correct • 80% accuracy
   Score: 195 points

#4 Dave              Period 1 • Bucket 4 • 130 correct • 85% accuracy
   Score: 180 points

#5 Eve               Period 1 • Bucket 4 • 125 correct • 75% accuracy
   Score: 175 points
```

## Features

### 🏅 **Visual Ranking**
- **#1**: Gold medal 🥇 with gold gradient background
- **#2**: Silver medal 🥈 with silver gradient background
- **#3**: Bronze medal 🥉 with bronze gradient background
- **#4-5**: Rank number with standard background
- **Your Position**: Yellow highlight wherever you are

### 📊 **Motivation System**
- **Leading**: Shows "You're the leader!" with crown 👑
- **Chasing**: Shows exact points gap to next person
- **Climbing**: See progress as you move up ranks

### 🎯 **Transparency**
- **Scoring Info**: Clear explanation of how points are calculated
- **Real Stats**: See actual performance metrics
- **Fair System**: Rewards both progress (bucket) and accuracy

## User Flows

### Scenario 1: Student in Middle of Pack
```
Dashboard shows:
- Your Rank: #8 of 20
- Your Score: 145
- Gap to #7: 12 points behind Sarah

Student thinks: "I just need 12 more points to beat Sarah!"
→ Plays more games to close the gap
```

### Scenario 2: Student Near Top
```
Dashboard shows:
- Your Rank: #2 of 20
- Your Score: 210
- Gap to #1: 5 points behind Tom

Student thinks: "So close to #1! Just 5 more points!"
→ Extra motivated to overtake leader
```

### Scenario 3: Student is Leader
```
Dashboard shows:
- Your Rank: #1 of 20
- Your Score: 225
- 👑 You're the leader!

Student thinks: "I'm #1! Need to stay here!"
→ Motivated to maintain position
```

## Privacy & Display

### What's Shown:
✅ Username
✅ Score
✅ Rank
✅ Current bucket
✅ Words correct
✅ Accuracy percentage

### What's Hidden:
❌ Full name (unless set)
❌ Email
❌ Specific wrong words
❌ Other classrooms

### Scope:
- Only shows students in YOUR classroom
- Teacher can have multiple classrooms with separate leaderboards
- No cross-classroom comparison

## Technical Implementation

### Score Calculation
```python
@property
def score(self):
    base_score = self.total_words_correct
    bucket_bonus = self.current_bucket * 10
    
    if self.total_attempts > 0:
        accuracy = (self.total_words_correct / self.total_attempts) * 100
        accuracy_bonus = int(accuracy / 10)
    else:
        accuracy_bonus = 0
    
    return base_score + bucket_bonus + accuracy_bonus
```

### Leaderboard Logic
```python
def get_classroom_leaderboard(classroom, current_student):
    # Get all students in classroom
    # Calculate scores for each
    # Sort by score (descending)
    # Find current student's rank
    # Calculate gap to next person
    # Return top 5 + current student data
```

### Database Queries
- Efficient: Only queries students in current classroom
- Cached: Score calculated from existing progress data
- No new tables: Uses StudentProgress model

## Benefits

### For Students
✅ **Motivation**: See progress compared to peers
✅ **Goals**: Clear target (beat next person)
✅ **Recognition**: Medals for top 3
✅ **Engagement**: Adds competitive element
✅ **Transparency**: Know exactly where they stand

### For Teachers
✅ **Engagement**: Students play more to climb ranks
✅ **Healthy Competition**: Fosters classroom community
✅ **No Extra Work**: Automatic calculation
✅ **Privacy Safe**: Only classroom-level visibility
✅ **Fair System**: Rewards both quantity and quality

### For Learning
✅ **Practice Incentive**: More games = higher score
✅ **Accuracy Matters**: Bonus for getting words right
✅ **Progress Rewarded**: Bucket bonus for advancement
✅ **Balanced**: Can't just spam easy words

## Gamification Elements

### 🎮 **Game Mechanics**
- **Points System**: Clear scoring rules
- **Rankings**: Competitive ladder
- **Progress Tracking**: See improvement over time
- **Achievements**: Medal icons for top 3

### 🏆 **Competitive Features**
- **Leaderboard**: Public rankings
- **Gap Display**: Know how close you are
- **Personal Best**: Track your own score
- **Class Champion**: Special badge for #1

### 📈 **Progression**
- **Score Increases**: As you practice more
- **Rank Changes**: Dynamic based on performance
- **Bucket Advancement**: Unlocks higher bonuses
- **Accuracy Improvement**: Adds bonus points

## Example Scenarios

### Elementary School
```
Mrs. Johnson's 3rd Grade Class (15 students)

Top 5:
🥇 Emma - 180 pts
🥈 Liam - 165 pts  
🥉 Sophia - 152 pts
#4 Noah - 140 pts
#5 Olivia - 135 pts

Your Rank: #7 (You: 125 pts)
Gap to #6: 8 points behind Ava

Motivation: "I can beat Ava if I play 8 more words!"
```

### High School
```
Ms. Smith's Period 2 English (28 students)

Top 5:
🥇 Alex - 425 pts (Bucket 8, 98% accuracy)
🥈 Jordan - 410 pts (Bucket 7, 95% accuracy)
🥉 Taylor - 395 pts (Bucket 7, 92% accuracy)
#4 Casey - 380 pts (Bucket 6, 90% accuracy)
#5 Riley - 365 pts (Bucket 6, 88% accuracy)

Your Rank: #12 (You: 285 pts)
Gap to #11: 15 points behind Sam

Motivation: "Need to improve accuracy to climb faster"
```

## Tips for Students

### 🎯 **How to Climb the Leaderboard**

1. **Play Consistently**
   - Each word = 1 point
   - More games = more points

2. **Improve Accuracy**
   - Higher accuracy = bonus points
   - 90%+ accuracy = 9 bonus points!

3. **Advance Buckets**
   - Each bucket = 10 bonus points
   - Bucket 10 = 100 bonus points!

4. **Strategic Play**
   - Focus on accuracy over speed
   - Master current bucket before advancing
   - Consistent practice beats cramming

### 📊 **Understanding Your Position**

**If you're #1:**
- Keep practicing to maintain lead
- Help classmates improve too
- Set a high score goal

**If you're in top 5:**
- Close to the top!
- See exact gap to climb
- Focus on bonus points

**If you're outside top 5:**
- Room to improve
- Every game helps you climb
- Focus on accuracy bonus

## Frequently Asked Questions

**Q: How often does the leaderboard update?**
A: Real-time! Every time you complete a game, your score updates immediately.

**Q: Can other classes see my rank?**
A: No, leaderboards are classroom-specific. Only your classmates see your rank.

**Q: What if I'm last place?**
A: Everyone starts somewhere! The leaderboard shows there's always room to improve. Plus, you can see exactly how many points you need to advance.

**Q: Do teachers see the leaderboard?**
A: Teachers see student stats but from a different view focused on academic progress.

**Q: Can I see the full leaderboard beyond top 5?**
A: Currently shows top 5 + your position. This keeps focus on top performers and your personal goal.

**Q: What if there's a tie in scores?**
A: Students with same score share the same rank.

**Q: Does deleting my progress reset my score?**
A: Your score is based on your StudentProgress, so yes. But teachers typically don't delete progress!

## Future Enhancements (Potential)

- **Weekly/Monthly Leaderboards**: Reset period-based rankings
- **Achievements**: Badges for milestones
- **Personal Records**: Track your all-time high
- **Class Average**: Compare to class performance
- **Progress Charts**: Visualize rank changes over time
- **Custom Scoring**: Teachers adjust point values
- **Team Mode**: Collaborative scoring
- **Seasonal Champions**: Hall of fame

## Summary

The leaderboard adds a fun, competitive element to the spelling game while maintaining educational value. Students can:

✅ See where they rank
✅ Know their score
✅ Track gap to next person
✅ Get motivated by medals
✅ Compete with classmates
✅ Stay engaged with learning

All while the scoring system rewards both **quantity** (words practiced) and **quality** (accuracy), ensuring balanced progression!
