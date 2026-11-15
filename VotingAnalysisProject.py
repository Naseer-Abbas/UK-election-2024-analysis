"""UK General Election 2024 analysis tool.

Loads constituency-level results from ge2024_results.csv and lets you explore
them from a text menu: list seats and MPs, view party totals and vote shares,
filter and search, compare parties and draw charts.
"""

import csv
import sys
from pathlib import Path

DATA_FILE = Path(__file__).resolve().with_name("ge2024_results.csv")
STATS_FILE = Path(__file__).resolve().with_name("statistics.txt")

# Parties that have their own vote column in the dataset.
PARTY_COLUMNS = ["Con", "Lab", "LD", "RUK", "Green", "SNP", "PC",
                 "DUP", "SF", "SDLP", "UUP", "APNI"]
OTHER_COLUMN = "All other candidates"
OTHER_WINNER_COLUMN = "Of which other winner"


class MP:
    """The winning candidate in a constituency."""

    def __init__(self, name, party, gender, votes, constituency):
        self.name = name
        self.party = party
        self.gender = gender
        self.votes = votes
        self.constituency = constituency


class Constituency:
    def __init__(self, name, region, country, constituency_type,
                 electorate, valid_votes, invalid_votes, majority, results):
        self.name = name
        self.region = region
        self.country = country
        self.constituency_type = constituency_type
        self.electorate = electorate
        self.valid_votes = valid_votes
        self.invalid_votes = invalid_votes
        self.majority = majority
        self.results = results  # {party or "Other": votes}, parties with votes only
        self.mp = None

    @property
    def turnout(self):
        total = self.valid_votes + self.invalid_votes
        return percentage(total, self.electorate)

    def vote_share(self, votes):
        """Share of valid votes, the standard way vote share is reported."""
        return percentage(votes, self.valid_votes)


class Party:
    def __init__(self, name):
        self.name = name
        self.seats = 0
        # None means the dataset has no national vote column for this party
        # (independents, the Speaker and TUV are grouped under "other").
        self.total_votes = 0 if name in PARTY_COLUMNS else None

    def vote_share(self, national_valid_votes):
        if self.total_votes is None:
            return None
        return percentage(self.total_votes, national_valid_votes)


def percentage(part, whole):
    return (part / whole) * 100 if whole else 0.0


