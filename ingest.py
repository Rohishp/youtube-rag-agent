# ingest.py
#
# Loads transcript data into the vector database.
#
# You have TWO ways to add knowledge:
#
# Option A — Use transcripts from your YouTube Research Agent output
#   python ingest.py --from-research ../youtube-research-agent/output/brief_*.json
#
# Option B — Add sample data to test immediately (no research agent needed)
#   python ingest.py --sample
#
# Run this before asking questions. The knowledge base must have content
# before the agent can retrieve anything.

import json
import os
import argparse
import glob
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def ingest_from_research_brief(brief_path: str) -> dict:
    """
    Extract transcript data from a research agent output file and index it.
    
    The research agent saves briefs as JSON with top_videos_analyzed.
    We use the video titles and descriptions as indexable knowledge.
    Note: The full transcripts aren't in the brief — only metadata and descriptions.
    For full transcript indexing, we'd need to re-fetch or save transcripts separately.
    We use descriptions + key themes as a proxy here.
    """
    from tools.indexer import index_transcript

    with open(brief_path, encoding="utf-8") as f:
        brief = json.load(f)

    niche = brief.get("niche", "unknown").lower().replace(" ", "_")
    indexed = 0

    # Index each video's description and the brief's content gaps as knowledge
    for video in brief.get("top_videos_analyzed", []):
        if not video.get("description"):
            continue

        # Build a richer text from the video data we have
        text = f"""
        Video: {video['title']}
        Channel: {video['channel_name']}
        Views: {video['view_count']:,}
        
        Description: {video['description']}
        
        Key themes from this niche: {', '.join(brief.get('key_themes', []))}
        """.strip()

        result = index_transcript(
            transcript=text,
            video_id=video["video_id"],
            title=video["title"],
            channel_name=video["channel_name"],
            niche=niche,
            view_count=video.get("view_count", 0),
            published_at=video.get("published_at", ""),
        )

        if result["status"] in ("indexed", "already_indexed"):
            indexed += 1

    # Also index the content gaps and video ideas as knowledge chunks
    gaps_text = "\n\n".join([
        f"Content gap: {gap['gap_title']}\n{gap['explanation']}\nDemand: {gap['estimated_demand']}"
        for gap in brief.get("content_gaps", [])
    ])

    if gaps_text:
        index_transcript(
            transcript=gaps_text,
            video_id=f"{niche}_gaps",
            title=f"Content Gaps Analysis: {brief['niche']}",
            channel_name="research_analysis",
            niche=niche,
            view_count=0,
            published_at="",
        )
        indexed += 1

    return {"brief": brief_path, "niche": niche, "items_indexed": indexed}


