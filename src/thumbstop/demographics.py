"""Population priors for the crowd simulation.

These are editable assumptions loosely based on public platform demographics, NOT measured truth.
Fit them to your own audience with `thumbstop calibrate` and by editing this file / passing a
custom platform mix. Every table is plain data so contributors can improve it with a PR."""

KINDS = ("reel", "video", "carousel", "image", "audio", "text")
KIND_ALIASES = {"short": "reel", "shorts": "reel", "tiktok": "reel", "story": "image", "post": "text",
                "podcast": "audio", "photo": "image", "thread": "text", "article": "text"}

# Interest -> whole-word/phrase keywords used to detect what a piece of content is about.
INTERESTS = {
    "fitness": ["gym", "workout", "lift", "lifting", "protein", "reps", "cardio", "fat loss", "muscle", "training", "gains", "squat"],
    "health": ["sleep", "stress", "nutrition", "diet", "mental health", "wellness", "habit", "burnout", "supplement", "creatine"],
    "food": ["recipe", "cook", "cooking", "meal", "kitchen", "dinner", "bake", "snack", "restaurant", "breakfast"],
    "finance": ["money", "invest", "investing", "budget", "debt", "saving", "savings", "stock", "salary", "tax", "income", "crypto"],
    "business": ["startup", "founder", "marketing", "sales", "clients", "brand", "entrepreneur", "agency", "revenue", "creator"],
    "tech": ["ai", "app", "code", "coding", "software", "gadget", "phone", "automation", "prompt", "developer", "chatgpt"],
    "gaming": ["game", "gaming", "stream", "console", "esports", "fps", "minecraft", "gamer"],
    "music": ["song", "album", "beat", "guitar", "lyrics", "concert", "playlist", "producer", "singer"],
    "comedy": ["funny", "meme", "joke", "relatable", "pov", "skit", "lol"],
    "education": ["learn", "study", "exam", "lesson", "explained", "student", "course", "how to", "tutorial"],
    "fashion": ["outfit", "style", "fashion", "wear", "thrift", "sneakers", "wardrobe"],
    "beauty": ["skincare", "makeup", "hair", "glow", "serum", "nails"],
    "travel": ["travel", "trip", "visa", "hotel", "flight", "itinerary", "backpacking", "beach"],
    "parenting": ["kids", "toddler", "mom", "dad", "parenting", "baby"],
    "sports": ["football", "cricket", "nba", "match", "league", "goal", "coach", "tournament"],
    "art": ["design", "art", "draw", "illustration", "photography", "aesthetic", "creative", "edit"],
    "news": ["news", "election", "policy", "government", "breaking", "war", "economy"],
    "pets": ["dog", "cat", "puppy", "kitten", "pet", "vet"],
    "cars": ["car", "engine", "drive", "ev", "motorcycle", "tesla"],
    "diy": ["diy", "build", "repair", "decor", "garden", "craft", "woodwork"],
}

# Persona-pack niche -> interests it implies.
NICHE_TOPICS = {"fitness": ["fitness", "health"], "finance": ["finance", "business"],
                "food": ["food"], "tech": ["tech", "business"]}

# Age groups. attn: attention multiplier. mults: propensity multipliers per action.
# fmt: affinity for each content kind (1 = loves it). boost: interest prior multipliers.
AGES = {
    "13-17": dict(attn=0.80, like=1.3, comment=1.2, share=1.2, save=0.7, follow=1.0,
                  fmt=dict(reel=1.0, video=0.9, carousel=0.6, image=0.7, audio=0.5, text=0.35),
                  boost=dict(gaming=4, music=3, comedy=3, beauty=2, fashion=2, sports=2, art=1.5, education=1.5)),
    "18-24": dict(attn=0.90, like=1.2, comment=1.1, share=1.3, save=1.0, follow=1.1,
                  fmt=dict(reel=1.0, video=0.9, carousel=0.8, image=0.8, audio=0.6, text=0.45),
                  boost=dict(gaming=2, music=2.5, comedy=2.5, fashion=2.5, beauty=2, fitness=2, tech=1.5, education=2, travel=2)),
    "25-34": dict(attn=1.00, like=1.0, comment=0.9, share=1.1, save=1.3, follow=1.0,
                  fmt=dict(reel=0.95, video=0.9, carousel=0.95, image=0.8, audio=0.8, text=0.6),
                  boost=dict(fitness=2, finance=2.5, tech=2, business=2.5, food=1.5, travel=2, health=1.5, education=1.5)),
    "35-44": dict(attn=1.10, like=0.9, comment=0.9, share=0.9, save=1.4, follow=0.9,
                  fmt=dict(reel=0.8, video=0.9, carousel=0.9, image=0.85, audio=0.9, text=0.8),
                  boost=dict(parenting=3, finance=2.5, health=2, food=2, business=2, diy=2, news=1.5, cars=1.5)),
    "45-54": dict(attn=1.15, like=0.9, comment=0.8, share=0.8, save=1.2, follow=0.8,
                  fmt=dict(reel=0.65, video=0.9, carousel=0.8, image=0.9, audio=0.9, text=0.9),
                  boost=dict(news=3, health=2.5, finance=2, diy=2.5, cars=2, food=2, travel=1.5, parenting=1.5)),
    "55+": dict(attn=1.20, like=0.8, comment=0.9, share=0.9, save=0.9, follow=0.7,
                fmt=dict(reel=0.5, video=0.85, carousel=0.7, image=0.95, audio=0.9, text=1.0),
                boost=dict(news=3.5, health=3, food=2, travel=2, diy=2, pets=2, cars=1.5)),
}

