from rapidfuzz import process, fuzz

def find_player_mentions_fuzzy(tweet_text, all_player_names, threshold=80):
    """
    Returns a list of possible player name matches from the tweet_text, using
    fuzzy matching against all_player_names. Matches with a score >= threshold
    are considered candidates.
    """
    # process.extract(...) returns a list of tuples: (matched_string, score, index)
    matches = process.extract(
        query=tweet_text,
        choices=all_player_names,
        scorer=fuzz.token_set_ratio
    )
    
    print('matches', matches)
    # Filter by threshold
    best_matches = [name for name, score, _ in matches if score >= threshold]
    return list(set(best_matches))  # remove duplicates if any

if __name__ == "__main__":
    # Example usage
    all_players = [
        "LeBron James",
        "Stephen Curry",
        "Kevin Durant",
        "Giannis Antetokounmpo",
        "James Harden"
    ]
    
    tweet = "Lebron is questionable tonight with a sore ankle"
    candidates = find_player_mentions_fuzzy(tweet, all_players)
    print("Fuzzy Matching Candidates:", candidates)