def ingest_sample_data():
    """
    Index sample transcript data so you can test the agent immediately.
    These are realistic transcript excerpts representing what real videos say.
    """
    from tools.indexer import index_transcript

    sample_transcripts = [
        {
            "video_id": "sample_morning_001",
            "title": "I Tested 7 Entrepreneur Morning Routines for 30 Days",
            "channel_name": "Deep Work Daily",
            "niche": "morning_routines",
            "view_count": 2800000,
            "published_at": "2024-03-15",
            "transcript": """
            What if everything you knew about morning routines was wrong? I spent 30 days 
            testing seven different routines used by successful entrepreneurs, and the results 
            completely surprised me.
            
            Most morning routine content tells you to wake up at 5am, meditate for 20 minutes, 
            exercise, journal, and eat a healthy breakfast. All before 7am. And while that sounds 
            great in theory, the data tells a different story.
            
            The entrepreneurs I studied who were most productive didn't follow a rigid schedule. 
            They followed a rigid SEQUENCE. The order of activities mattered far more than the 
            time they happened. The first 90 minutes were protected for one thing: their most 
            important cognitive work. Not email. Not meetings. Not planning. The work itself.
            
            I noticed that the highest performers all had one thing in common that nobody talks 
            about: they made zero decisions in the first hour of being awake. Clothes were chosen 
            the night before. Breakfast was the same every day. Coffee was automatic. Every ounce 
            of decision-making energy was preserved for the work.
            
            The second pattern was around exercise timing. Counterintuitively, the most productive 
            entrepreneurs did not exercise first thing. They worked for 90 minutes, then exercised. 
            Their reasoning: the first 90 minutes after waking is when cortisol is naturally 
            highest, giving a natural energy peak for cognitive work. Exercise was used to reset 
            and recharge for the afternoon, not to start the day.
            """
        },
        {
            "video_id": "sample_morning_002",
            "title": "Why Your Morning Routine is Failing You",
            "channel_name": "Rethink Productivity",
            "niche": "morning_routines",
            "view_count": 1500000,
            "published_at": "2024-07-22",
            "transcript": """
            Your morning routine isn't failing because you lack discipline. It's failing because 
            you designed it for someone else's life. 
            
            Every morning routine video you've watched was made by someone who works from home, 
            has no kids, and can structure their entire day around personal optimization. But 
            what about the entrepreneur who has a 7am school run? The founder whose first 
            meeting is at 8:30? The business owner who needs to be responsive to their team 
            before 9am?
            
            The five am club doesn't work for everyone. And the research backs this up. A 2023 
            study from the University of Toronto found that chronotype — your natural sleep-wake 
            preference — is largely genetic. About 40 percent of people are genuine morning types. 
            30 percent are genuine evening types. The rest fall somewhere in between.
            
            What actually works regardless of chronotype: anchor habits. Instead of building a 
            routine around a specific time, build it around a trigger. After coffee, I do 10 minutes 
            of planning. After the school run, I have 25 minutes of deep work. After lunch, I 
            review metrics. The trigger makes the habit location and time independent.
            
            The entrepreneurs I interviewed who had the most consistent productive mornings all 
            shared one design principle: they optimized for their actual life, not an imagined 
            ideal version of their life.
            """
        },
        {
            "video_id": "sample_stoic_001",
            "title": "Stoic Principles That Changed How I Run My Business",
            "channel_name": "Modern Philosopher",
            "niche": "stoic_philosophy",
            "view_count": 980000,
            "published_at": "2024-01-10",
            "transcript": """
            Two thousand years ago, a Roman emperor who ruled over sixty million people wrote 
            a private journal that he never intended anyone to read. That journal, Marcus Aurelius's 
            Meditations, is now one of the most widely read books in the world. And if you've 
            never read it, I want to tell you why it might be the most practically useful book 
            for running a business in 2024.
            
            The Stoics had one core idea that I come back to constantly as an entrepreneur: 
            the dichotomy of control. There are things within your control — your decisions, 
            your effort, your response to events. And there are things outside your control — 
            market conditions, competitors, other people's behavior, luck. 
            
            Most entrepreneurial stress comes from trying to control the uncontrollable. I spent 
            the first three years of my business anxious about what competitors were doing, what 
            the economy was doing, what customers might think. The Stoics would call this a 
            fundamental category error.
            
            The practical application I use every Monday morning: I write two lists. On the left: 
            everything I'm worried about this week. On the right: I mark each worry with C for 
            controllable or U for uncontrollable. Every U gets crossed off. Not ignored — crossed 
            off as something I will not spend emotional energy on. The exercise takes 8 minutes 
            and has more impact on my week than any other habit I've built.
            
            The second Stoic principle that transformed how I lead: amor fati, love of fate. 
            Not acceptance of bad outcomes — love of them. The Stoics believed that obstacles 
            don't block the path. They ARE the path. Every constraint, every setback, every 
            limitation is simultaneously the material you build with.
            """
        },
        {
            "video_id": "sample_stoic_002",
            "title": "3 Stoic Habits I Practice Every Single Day",
            "channel_name": "Philosophy For Life",
            "niche": "stoic_philosophy",
            "view_count": 720000,
            "published_at": "2024-05-30",
            "transcript": """
            I've been studying Stoic philosophy for eight years. Not as an academic exercise — 
            as a practical operating system for navigating a difficult decade that included 
            a failed startup, a divorce, and a health scare. These three habits are what I 
            actually practice, not what sounds good in a YouTube video.
            
            Habit one: the evening review. Every night before bed, I ask three questions. 
            What did I do well today? What could I have done better? What would a wiser 
            version of me have done differently? This comes directly from the Stoic practice 
            of evening reflection described by Seneca. The key is not to judge yourself harshly — 
            the Stoics were deeply opposed to self-flagellation. The goal is clear-eyed 
            observation without emotional charge.
            
            Habit two: voluntary discomfort. Once a week I deliberately do something uncomfortable. 
            Cold shower, skipping a meal, sitting with boredom without reaching for my phone. 
            Epictetus taught that we should practice being OK with less so that we can never 
            truly lose our wellbeing. The modern application: when you've voluntarily been 
            uncomfortable, you stop fearing circumstances that used to trigger anxiety.
            
            Habit three: the view from above. When I'm stressed about a decision or conflict, 
            I do a mental zoom-out. How significant is this in the context of my whole life? 
            In the context of a century? Marcus Aurelius regularly reminded himself that even 
            Alexander the Great and Julius Caesar are forgotten dust. Most things that feel 
            urgent are not important. This habit creates immediate perspective that no 
            meditation app has ever given me.
            """
        },
        {
            "video_id": "sample_investing_001",
            "title": "5 Investing Mistakes That Cost Me $40,000",
            "channel_name": "Honest Money Talk",
            "niche": "beginner_investing",
            "view_count": 3200000,
            "published_at": "2023-11-08",
            "transcript": """
            I'm going to tell you something most finance YouTubers won't: I've made catastrophically 
            bad investment decisions, and I'm going to walk you through exactly what happened and 
            why, because the lessons cost me $40,000 and they don't have to cost you anything.
            
            Mistake one: I confused a bull market with personal genius. Between 2020 and 2021, 
            everything I touched went up. I started to believe I was exceptional at picking stocks. 
            I wasn't. The entire market was going up. Every month I was taking bigger positions 
            in more speculative assets because my confidence was being continuously reinforced 
            by my account balance. This is called the confidence-competence gap, and it's the 
            most dangerous state a beginner investor can be in.
            
            Mistake two: I checked my portfolio every day. This sounds harmless but it's 
            financially destructive. Research shows that investors who check their portfolio 
            daily take 50 percent more trades than those who check monthly. More trades means 
            more fees, more tax events, and more emotional decisions. The act of watching causes 
            action. Action causes underperformance.
            
            Mistake three: I didn't understand what I owned. I bought funds because someone 
            on Reddit said they were good. I had no idea what companies were in them, what 
            their expense ratios were, how they were weighted, or what scenarios would cause 
            them to lose value. When the market dropped in 2022, I panicked and sold because 
            I didn't have a thesis. I just had hope. Hope is not an investment strategy.
            
            The most important thing I learned: the goal of investing in your twenties and 
            thirties is not to get rich. The goal is to not do anything stupid. Time is the 
            asset. Consistency is the strategy. Boredom is the feeling you should be chasing, 
            not excitement.
            """
        },
    ]

    from tools.indexer import index_transcript

    print("\nIndexing sample transcript data...")
    print("-" * 40)

    results = []
    for data in sample_transcripts:
        result = index_transcript(
            transcript=data["transcript"],
            video_id=data["video_id"],
            title=data["title"],
            channel_name=data["channel_name"],
            niche=data["niche"],
            view_count=data["view_count"],
            published_at=data["published_at"],
        )
        results.append(result)

    return results


