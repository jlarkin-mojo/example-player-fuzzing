from rapidfuzz import process, fuzz
import time


def find_player_mentions_fuzzy(
    tweet_text, all_player_names, threshold=80, scorer=fuzz.token_set_ratio
):
    """
    Returns a list of possible player name matches from the tweet_text, using
    fuzzy matching against all_player_names. Matches with a score >= threshold
    are considered candidates.

    Args:
        tweet_text (str): The text to search for player mentions
        all_player_names (list): List of all player names to match against
        threshold (int): Minimum score (0-100) to consider a match
        scorer (callable): The scorer function to use for matching

    Returns:
        list: List of matched player names that meet the threshold
    """
    # process.extract(...) returns a list of tuples: (matched_string, score, index)
    matches = process.extract(
        query=tweet_text,
        choices=all_player_names,
        scorer=scorer,
        limit=10,  # Return top 10 matches for analysis
    )

    # Filter by threshold
    best_matches = [name for name, score, _ in matches if score >= threshold]
    return list(set(best_matches)), matches  # return both matches and filtered results


def run_test_cases(test_cases, all_players, threshold=80, scorer=fuzz.token_set_ratio):
    """
    Run a series of test cases and display the results.

    Args:
        test_cases (list): List of test case dictionaries
        all_players (list): List of all player names
        threshold (int): Score threshold for matching
        scorer (callable): Scoring function to use
    """
    print(f"\n{'='*80}")
    print(
        f"FUZZY MATCHING TEST RESULTS (Threshold: {threshold}, Scorer: {scorer.__name__})"
    )
    print(f"{'='*80}")

    results = []

    for i, test in enumerate(test_cases, 1):
        tweet = test["tweet"]
        expected = set(test.get("expected_matches", []))

        start_time = time.time()
        matches, all_match_data = find_player_mentions_fuzzy(
            tweet, all_players, threshold, scorer
        )
        elapsed = (time.time() - start_time) * 1000  # convert to ms

        # Determine if test passed
        actual_set = set(matches)
        passed = actual_set == expected

        results.append(
            {
                "id": i,
                "passed": passed,
                "tweet": tweet,
                "expected": expected,
                "actual": actual_set,
                "all_matches": all_match_data,
                "elapsed_ms": elapsed,
            }
        )

    # Display results
    total_passed = sum(1 for r in results if r["passed"])

    for i, result in enumerate(results, 1):
        print(f"\nTest Case #{i}: {'✓ PASSED' if result['passed'] else '✗ FAILED'}")
        print(f"Tweet: \"{result['tweet']}\"")

        print("\nAll potential matches (Name, Score, Index):")
        for name, score, idx in result["all_matches"]:
            match_status = ""
            if score >= threshold:
                if name in result["expected"]:
                    match_status = "✓ CORRECT MATCH"
                else:
                    match_status = "! FALSE POSITIVE"
            elif name in result["expected"]:
                match_status = "! FALSE NEGATIVE"

            print(f"  {name:<25} {score:>6.2f}  {idx:>3}  {match_status}")

        if not result["passed"]:
            print("\nExpected:", sorted(list(result["expected"])))
            print("Actual:  ", sorted(list(result["actual"])))

        print(f"Time: {result['elapsed_ms']:.2f}ms")
        print("-" * 80)

    print(
        f"\nSummary: {total_passed}/{len(results)} tests passed ({total_passed/len(results)*100:.1f}%)"
    )
    return results


