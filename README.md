# UK General Election 2024 Analysis

A command-line Python tool for exploring the results of the 2024 UK general election across all 650 constituencies.

## Features

- List every constituency and every elected MP, with their vote share
- Party statistics: seats won, total votes and national vote share
- Search for an MP, a constituency (full party-by-party result) or a party
- Filter constituencies by region, country or constituency type
- Compare two parties on seats and votes
- Charts: seats by party, votes by party and a vote-share pie chart
- Export party statistics to a CSV-formatted `statistics.txt`

## Requirements

- Python 3.8 or later
- matplotlib (only needed for the charts)

```
pip install -r requirements.txt
```

## Usage

```
python VotingAnalysisProject.py
```

Choose an option from the menu by number. The data file `ge2024_results.csv` must be in the same folder as the script.

## How the numbers are calculated

- **Total votes** for a party are summed across every constituency, not just the seats it won.
- **Vote share** is votes divided by valid votes, the standard way it is reported.
- Independents, the Speaker and TUV have no separate vote column in the dataset (their votes are grouped under "All other candidates"), so the tool reports their seats but not a national vote total.

## Data source

Constituency-level results for the 2024 UK general election, published by the House of Commons Library. [Add the link to the dataset page here.]

## Example

```
Party   Seats           Votes   Share
Lab       411       9,708,716   33.7%
Con       121       6,828,925   23.7%
LD         72       3,519,143   12.2%
SNP         9         724,758    2.5%
...
```