def load_data(filename):
    """Return (constituencies, parties). Bad rows are skipped with a warning."""
    constituencies = []
    parties = {name: Party(name) for name in PARTY_COLUMNS}

    with open(filename, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for line_number, row in enumerate(reader, start=2):
            try:
                results = {}
                for party in PARTY_COLUMNS:
                    votes = int(row[party])
                    parties[party].total_votes += votes
                    if votes > 0:
                        results[party] = votes
                other_votes = int(row[OTHER_COLUMN])
                if other_votes > 0:
                    results["Other"] = other_votes

                constituency = Constituency(
                    name=row["Constituency name"],
                    region=row["Region name"],
                    country=row["Country name"],
                    constituency_type=row["Constituency type"],
                    electorate=int(row["Electorate"]),
                    valid_votes=int(row["Valid votes"]),
                    invalid_votes=int(row["Invalid votes"]),
                    majority=int(row["Majority"]),
                    results=results,
                )

                winner_party = row["First party"]
                if winner_party in PARTY_COLUMNS:
                    winner_votes = int(row[winner_party])
                else:
                    winner_votes = int(row[OTHER_WINNER_COLUMN])
                constituency.mp = MP(
                    name=f"{row['Member first name']} {row['Member surname']}",
                    party=winner_party,
                    gender=row["Member gender"],
                    votes=winner_votes,
                    constituency=constituency.name,
                )

                parties.setdefault(winner_party, Party(winner_party)).seats += 1
                constituencies.append(constituency)
            except (KeyError, ValueError) as error:
                print(f"Warning: skipped line {line_number} ({error}).")

    return constituencies, parties


# Helpers

def get_valid_input(prompt, min_value, max_value):
    while True:
        try:
            choice = int(input(prompt))
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue
        if min_value <= choice <= max_value:
            return choice
        print(f"Please enter a number between {min_value} and {max_value}.")


def national_valid_votes(constituencies):
    return sum(c.valid_votes for c in constituencies)


def sorted_parties(parties):
    """Parties ordered by seats, then by votes."""
    return sorted(parties.values(),
                  key=lambda p: (p.seats, p.total_votes or 0), reverse=True)


def format_votes(votes):
    return "not available" if votes is None else f"{votes:,}"


def format_share(share):
    return "n/a" if share is None else f"{share:.1f}%"


def find_party(parties, name):
    """Case-insensitive party lookup. Returns the Party or None."""
    lookup = {key.lower(): party for key, party in parties.items()}
    return lookup.get(name.strip().lower())


def print_constituency_results(c):
    print(f"\n{c.name} ({c.region}, {c.country}) - {c.constituency_type}")
    print(f"  Electorate: {c.electorate:,} | Valid votes: {c.valid_votes:,} | "
          f"Turnout: {c.turnout:.1f}% | Majority: {c.majority:,}")
    print(f"  Winner: {c.mp.name} ({c.mp.party})")
    for party, votes in sorted(c.results.items(), key=lambda item: item[1], reverse=True):
        print(f"    {party:<6} {votes:>7,}  {c.vote_share(votes):5.1f}%")


# Menu actions

def list_constituencies(constituencies):
    for c in constituencies:
        print(f"{c.name} | {c.region}, {c.country} | {c.constituency_type}")
    print(f"\n{len(constituencies)} constituencies.")


def list_mps(constituencies):
    for c in constituencies:
        mp = c.mp
        print(f"{mp.name} | {mp.party} | {mp.constituency} | "
              f"{mp.votes:,} votes ({c.vote_share(mp.votes):.1f}%) | {mp.gender}")


def list_party_statistics(constituencies, parties):
    total = national_valid_votes(constituencies)
    print(f"\n{'Party':<7}{'Seats':>6}{'Votes':>16}{'Share':>8}")
    for party in sorted_parties(parties):
        print(f"{party.name:<7}{party.seats:>6}{format_votes(party.total_votes):>16}"
              f"{format_share(party.vote_share(total)):>8}")
    print(f"\nTotal valid votes: {total:,}")
    print("Independents, the Speaker and TUV have no national vote column in the "
          "dataset, so only their seats are counted.")


def save_statistics(constituencies, parties, filename=STATS_FILE):
    total = national_valid_votes(constituencies)
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("Party,Seats,Votes,Vote share (%)\n")
            for party in sorted_parties(parties):
                share = party.vote_share(total)
                votes = "" if party.total_votes is None else party.total_votes
                share_text = "" if share is None else f"{share:.2f}"
                f.write(f"{party.name},{party.seats},{votes},{share_text}\n")
        print(f"Statistics saved to {filename}.")
    except OSError as error:
        print(f"Error saving statistics: {error}")


def plot_statistics(constituencies, parties):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib is not installed. Run: pip install -r requirements.txt")
        return

    print("\nChoose a chart:")
    print("1. Seats won by party (bar)")
    print("2. Total votes by party (bar)")
    print("3. Vote share by party (pie)")
    choice = get_valid_input("Enter your choice: ", 1, 3)

    if choice == 1:
        ranked = [p for p in sorted_parties(parties) if p.seats > 0]
        plt.bar([p.name for p in ranked], [p.seats for p in ranked])
        plt.ylabel("Seats")
        plt.title("Seats won by party, GE 2024")
    else:
        ranked = sorted((p for p in parties.values() if p.total_votes),
                        key=lambda p: p.total_votes, reverse=True)
        if choice == 2:
            plt.bar([p.name for p in ranked], [p.total_votes for p in ranked])
            plt.ylabel("Votes")
            plt.title("Total votes by party, GE 2024")
        else:
            # Group parties under 2% into "Other" so the pie stays readable.
            total = national_valid_votes(constituencies)
            labels, values, other = [], [], total
            for p in ranked:
                if p.vote_share(total) >= 2:
                    labels.append(p.name)
                    values.append(p.total_votes)
                    other -= p.total_votes
            labels.append("Other")
            values.append(other)
            plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
            plt.axis("equal")
            plt.title("Vote share, GE 2024")

    if choice != 3:
        plt.xticks(rotation=45)
        plt.tight_layout()
    plt.show()


def filter_constituencies(constituencies):
    print("\nFilter constituencies by:")
    print("1. Region")
    print("2. Country")
    print("3. Constituency type")
    choice = get_valid_input("Choose filter option: ", 1, 3)
    field = {1: "region", 2: "country", 3: "constituency_type"}[choice]

    options = sorted({getattr(c, field) for c in constituencies})
    print("Available: " + ", ".join(options))
    value = input("Enter value to filter by: ").strip().lower()

    filtered = [c for c in constituencies if getattr(c, field).lower() == value]
    for c in filtered:
        print(f"{c.name} | {c.region}, {c.country} | {c.constituency_type} | "
              f"won by {c.mp.party}")
    print(f"\n{len(filtered)} constituencies found." if filtered
          else "No constituencies found matching your criteria.")


def compare_parties(constituencies, parties):
    ranked = sorted_parties(parties)
    print("\nCompare two parties:")
    for i, party in enumerate(ranked, start=1):
        print(f"{i}. {party.name}")
    first = ranked[get_valid_input("Choose the first party: ", 1, len(ranked)) - 1]
    second = ranked[get_valid_input("Choose the second party: ", 1, len(ranked)) - 1]
    if first is second:
        print("Please choose two different parties.")
        return

    total = national_valid_votes(constituencies)
    for party in (first, second):
        print(f"{party.name}: {party.seats} seats, "
              f"{format_votes(party.total_votes)} votes "
              f"({format_share(party.vote_share(total))})")

    if first.seats != second.seats:
        leader = first if first.seats > second.seats else second
        print(f"{leader.name} won more seats.")
    else:
        print("Both parties won the same number of seats.")

    if first.total_votes is not None and second.total_votes is not None:
        if first.total_votes != second.total_votes:
            leader = first if first.total_votes > second.total_votes else second
            print(f"{leader.name} won more votes.")
        else:
            print("Both parties won the same number of votes.")


def search_mp(constituencies):
    query = input("\nEnter all or part of an MP's name: ").strip().lower()
    matches = [c for c in constituencies if query and query in c.mp.name.lower()]
    for c in matches:
        mp = c.mp
        print(f"{mp.name} | {mp.party} | {mp.constituency} | "
              f"{mp.votes:,} votes ({c.vote_share(mp.votes):.1f}%)")
    if not matches:
        print("No MP found with that name.")


def search_constituency(constituencies):
    query = input("\nEnter all or part of a constituency name: ").strip().lower()
    matches = [c for c in constituencies if query and query in c.name.lower()]
    for c in matches:
        print_constituency_results(c)
    if not matches:
        print("No constituency found with that name.")


def search_party(constituencies, parties):
    party = find_party(parties, input("\nEnter a party (e.g. Lab, Con, SNP): "))
    if party is None:
        print("Party not found. Available: " + ", ".join(sorted(parties)))
        return
    total = national_valid_votes(constituencies)
    stood_in = sum(1 for c in constituencies if party.name in c.results)
    print(f"\n{party.name}: {party.seats} seats | "
          f"votes: {format_votes(party.total_votes)} | "
          f"vote share: {format_share(party.vote_share(total))}")
    if party.total_votes is not None:
        print(f"Received votes in {stood_in} of {len(constituencies)} constituencies.")
    else:
        print("The dataset has no national vote column for this party.")


MENU = [
    ("List all constituencies", lambda c, p: list_constituencies(c)),
    ("List all MPs", lambda c, p: list_mps(c)),
    ("Party statistics (seats, votes, vote share)", list_party_statistics),
    ("Save party statistics to file", save_statistics),
    ("Charts (seats, votes, vote share)", plot_statistics),
    ("Filter constituencies", lambda c, p: filter_constituencies(c)),
    ("Compare two parties", compare_parties),
    ("Search for an MP", lambda c, p: search_mp(c)),
    ("Search for a constituency", lambda c, p: search_constituency(c)),
    ("Search for a party", search_party),
]


def main():
    try:
        constituencies, parties = load_data(DATA_FILE)
    except FileNotFoundError:
        sys.exit(f"Error: data file not found: {DATA_FILE}")
    if not constituencies:
        sys.exit("Error: no constituencies could be loaded.")
    print(f"Loaded {len(constituencies)} constituencies.")

    while True:
        print("\nUK General Election 2024 Analysis")
        for number, (label, _) in enumerate(MENU, start=1):
            print(f"{number}. {label}")
        exit_choice = len(MENU) + 1
        print(f"{exit_choice}. Exit")

        choice = get_valid_input("Enter your choice: ", 1, exit_choice)
        if choice == exit_choice:
            print("Goodbye.")
            break
        MENU[choice - 1][1](constituencies, parties)


if __name__ == "__main__":
    main()