def main():
    parser = argparse.ArgumentParser(description="Ingest transcript data into the knowledge base")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Index sample data to test the agent immediately"
    )
    parser.add_argument(
        "--from-research",
        type=str,
        nargs="+",
        help="Path(s) to research agent brief JSON files. Supports glob patterns."
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show current knowledge base stats"
    )
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set")
        return

    from tools.indexer import get_index_stats

    if args.stats:
        stats = get_index_stats()
        print(f"\nKnowledge Base Stats:")
        print(f"  Total chunks: {stats['total_chunks']}")
        print(f"  Total videos: {stats['total_videos']}")
        print(f"  Niches: {', '.join(stats['niches']) if stats['niches'] else 'none'}")
        return

    if args.sample:
        results = ingest_sample_data()
        print(f"\n✓ Sample data ingested: {len(results)} transcripts indexed")

    if args.from_research:
        # Expand glob patterns
        paths = []
        for pattern in args.from_research:
            expanded = glob.glob(pattern)
            paths.extend(expanded if expanded else [pattern])

        print(f"\nIngesting from {len(paths)} research brief(s)...")
        for path in paths:
            if not Path(path).exists():
                print(f"  ✗ File not found: {path}")
                continue
            result = ingest_from_research_brief(path)
            print(f"  ✓ {result['niche']}: {result['items_indexed']} items indexed")

    # Show final stats
    stats = get_index_stats()
    print(f"\nKnowledge Base Stats:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Total videos: {stats['total_videos']}")
    print(f"  Niches: {', '.join(stats['niches'])}")


if __name__ == "__main__":
    main()