# Platform -> age mix (shares sum to ~1), format affinity multipliers, interest bias, benchmark rate scale.
PLATFORMS = {
    "instagram": dict(ages={"13-17": .08, "18-24": .30, "25-34": .31, "35-44": .16, "45-54": .08, "55+": .07},
                      fmt=dict(reel=1.0, video=0.8, carousel=0.95, image=0.85, audio=0.45, text=0.4), bias={}),
    "tiktok": dict(ages={"13-17": .16, "18-24": .36, "25-34": .27, "35-44": .12, "45-54": .06, "55+": .03},
                   fmt=dict(reel=1.1, video=1.0, carousel=0.6, image=0.45, audio=0.4, text=0.2), bias={"comedy": 1.5, "music": 1.4}),
    "youtube": dict(ages={"13-17": .10, "18-24": .22, "25-34": .26, "35-44": .18, "45-54": .13, "55+": .11},
                    fmt=dict(reel=0.9, video=1.1, carousel=0.2, image=0.3, audio=0.7, text=0.3), bias={"education": 1.5, "gaming": 1.4}),
    "linkedin": dict(ages={"13-17": .00, "18-24": .14, "25-34": .38, "35-44": .27, "45-54": .15, "55+": .06},
                     fmt=dict(reel=0.6, video=0.7, carousel=1.0, image=0.6, audio=0.3, text=1.0),
                     bias={"business": 4, "tech": 2, "finance": 2.5, "education": 2, "gaming": .2, "comedy": .4}),
    "x": dict(ages={"13-17": .05, "18-24": .28, "25-34": .34, "35-44": .18, "45-54": .10, "55+": .05},
              fmt=dict(reel=0.6, video=0.7, carousel=0.4, image=0.8, audio=0.3, text=1.0),
              bias={"news": 3, "tech": 2, "sports": 2, "finance": 1.5, "comedy": 1.5}),
}

# User types: share of the population, impatience threshold (higher = skips more), action multipliers.
USER_TYPES = {
    "scroller": dict(share=.38, thr=.58, like=.6, comment=.3, share_=.5, save=.4, follow=.4, attn=.7),
    "casual":   dict(share=.24, thr=.50, like=1.0, comment=1.0, share_=1.0, save=1.0, follow=1.0, attn=1.0),
    "lurker":   dict(share=.16, thr=.46, like=.4, comment=.1, share_=.3, save=1.3, follow=.8, attn=1.2),
    "engager":  dict(share=.09, thr=.44, like=2.2, comment=3.0, share_=1.2, save=1.0, follow=1.5, attn=1.1),
    "sharer":   dict(share=.06, thr=.46, like=1.2, comment=1.0, share_=4.0, save=1.0, follow=1.0, attn=1.0),
    "saver":    dict(share=.05, thr=.46, like=.8, comment=.5, share_=.8, save=4.0, follow=1.0, attn=1.3),
    "superfan": dict(share=.02, thr=.35, like=2.5, comment=2.5, share_=2.0, save=2.0, follow=1.0, attn=1.6),
}

# Words that signal emotion/controversy/curiosity (drive shares and comments).
EMOTION = ["love", "hate", "shocking", "crazy", "insane", "scary", "worst", "best", "regret", "unbelievable",
           "finally", "truth", "never", "stop", "wrong", "secret", "mistake", "obsessed", "nobody", "everyone"]
CTA = ["follow", "comment", "share", "save", "send this", "dm me", "link in bio", "subscribe", "tag a", "tell me"]
LINK_CTA = ["link in bio", "dm me", "dm \"", "comment \""]
