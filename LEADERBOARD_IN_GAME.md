# Leaderboard in Game Play Interface

## Overview
The leaderboard widget is now available on both the dashboard AND during active gameplay! Students can see their competitive standing while playing.

## Feature Location

### 1. **Student Dashboard** (`/dashboard/`)
- Shows full leaderboard widget with rank card and top 5
- Positioned below session cards

### 2. **Game Play Page** (`/play/`) ✨ NEW!
- **Desktop/Tablet**: Leaderboard appears as a sticky sidebar on the right
- **Mobile**: Leaderboard appears below the game controls
- Stays visible while playing to maintain motivation

## Layout & Responsiveness

### Desktop View (≥1024px)
```
┌─────────────────────────────────┬──────────────┐
│  🎮 Spelling Challenge          │ 🏆 Leaderboard│
│                                 │              │
│  [Bucket] [Score] [Progress]... │  Your Rank   │
│                                 │   #2 of 15   │
│  ┌─────────────────────────┐   │              │
│  │ Word Display & Controls │   │  Score: 208  │
│  │                         │   │              │
│  │  [Speak] [Definition]   │   │  Gap: 15 pts │
│  │                         │   │              │
│  │  [Input Field]          │   │  Top 5:      │
│  │  [Submit]               │   │  🥇 Bob  223 │
│  └─────────────────────────┘   │  🥈 You  208 │
│                                 │  🥉 Carol 195│
│  [End Session]                  │  #4 Dave 180 │
│                                 │  #5 Eve  175 │
│                                 │              │
│                                 │ [View Full →]│
└─────────────────────────────────┴──────────────┘
```

### Mobile View (<1024px)
```
┌──────────────────────────┐
│ 🎮 Spelling Challenge    │
│                          │
│ [Bucket] [Score]         │
│ [Progress] [Total]       │
│                          │
│ ┌──────────────────────┐ │
│ │  Word Display        │ │
│ │  [Speak] [Def]       │ │
│ │  [Input]             │ │
│ │  [Submit]            │ │
│ └──────────────────────┘ │
│                          │
│ [End Session]            │
│                          │
│ ┌──────────────────────┐ │
│ │ 🏆 Leaderboard       │ │
│ │                      │ │
│ │  Your Rank: #2/15    │ │
│ │  Score: 208 pts      │ │
│ │  Gap: 15 pts behind  │ │
│ │                      │ │
│ │  Top 5:              │ │
│ │  🥇 Bob    223       │ │
│ │  🥈 You    208       │ │
│ │  🥉 Carol  195       │ │
│ │  #4 Dave   180       │ │
│ │  #5 Eve    175       │ │
│ │                      │ │
│ │ [View Full →]        │ │
│ └──────────────────────┘ │
└──────────────────────────┘
```

## Visual Design

### Rank Badge Colors
- **#1 (Gold)**: Gold gradient background with 🥇 medal
- **#2 (Silver)**: Silver gradient background with 🥈 medal
- **#3 (Bronze)**: Bronze gradient background with 🥉 medal
- **#4-5+**: Standard white background with rank number

### Sticky Behavior (Desktop)
The leaderboard sidebar uses `position: sticky; top: 1rem;` which means:
- Scrolls normally with the page initially
- Sticks to the top (1rem from viewport) when you scroll down
- Always visible during gameplay

### Compact Design
The sidebar widget is optimized for space:
- **Width**: 300px on desktop
- **Compact font sizes**: 0.85rem - 1.1rem
- **Tight spacing**: Minimal padding and gaps
- **Scrollable**: If content exceeds viewport height

## Features in Game Widget

### Your Rank Card
```
╔════════════════════╗
║     🥈 #2         ║
║    of 15          ║
║                   ║
║   208 pts         ║
║                   ║
║ 15 pts behind Bob ║
╚════════════════════╝
```

### Top 5 Mini List
```
Top 5 Students
─────────────────
🥇 Bob       223
🥈 You       208  (highlighted)
🥉 Carol     195
#4 Dave      180
#5 Eve       175
```

### Current Student Highlight
When you appear in the top 5:
- Yellow gradient background
- Gold border (2px)
- Bold text
- "(You)" label after name

## User Experience Benefits

### 🎮 **During Gameplay**
1. **Constant Motivation**: See your rank while playing
2. **Goal Reminder**: Gap to next person visible at all times
3. **Progress Context**: Understand how each word affects standing
4. **Competitive Drive**: "Just 15 more points to beat Bob!"

### 🏆 **Engagement Boost**
- Students stay motivated between words
- Can see rank changes in real-time
- Easier to set short-term goals
- Reduces need to check dashboard

### 📱 **Mobile Friendly**
- Doesn't clutter small screens
- Appears after game controls (logical flow)
- Full-width on mobile for readability
- Same information, optimized layout