if __name__ == "__main__":
    # Expanded list of players
    all_players = [
        "LeBron James",
        "Stephen Curry",
        "Kevin Durant",
        "Giannis Antetokounmpo",
        "James Harden",
        "Anthony Davis",
        "Nikola Jokić",
        "Luka Dončić",
        "Joel Embiid",
        "Jayson Tatum",
        "Damian Lillard",
        "Jimmy Butler",
        "Kawhi Leonard",
        "Kyrie Irving",
        "Devin Booker",
        "Paul George",
        "Ja Morant",
        "Zion Williamson",
        "Trae Young",
        "Donovan Mitchell",
        "Bam Adebayo",
        "Jaylen Brown",
        "Rudy Gobert",
        "Karl-Anthony Towns",
        "Draymond Green",
        "Russell Westbrook",
        "Chris Paul",
        "Klay Thompson",
        "Ben Simmons",
    ]

    # Test cases with expected matches
    test_cases = [
        {
            "tweet": "Lebron is questionable tonight with a sore ankle",
            "expected_matches": ["LeBron James"],
        },
        {
            "tweet": "King James dropped 35 points in the comeback win",
            "expected_matches": ["LeBron James"],
        },
        {
            "tweet": "Curry with another deep three! He's on fire tonight.",
            "expected_matches": ["Stephen Curry"],
        },
        {
            "tweet": "The Greek Freak is dominating in the paint again",
            "expected_matches": ["Giannis Antetokounmpo"],
        },
        {
            "tweet": "KD and Kyrie combined for 75 points in Brooklyn's win",
            "expected_matches": ["Kevin Durant", "Kyrie Irving"],
        },
        {
            "tweet": "Giannis antetokounpo is unstoppable this season",  # Misspelled name
            "expected_matches": ["Giannis Antetokounmpo"],
        },
        {
            "tweet": "Amazing performance by Jimmy Buckets last night!",
            "expected_matches": ["Jimmy Butler"],
        },
        {
            "tweet": "Can't believe Luka got another triple-double",
            "expected_matches": ["Luka Dončić"],
        },
        {
            "tweet": "The Beard doing what he does best. 40 points and 15 assists!",
            "expected_matches": ["James Harden"],
        },
        {
            "tweet": "Who is better - Embiid or Jokic?",
            "expected_matches": ["Joel Embiid", "Nikola Jokić"],
        },
        {
            "tweet": "Westbrook with another record-breaking performance",
            "expected_matches": ["Russell Westbrook"],
        },
        {
            "tweet": "Watching LBJ and AD dominate tonight",
            "expected_matches": ["LeBron James", "Anthony Davis"],
        },
        {
            "tweet": "Tatum and Brown combined for 65 in the Celtics win",
            "expected_matches": ["Jayson Tatum", "Jaylen Brown"],
        },
        {
            "tweet": "just watched a great game with no particular star players",
            "expected_matches": [],
        },
        {
            "tweet": "James playing tonight?",  # Ambiguous - could be LeBron James or James Harden
            "expected_matches": [],  # Setting to empty as it's ambiguous
        },
    ]

    # Run tests with different scorers and thresholds
    print("\n=== TESTING WITH DEFAULT SETTINGS ===")
    run_test_cases(test_cases, all_players, threshold=80, scorer=fuzz.token_set_ratio)

    print("\n=== TESTING WITH LOWER THRESHOLD ===")
    run_test_cases(test_cases, all_players, threshold=60, scorer=fuzz.token_set_ratio)

    print("\n=== TESTING WITH DIFFERENT SCORER ===")
    run_test_cases(test_cases, all_players, threshold=70, scorer=fuzz.token_sort_ratio)

    # Benchmarking different scorers
    print("\n=== BENCHMARKING DIFFERENT SCORERS ===")
    scorers = [
        fuzz.ratio,
        fuzz.partial_ratio,
        fuzz.token_sort_ratio,
        fuzz.token_set_ratio,
        fuzz.partial_token_sort_ratio,
        fuzz.partial_token_set_ratio,
        fuzz.WRatio,
    ]

    benchmark_tweet = "King James and the Greek Freak are both playing amazing this season. KD is back too!"
    expected = ["LeBron James", "Giannis Antetokounmpo", "Kevin Durant"]

    print(f'\nBenchmarking tweet: "{benchmark_tweet}"')
    print(f"Expected matches: {expected}")
    print(
        "\nScorer                   | Threshold | Matches                           | Time (ms)"
    )
    print("-" * 90)

    for scorer in scorers:
        for threshold in [50, 70, 90]:
            start_time = time.time()
            matches, _ = find_player_mentions_fuzzy(
                benchmark_tweet, all_players, threshold, scorer
            )
            elapsed = (time.time() - start_time) * 1000

            matches_str = str(matches)
            if len(matches_str) > 35:
                matches_str = matches_str[:32] + "..."

            print(
                f"{scorer.__name__:<25} | {threshold:>9} | {matches_str:<35} | {elapsed:>8.2f}"
            )