## Technical Implementation

### View Changes (`game/views.py`)
```python
@login_required
def student_game(request):
    # ... existing code ...
    
    # Get leaderboard data for current student's classroom
    leaderboard_data = None
    if request.user.classroom:
        leaderboard_data = get_classroom_leaderboard(request.user.classroom, request.user)
    
    context = {
        'progress': progress,
        'session': active_session,
        'bucket_progress': bucket_progress,
        'config': config,
        'leaderboard_data': leaderboard_data,  # NEW
    }
    
    return render(request, 'game/student_game.html', context)
```

### Template Changes (`templates/game/student_game.html`)
1. **Layout Grid**: Changed from single column to responsive grid
   - 1 column on mobile
   - 2 columns (main + sidebar) on desktop (≥1024px)

2. **Leaderboard Sidebar**: New component after main game container
   - Conditional rendering: `{% if leaderboard_data %}`
   - Reuses same data structure as dashboard widget
   - Sticky positioning on desktop

3. **Styling**: Added 150+ lines of CSS for:
   - Sidebar layout and positioning
   - Rank badges with medal colors
   - Mini leaderboard items
   - Responsive behavior
   - Highlighting for current student

## Classroom Context

### When Leaderboard Shows
✅ Student is in a classroom (has `classroom` relationship)
✅ Classroom has 1+ other students with progress

### When Leaderboard is Hidden
❌ Student not assigned to classroom
❌ Student is the only one in classroom
❌ No other students have started playing

### Fallback Behavior
If no leaderboard data:
- Widget doesn't render
- No empty state message needed
- Game layout adjusts (single column on all screens)

## Performance Considerations

### Efficient Queries
- Same `get_classroom_leaderboard()` function used across views
- Filters only students in current classroom
- Calculates scores from existing `StudentProgress` data
- No additional database tables or migrations needed

### Caching Opportunities (Future)
- Could cache leaderboard data for X minutes
- Invalidate cache on game session completion
- Reduce database load for large classrooms

### Real-Time Updates (Current Behavior)
- Leaderboard shows snapshot at page load
- Updates when page is refreshed
- Changes reflect after completing game session
- No WebSocket/polling implemented (yet)

## Example Scenarios

### Scenario 1: Close Race
```
Student Alice is playing, currently #2

Sidebar shows:
┌─────────────────┐
│  🥈 #2 of 15   │
│   208 pts      │
│                │
│ 15 pts behind  │
│     Bob        │
└─────────────────┘

Alice thinks: "I need 16 points to take the lead!"
→ Gets word correct (+1 base + bucket bonus)
→ Finishes session and refreshes
→ Sees she's now #1 🥇
```

### Scenario 2: Leading by Large Margin
```
Student Bob is playing, currently #1 with big lead

Sidebar shows:
┌─────────────────┐
│   🥇 #1 of 15  │
│    223 pts     │
│                │
│ 👑 You're the  │
│    leader!     │
└─────────────────┘

Bob thinks: "Nice! I need to maintain this position."
→ Continues playing to keep lead
```

### Scenario 3: Outside Top 5
```
Student Sam is playing, currently #8

Sidebar shows:
┌─────────────────┐
│   #8 of 15     │
│   125 pts      │
│                │
│ 8 pts behind   │
│    Ava (#7)    │
└─────────────────┘

Top 5 shows students ranked 1-5
Sam sees goal: beat Ava to climb to #7
```

## Future Enhancements

### Real-Time Updates
- **WebSocket Integration**: Live rank changes without refresh
- **Animation**: Smooth transitions when rank changes
- **Notifications**: "You moved up to #3!" toast messages

### Enhanced Stats
- **Points per Word**: Show expected points for current word
- **Projection**: "Score 5 more words to reach #2"
- **Streak Indicator**: "3 correct in a row! +bonus"

### Customization
- **Collapse/Expand**: Toggle sidebar visibility
- **Minimal Mode**: Show only rank number
- **Focus Mode**: Hide until session ends

### Gamification
- **Level Up Animation**: Confetti when reaching top 3
- **Achievement Popups**: "First time in top 5!"
- **Challenge Notifications**: "Bob just scored! Can you catch up?"

## Summary

The leaderboard widget on the `/play/` page provides:

✅ **Always-Visible Competition**: See your standing during gameplay
✅ **Responsive Layout**: Desktop sidebar, mobile below-game
✅ **Compact Design**: Doesn't interfere with game controls
✅ **Real Motivation**: Gap to next person shown clearly
✅ **Visual Feedback**: Medal icons and color-coded rankings
✅ **Quick Access**: Link to full leaderboard page
✅ **Context Awareness**: Only shows when in classroom

Students now have competitive context at all times, making every word count toward climbing the leaderboard! 🎮🏆
